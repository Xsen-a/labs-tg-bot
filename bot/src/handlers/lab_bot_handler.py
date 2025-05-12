import base64
import re
import json

import requests
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.lab_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit
from api.src.models import Status
from bot.src.deepseek import create_answer

router = Router()


def format_value(value):
    return "-" if value is None else value


class AddLabStates(StatesGroup):
    adding_lab = State()
    waiting_for_discipline = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_files = State()
    waiting_for_link = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    waiting_for_additional_info = State()
    waiting_for_new_discipline = State()
    waiting_for_new_name = State()
    waiting_for_new_description = State()
    waiting_for_new_files = State()
    waiting_for_new_link = State()
    waiting_for_new_start_date = State()
    waiting_for_new_end_date = State()
    waiting_for_new_additional_info = State()
    waiting_for_query_text = State()


class ShowLabStates(StatesGroup):
    showing_list = State()
    showing_chosen_lab = State()


class EditLabStates(StatesGroup):
    editing_lab = State()
    editing_discipline = State()
    editing_name = State()
    editing_description = State()
    editing_files = State()
    editing_link = State()
    editing_start_date = State()
    editing_end_date = State()
    editing_additional_info = State()


async def show_lab_confirmation(message: Message, state: FSMContext, bot: Bot = bot_unit):
    try:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
    except Exception:
        pass

    state_data = await state.get_data()

    file_names = []
    if state_data.get("files"):
        for file_info in state_data["files"]:
            if isinstance(file_info, dict):
                file_names.append(file_info.get('file_name', 'Без названия'))
            else:
                file_names.append("Файл")

    confirmation_text = _(
        "Вы действительно хотите добавить задание {name} для дисциплины {discipline}?\n\n"
        "Название: {name}\n"
        "Текст задания: {description}\n"
        "Файлы: {files}\n"
        "Ссылка: {link}\n"
        "Дата начала: {start_date}\n"
        "Срок сдачи: {end_date}\n"
        "Доп. информация: {additional_info}"
    ).format(
        name=format_value(state_data.get("lab_name")),
        discipline=format_value(state_data.get("discipline_name")),
        description=format_value(state_data.get("description")),
        files=", ".join(file_names) if file_names else "-",
        link=format_value(state_data.get("link")),
        start_date=format_value(datetime.strptime(state_data.get("start_date"), "%Y-%m-%d").strftime("%d.%m.%Y")),
        end_date=format_value(datetime.strptime(state_data.get("end_date"), "%Y-%m-%d").strftime("%d.%m.%Y")),
        additional_info=format_value(state_data.get("additional_info"))
    )

    await message.answer(
        confirmation_text,
        reply_markup=kb.add_lab_confirm()
    )

    if state_data.get("files"):
        for file_info in state_data["files"]:
            try:
                file_id = file_info['file_id']
                if file_info['file_type'] == 'document':
                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=file_id
                    )
                elif file_info['file_type'] == 'photo':
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=file_id
                    )
                elif file_info['file_type'] == 'video':
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=file_id,
                        supports_streaming=True
                    )
                elif file_info['file_type'] == 'audio':
                    await bot.send_audio(
                        chat_id=message.chat.id,
                        audio=file_id,
                    )
            except Exception as e:
                await message.answer(
                    _("Не удалось отправить файл.").format(error=str(e))
                )


@router.message(F.text == __("Добавить задание"))
async def add_lab_start(message: Message, state: FSMContext):
    await state.set_state(AddLabStates.adding_lab)
    state_data = await state.get_data()

    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)

        url_req = f"{settings.API_URL}/get_disciplines"
        response = requests.get(url_req, json={"user_id": user_id})

        if response.status_code == 200:
            disciplines = response.json().get("disciplines", [])
            if len(disciplines) == 0:
                await message.answer(
                    _("Дисциплин не найдено. Пожалуйста, добавьте дисциплины в меню дисциплин."))
                return
            sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
            disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
            await state.update_data(disciplines_dict=disciplines_dict)
            await state.update_data(disciplines=list(disciplines_dict.values()))
            await state.update_data(disciplines_id=list(disciplines_dict.keys()))

            await message.answer(
                _("Выберите дисциплину для задания."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_discipline)
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lab_disciplines_page_"),
                       or_f(AddLabStates.waiting_for_discipline, AddLabStates.waiting_for_new_discipline,
                            ShowLabStates.showing_list, EditLabStates.editing_discipline))
async def handle_disciplines_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    disciplines = state_data.get("disciplines", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.disciplines_list(disciplines, page=page)
    )


@router.callback_query(F.data.startswith("lab_discipline_index_"),
                       or_f(AddLabStates.waiting_for_discipline, AddLabStates.waiting_for_new_discipline,
                            ShowLabStates.showing_list, EditLabStates.editing_discipline))
async def select_discipline(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    discipline_index = int(callback_query.data.split("_")[-1])

    discipline_id = state_data.get("disciplines_id")[discipline_index]
    discipline_name = state_data.get("disciplines")[discipline_index]

    await state.update_data(discipline_id=discipline_id)
    await state.update_data(discipline_name=discipline_name)

    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )

    if await state.get_state() == AddLabStates.waiting_for_discipline:
        await callback_query.message.answer(_("Введите название задания."),
                                            reply_markup=None)
        await state.set_state(AddLabStates.waiting_for_name)
    elif await state.get_state() == AddLabStates.waiting_for_new_discipline:
        await show_lab_confirmation(callback_query.message, state)
    elif await state.get_state() == ShowLabStates.showing_list:
        labs_data = state_data.get("labs_response")
        disciplines_dict = state_data.get("disciplines_dict")
        await state.update_data(show_abb=False)
        filtered_lab_list = []
        for lab in labs_data["labs"]:
            if lab["discipline_id"] == discipline_id:
                filtered_lab_list.append(lab)
        filtered_lab_list.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
        await state.update_data(labs=filtered_lab_list)

        if filtered_lab_list:
            info_string = f"Задания по дисциплине {disciplines_dict[discipline_id]}\n\n"
            for lab in filtered_lab_list:
                info_string += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
                                  __(f'{lab["name"]}\n') +
                                  __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                  __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                  __(f'Статус: <b>{lab["status"]}</b>\n\n'))
        else:
            info_string = f"Заданий по дисциплине {disciplines_dict[discipline_id]} не найдено.\n\n"
        await callback_query.message.answer(
            info_string,
            reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, False, page=0))
    elif await state.get_state() == EditLabStates.editing_discipline:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "discipline_id",
                                                "editing_value": str(discipline_id)})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Дисциплина успешно изменена на {discipline_name}.").format(discipline_name=discipline_name))
            chosen_lab["discipline_id"] = discipline_id
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(callback_query.message, state, True)


@router.message(or_f(AddLabStates.waiting_for_name, AddLabStates.waiting_for_new_name, EditLabStates.editing_name))
async def get_lab_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(lab_name=name)
    state_data = await state.get_data()
    if await state.get_state() == AddLabStates.waiting_for_name:
        await message.answer(
            _("Введите текст задания."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_description)
    elif await state.get_state() == AddLabStates.waiting_for_new_name:
        await show_lab_confirmation(message, state)
    elif await state.get_state() == EditLabStates.editing_name:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "name",
                                                "editing_value": name})
        if response.status_code == 200:
            await message.answer(
                _("Название успешно изменено на {name}.").format(name=name))
            chosen_lab["name"] = name
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(message, state, True)


@router.message(or_f(AddLabStates.waiting_for_description, AddLabStates.waiting_for_new_description,
                     EditLabStates.editing_description))
async def get_lab_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    state_data = await state.get_data()
    if await state.get_state() == AddLabStates.waiting_for_description:
        await message.answer(
            _("Прикрепите файл с заданием размером до 50 МБ."),
            reply_markup=kb.finish_files_button()
        )
        await state.set_state(AddLabStates.waiting_for_files)
    elif await state.get_state() == AddLabStates.waiting_for_new_description:
        await show_lab_confirmation(message, state)
    elif await state.get_state() == EditLabStates.editing_description:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "task_text",
                                                "editing_value": description})
        if response.status_code == 200:
            await message.answer(
                _("Текст задания изменен."))
            chosen_lab["task_text"] = description
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(message, state, True)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_description)
async def skip_description(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(description=None)
    await callback_query.message.edit_text(
        _("Прикрепите файл с заданием размером до 50 МБ."),
        reply_markup=kb.finish_files_button()
    )
    await state.set_state(AddLabStates.waiting_for_files)


@router.message(or_f(AddLabStates.waiting_for_files, AddLabStates.waiting_for_new_files, EditLabStates.editing_files),
                F.document | F.photo | F.audio | F.video)
async def get_lab_file(message: Message, state: FSMContext, bot: Bot = bot_unit):
    try:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
    except Exception:
        pass

    state_data = await state.get_data()
    if (
            await state.get_state() == AddLabStates.waiting_for_new_files or await state.get_state() == EditLabStates.editing_files) and \
            (state_data.get("is_editing_files") is False or state_data.get("is_editing_files") is None):
        await state.update_data(is_editing_files=True)
        await state.update_data(files=[])

    max_file_size = 50 * 1024 * 1024
    file_info = None

    if message.document:
        document = message.document

        if document.file_size > max_file_size:
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ."))
            return

        file_type = 'document'
        file = await bot.get_file(document.file_id)
        file_data = await bot.download_file(file.file_path)
        file_bytes = file_data.read()

        file_info = {
            'file_id': document.file_id,
            'file_name': document.file_name or "Без названия",
            'file_data': file_bytes,
            'file_type': file_type,
            'mime_type': document.mime_type
        }

        state_data = await state.get_data()
        files = state_data.get("files", [])
        files.append(file_info)
        await state.update_data(files=files)

    elif message.photo:
        photo = message.photo[-1]

        if photo.file_size > max_file_size:
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ."))
            return

        file = await bot.get_file(photo.file_id)
        file_data = await bot.download_file(file.file_path)
        file_bytes = file_data.read()

        file_info = {
            'file_id': photo.file_id,
            'file_name': f"photo_{message.message_id}.jpg" or "Без названия",
            'file_data': file_bytes,
            'file_type': 'photo',
            'mime_type': 'image/jpeg'
        }

        state_data = await state.get_data()
        files = state_data.get("files", [])
        files.append(file_info)
        await state.update_data(files=files)

    elif message.audio:
        audio = message.audio

        if audio.file_size > max_file_size:
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ."))
            return

        file = await bot.get_file(audio.file_id)
        file_data = await bot.download_file(file.file_path)
        file_bytes = file_data.read()

        file_info = {
            'file_id': audio.file_id,
            'file_name': audio.file_name or f"audio_{audio.file_id}.mp3",
            'file_data': file_bytes,
            'file_type': 'audio',
            'mime_type': audio.mime_type or 'audio/mpeg'
        }

        state_data = await state.get_data()
        files = state_data.get("files", [])
        files.append(file_info)
        await state.update_data(files=files)

    elif message.video:
        video = message.video
        if video.file_size > max_file_size:
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ."))
            return
        file = await bot.get_file(video.file_id)
        file_data = await bot.download_file(file.file_path)
        file_bytes = file_data.read()

        file_info = {
            'file_id': video.file_id,
            'file_name': video.file_name or f"video_{message.message_id}.mp4",
            'file_data': file_bytes,
            'file_type': 'video',
            'mime_type': video.mime_type or 'video/mp4'
        }

        state_data = await state.get_data()
        files = state_data.get("files", [])
        files.append(file_info)
        await state.update_data(files=files)

    if file_info:
        try:
            await message.answer(
                _("Файл '{file_name}' успешно загружен. Прикрепите еще один файл или нажмите 'Завершить добавление файлов'").format(
                    file_name=file_info['file_name']
                ),
                reply_markup=kb.finish_files_button()
            )
        except Exception as e:
            await message.answer(_("Произошла ошибка при загрузке файла: {error}").format(error=str(e)))


@router.callback_query(F.data == "finish_files",
                       or_f(AddLabStates.waiting_for_files, AddLabStates.waiting_for_new_files,
                            EditLabStates.editing_files))
async def finish_files(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_editing_files=False)
    state_data = await state.get_data()
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    if await state.get_state() == AddLabStates.waiting_for_files:
        await callback_query.message.edit_text(
            _("Вставьте ссылку на задание."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_link)
    elif await state.get_state() == AddLabStates.waiting_for_new_files:
        await show_lab_confirmation(callback_query.message, state)
    elif await state.get_state() == EditLabStates.editing_files:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/delete_files"
        response = requests.delete(url_req, json={"task_id": chosen_lab["task_id"]})
        if response.status_code == 200:
            flag = True
            if state_data.get("files"):
                for file_info in state_data["files"]:
                    url_req = f"{settings.API_URL}/add_file"
                    file_data = {
                        "task_id": chosen_lab["task_id"],
                        "file_name": file_info["file_name"],
                        "file_data": base64.b64encode(file_info["file_data"]).decode('utf-8'),
                        "file_type": file_info["file_type"],
                    }
                    response = requests.post(url_req, json=file_data)
                    if response.status_code != 200:
                        flag = False
                        response_data = response.json()
                        # for file_info in response_data["files"]:
                        #     url_req = f"{settings.API_URL}/add_file"
                        #     file_data = {
                        #         "task_id": state_data.get("task_id"),
                        #         "file_name": file_info["file_name"],
                        #         "file_data": base64.b64encode(file_info["file_data"]).decode('utf-8'),
                        #         "file_type": file_info["file_type"],
                        #     }
                        #     response = requests.post(url_req, json=file_data)
            if flag:
                await callback_query.message.answer(
                    _("Файлы успешно заменены."))
                await state.set_state(ShowLabStates.showing_chosen_lab)
                await state.update_data(files=[])
                await show_chosen_lab_menu(callback_query.message, state, True)
            else:
                await callback_query.message.answer(
                    _("Ошибка добавления файлов. Повторите попытку."))


@router.message(or_f(AddLabStates.waiting_for_link, AddLabStates.waiting_for_new_link, EditLabStates.editing_link))
async def get_lab_link(message: Message, state: FSMContext):
    link = message.text
    if not re.match(r'^https?://', link):
        await message.answer(_("Пожалуйста, введите корректную ссылку (начинается с http:// или https://)."))
        return

    await state.update_data(link=link)
    state_data = await state.get_data()
    if await state.get_state() == AddLabStates.waiting_for_link:
        await message.answer(
            _("Выберите дату начала выполнения задания."),
            reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
        )
        await state.set_state(AddLabStates.waiting_for_start_date)
    elif await state.get_state() == AddLabStates.waiting_for_new_link:
        await show_lab_confirmation(message, state)
    elif await state.get_state() == EditLabStates.editing_link:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "task_link",
                                                "editing_value": link})
        if response.status_code == 200:
            await message.answer(
                _("Ссылка успешно изменена на {link}.").format(link=link))
            chosen_lab["task_link"] = link
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(message, state, True)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_link)
async def skip_link(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(link=None)
    await callback_query.message.edit_text(
        _("Выберите дату начала выполнения задания"),
        reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
    )
    await state.set_state(AddLabStates.waiting_for_start_date)


@router.callback_query(F.data.startswith("calendar_prev_"))
async def prev_month(callback: CallbackQuery):
    _, _, year, month = callback.data.split('_')
    year = int(year)
    month = int(month)

    # Переход к предыдущему месяцу
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1

    await callback.message.edit_reply_markup(
        reply_markup=kb.calendar(year, month)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("calendar_next_"))
async def next_month(callback: CallbackQuery):
    _, _, year, month = callback.data.split('_')
    year = int(year)
    month = int(month)

    # Переход к следующему месяцу
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    await callback.message.edit_reply_markup(
        reply_markup=kb.calendar(year, month)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ignore"))
async def ignore_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.answer()


@router.callback_query(F.data.startswith("calendar_date_"),
                       or_f(AddLabStates.waiting_for_start_date, AddLabStates.waiting_for_new_start_date,
                            EditLabStates.editing_start_date))
async def select_start_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split("_")[-1]
    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    state_data = await state.get_data()
    end_date_str = state_data.get("end_date")
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if end_date < start_date:
            if await state.get_state() == AddLabStates.waiting_for_start_date:
                await callback.message.edit_text(
                    _("Выберите дату начала выполнения задания.\n\n"
                      "Дата начала не может быть позже даты сдачи. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return
            else:
                await callback.message.edit_text(
                    _("Выберите новую дату начала выполнения задания.\n\n"
                      "Дата начала не может быть позже даты сдачи. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return

    # Сохраняем как строку в формате DD.MM.YYYY
    await state.update_data(start_date=start_date.strftime("%Y-%m-%d"))

    if await state.get_state() == AddLabStates.waiting_for_start_date:
        await callback.message.edit_text(
            _("Выберите дату сдачи задания."),
            reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
        )
        await state.set_state(AddLabStates.waiting_for_end_date)
    elif await state.get_state() == AddLabStates.waiting_for_new_start_date:
        await show_lab_confirmation(callback.message, state)
    elif await state.get_state() == EditLabStates.editing_start_date:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "start_date",
                                                "editing_value": start_date.strftime("%Y-%m-%d")})
        if response.status_code == 200:
            await callback.message.answer(
                _("Дата начала успешно изменена на {start_date}.").format(start_date=start_date))
            chosen_lab["start_date"] = start_date.strftime("%Y-%m-%d")
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(callback.message, state, True)


@router.callback_query(F.data.startswith("calendar_date_"),
                       or_f(AddLabStates.waiting_for_end_date, AddLabStates.waiting_for_new_end_date,
                            EditLabStates.editing_end_date))
async def select_end_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split("_")[-1]
    end_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    state_data = await state.get_data()
    start_date_str = state_data.get("start_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        if end_date < start_date:
            if await state.get_state() == AddLabStates.waiting_for_end_date:
                await callback.message.edit_text(
                    _("Выберите дату сдачи задания.\n\n"
                      "Дата сдачи не может быть раньше даты начала. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return
            else:
                await callback.message.edit_text(
                    _("Выберите новую дату сдачи задания.\n\n"
                      "Дата сдачи не может быть раньше даты начала. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return

    # Сохраняем дату сдачи
    await state.update_data(end_date=end_date.strftime("%Y-%m-%d"))

    if await state.get_state() == AddLabStates.waiting_for_end_date:
        await callback.message.edit_text(
            _("Введите дополнительную информацию о задании."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_additional_info)
    elif await state.get_state() == AddLabStates.waiting_for_new_end_date:
        await show_lab_confirmation(callback.message, state)
    elif await state.get_state() == EditLabStates.editing_end_date:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "end_date",
                                                "editing_value": end_date.strftime("%Y-%m-%d")})
        if response.status_code == 200:
            await callback.message.answer(
                _(f"Дата сдачи успешно изменена на {end_date}").format(end_date=end_date))
            chosen_lab["end_date"] = end_date.strftime("%Y-%m-%d")
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(callback.message, state, True)


@router.message(or_f(AddLabStates.waiting_for_additional_info, AddLabStates.waiting_for_new_additional_info,
                     EditLabStates.editing_additional_info))
async def get_additional_info(message: Message, state: FSMContext):
    additional_info = message.text
    state_data = await state.get_data()
    if await state.get_state() != EditLabStates.editing_additional_info:
        await state.update_data(additional_info=additional_info)
        await show_lab_confirmation(message, state, bot_unit)
    else:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "extra_info",
                                                "editing_value": additional_info})
        if response.status_code == 200:
            await message.answer(
                _("Дополнительная информация успешно изменена."))
            chosen_lab["extra-info"] = additional_info
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(message, state, True)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_additional_info)
async def skip_additional_info(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(additional_info=None)
    await show_lab_confirmation(callback_query.message, state, bot_unit)


@router.callback_query(F.data == "add_lab")
async def confirm_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()

    if state_data.get("files"):
        await callback_query.message.answer("Сохранение файлов...")

    lab_data = {
        "user_id": state_data.get("user_id"),
        "discipline_id": state_data.get("discipline_id"),
        "name": state_data.get("lab_name"),
        "task_text": state_data.get("description"),
        "task_link": state_data.get("link"),
        "start_date": state_data.get("start_date"),
        "end_date": state_data.get("end_date"),
        "extra_info": state_data.get("additional_info"),
        "status": "not_started"
    }
    url_req = f"{settings.API_URL}/add_lab"
    response = requests.post(url_req, json=lab_data)

    if response.status_code == 200:
        await state.update_data(task_id=str(response.json()["task_id"]))
        state_data = await state.get_data()
        flag = True
        if state_data.get("files"):
            for file_info in state_data["files"]:
                url_req = f"{settings.API_URL}/add_file"
                file_data = {
                    "task_id": state_data.get("task_id"),
                    "file_name": file_info["file_name"],
                    "file_data": base64.b64encode(file_info["file_data"]).decode('utf-8'),
                    "file_type": file_info["file_type"],
                }
                response = requests.post(url_req, json=file_data)
                if response.status_code != 200:
                    flag = False
        if flag:
            await callback_query.message.answer(
                _("Задание {name} со статусом 'Не начато' для дисциплины {discipline} успешно добавлено. Если необходимо, измените статус в меню заданий.").format(
                    name=state_data.get("lab_name"),
                    discipline=state_data.get("discipline_name")
                )
            )
            await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))
        else:
            await callback_query.message.answer(
                _("Задание {name} со статусом 'Не начато' для дисциплины {discipline} успешно добавлено. Если необходимо, измените статус в меню заданий. Ошибка добавления файлов. Добавьте файлы в меню заданий.").format(
                    name=state_data.get("lab_name"),
                    discipline=state_data.get("discipline_name")
                )
            )
            await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_add_lab")
async def confirm_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    await callback_query.message.answer("Вы отменили добавление задания.")
    state_data = await state.get_data()
    await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))


@router.callback_query(F.data.startswith("change_lab_"))
async def edit_lab_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    field = callback_query.data.split("_")[2:]
    if len(field) > 1:
        field = "_".join(field)
    else:
        field = "".join(field)
    await state.update_data(editing_attribute=field)

    match field:
        case "discipline":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите новую дисциплину для задания."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_new_discipline)
        case "name":
            await callback_query.message.answer(_("Введите новое название задания."))
            await state.set_state(AddLabStates.waiting_for_new_name)
        case "description":
            await callback_query.message.answer(_("Введите новый текст задания."))
            await state.set_state(AddLabStates.waiting_for_new_description)
        case "files":
            await callback_query.message.answer(
                _("Прикрепите заново файл(ы) с заданием размером до 50 МБ."),
                reply_markup=kb.finish_files_button())
            await state.set_state(AddLabStates.waiting_for_new_files)
        case "link":
            await callback_query.message.answer(
                _("Выберите новую ссылку на задание."))
            await state.set_state(AddLabStates.waiting_for_new_link)
        case "start_date":
            await callback_query.message.answer(
                _("Выберите новую дату начала выполнения задания."),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(AddLabStates.waiting_for_new_start_date)
        case "end_date":
            await callback_query.message.answer(
                _("Выберите новую дату сдачи задания."),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(AddLabStates.waiting_for_new_end_date)
        case "additional_info":
            await callback_query.message.answer(
                _("Введите новую дополнительную информацию о задании."))
            await state.set_state(AddLabStates.waiting_for_new_additional_info)

    await callback_query.answer()


@router.message(F.text == __("Посмотреть список заданий"))
async def show_lab_list(message: Message, state: FSMContext):
    await state.set_state(ShowLabStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)
        url_req = f"{settings.API_URL}/get_labs"
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            await state.update_data(labs_response=response_data)

            url_req = f"{settings.API_URL}/get_disciplines"
            response = requests.get(url_req, json={"user_id": user_id})

            if response.status_code == 200:
                disciplines = response.json().get("disciplines", [])
                sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
                disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
                await state.update_data(disciplines_dict=disciplines_dict)
                await state.update_data(disciplines=list(disciplines_dict.values()))
                await state.update_data(disciplines_id=list(disciplines_dict.keys()))
                await message.answer(
                    _("Выберите вид отображения списка."),
                    reply_markup=kb.list_show_option()
                )
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lab_list_"))
async def show_lab_list_option(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    field = callback_query.data.split("_")[-1]

    match field:
        case "status":
            await callback_query.message.answer(
                _("Выберите статус."),
                reply_markup=kb.status_option())
        case "discipline":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите дисциплину."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
        case "week":
            state_data = await state.get_data()
            labs_data = state_data.get("labs_response")
            disciplines_dict = state_data.get("disciplines_dict")
            await state.update_data(show_abb=True)
            filtered_lab_list_undone = []
            filtered_lab_list_process = []

            today = datetime.now().date()
            date_mark = today + timedelta(days=7)

            for lab in labs_data["labs"]:
                if datetime.strptime(lab["end_date"], "%Y-%m-%d").date() < date_mark:
                    if lab["status"] != 'Сдано' and datetime.strptime(lab["end_date"], "%Y-%m-%d").date() < today:
                        filtered_lab_list_undone.append(lab)
                    else:
                        filtered_lab_list_process.append(lab)
            filtered_lab_list_undone.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
            filtered_lab_list_process.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
            filtered_lab_list = filtered_lab_list_undone + filtered_lab_list_process
            await state.update_data(labs=filtered_lab_list)

            if filtered_lab_list_undone or filtered_lab_list_process:
                if filtered_lab_list_undone:
                    info_string_undone = __(f"<b>Просроченные задания:</b>\n\n")
                    for lab in filtered_lab_list_undone:
                        info_string_undone += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
                                                 __(f'{lab["name"]}\n') +
                                                 __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                                 __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                                 __(f'Статус: <b>{lab["status"]}</b>\n\n'))
                else:
                    info_string_undone = __(f"<b>Просроченных заданий не найдено.</b>\n\n")
                if filtered_lab_list_process:
                    info_string_process = __(f"<b>Предстоящие задания на следующие 7 дней:</b>\n\n")
                    for lab in filtered_lab_list_process:
                        info_string_process += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
                                                  __(f'{lab["name"]}\n') +
                                                  __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                                  __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                                  __(f'Статус: <b>{lab["status"]}</b>\n\n'))
                else:
                    info_string_process = __(f"<b>Заданий на ближайшие 7 дней не найдено.</b>\n\n")
                info_string = info_string_undone + info_string_process
            else:
                info_string = __(f"Заданий не найдено.\n\n")
            await callback_query.message.answer(
                info_string,
                reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, True, page=0),
                parse_mode="HTML")


@router.callback_query(F.data == "back_to_options")
async def back_to_options(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.message.answer(
        _("Выберите вид отображения списка."),
        reply_markup=kb.list_show_option()
    )


@router.callback_query(F.data.startswith("lab_status_"),
                       or_f(ShowLabStates.showing_list, ShowLabStates.showing_chosen_lab))
async def show_lab_list_status(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    state_data = await state.get_data()

    status_name = callback_query.data.replace("lab_status_", "")
    selected_status = Status[status_name]

    if await state.get_state() == ShowLabStates.showing_list:
        labs_data = state_data.get("labs_response")
        disciplines_dict = state_data.get("disciplines_dict")
        await state.update_data(show_abb=True)
        filtered_lab_list = []
        for lab in labs_data["labs"]:
            if lab["status"] == selected_status.value:
                filtered_lab_list.append(lab)
        filtered_lab_list.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
        await state.update_data(labs=filtered_lab_list)

        if filtered_lab_list:
            info_string = f"Задания со статусом: {selected_status.value}\n\n"
            for lab in filtered_lab_list:
                info_string += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
                                  __(f'{lab["name"]}\n') +
                                  __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
                                  __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n\n'))
        else:
            info_string = f"Заданий со статусом {selected_status.value} не найдено.\n\n"
        await callback_query.message.answer(
            info_string,
            reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, True, page=0))
    elif await state.get_state() == ShowLabStates.showing_chosen_lab:
        chosen_lab = state_data.get("chosen_lab")
        url_req = f"{settings.API_URL}/edit_lab"
        response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
                                                "editing_attribute": "status",
                                                "editing_value": status_name})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Статус успешно изменен на {new_status}.").format(new_status=selected_status.value))
            chosen_lab["status"] = selected_status.value
            await state.update_data(chosen_lab=chosen_lab)
            await state.set_state(ShowLabStates.showing_chosen_lab)
            await show_chosen_lab_menu(callback_query.message, state, True)


async def show_chosen_lab_menu(message: Message, state: FSMContext, after_edit, bot: Bot = bot_unit):
    state_data = await state.get_data()
    disciplines_dict = state_data.get("disciplines_dict")
    chosen_lab = state_data.get("chosen_lab")

    url_req = f"{settings.API_URL}/get_lab_files"
    response = requests.get(url_req, json={"task_id": chosen_lab["task_id"]})
    if response.status_code == 200:
        response_data = response.json()
        file_names = [file['file_name'] for file in response_data.get("files", [])]
        confirmation_text = _(
            "Вы в меню задания:\n\n"
            "Дисциплина: {discipline}\n"
            "Название: {name}\n"
            "Текст задания: {description}\n"
            "Файлы: {files}\n"
            "Ссылка: {link}\n"
            "Дата начала: {start_date}\n"
            "Срок сдачи: {end_date}\n"
            "Доп. информация: {additional_info}\n"
            "Статус: <b>{status}</b>"
        ).format(
            name=format_value(chosen_lab["name"]),
            discipline=format_value(disciplines_dict[chosen_lab["discipline_id"]]),
            description=format_value(chosen_lab["task_text"]),
            files=", ".join(file_names) if file_names else "-",
            link=format_value(chosen_lab["task_link"]),
            start_date=format_value(datetime.strptime(chosen_lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
            end_date=format_value(datetime.strptime(chosen_lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
            additional_info=format_value(chosen_lab["extra_info"]),
            status=chosen_lab["status"]
        )

        try:
            if not after_edit:
                await message.edit_text(
                    confirmation_text,
                    reply_markup=kb.lab_menu(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    confirmation_text,
                    reply_markup=kb.lab_menu(),
                    parse_mode="HTML"
                )
        except:
            await message.answer(
                confirmation_text,
                reply_markup=kb.lab_menu(),
                parse_mode="HTML"
            )

        for file_info in response_data["files"]:
            try:
                file_bytes = base64.b64decode(file_info['file_data'])
                file_data = BufferedInputFile(file_bytes, filename=file_info["file_name"])
                if file_info['file_type'] == 'document':
                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=file_data
                    )
                elif file_info['file_type'] == 'photo':
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=file_data
                    )
                elif file_info['file_type'] == 'video':
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=file_data,
                        supports_streaming=True
                    )
                elif file_info['file_type'] == 'audio':
                    await bot.send_audio(
                        chat_id=message.chat.id,
                        audio=file_data,
                    )
            except Exception as e:
                await message.answer(
                    _("Не удалось отправить файл").format(error=str(e))
                )


@router.callback_query(F.data.startswith("lab_page_"), ShowLabStates.showing_list)
async def handle_lab_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    show_abb = state_data.get("show_abb")
    labs = state_data.get("labs", [])
    disciplines_dict = state_data.get("disciplines_dict")

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.labs_list(labs, disciplines_dict, show_abb, page=page)
    )


@router.callback_query(F.data.startswith("lab_index_"))
async def show_chosen_lab_info(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
    await state.set_state(ShowLabStates.showing_chosen_lab)
    await callback_query.answer()
    state_data = await state.get_data()

    lab_index = int(callback_query.data.split("_")[-1])
    labs = state_data.get("labs")
    chosen_lab = next((lab for lab in labs if lab["task_id"] == lab_index), None)
    await state.update_data(chosen_lab=chosen_lab)

    await show_chosen_lab_menu(callback_query.message, state, False)


@router.callback_query(F.data == "edit_status")
async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    await callback_query.message.answer(
        _("Выберите статус для изменения."),
        reply_markup=kb.status_option()
    )


@router.callback_query(F.data == "edit_lab")
async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.answer(
        _("Выберите информацию для изменения."),
        reply_markup=kb.lab_edit_menu()
    )


@router.callback_query(F.data.startswith("edit_lab_"))
async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()

    field = callback_query.data.split("_")[2:]
    if len(field) > 1:
        field = "_".join(field)
    else:
        field = "".join(field)
    await state.update_data(editing_attribute=field)

    match field:
        case "discipline":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите новую дисциплину для задания."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(EditLabStates.editing_discipline)
        case "name":
            await callback_query.message.answer(_("Введите новое название задания."))
            await state.set_state(EditLabStates.editing_name)
        case "description":
            await callback_query.message.answer(_("Введите новый текст задания."))
            await state.set_state(EditLabStates.editing_description)
        case "files":
            await callback_query.message.answer(
                _("Прикрепите заново файл(ы) с заданием размером до 50 МБ."),
                reply_markup=kb.finish_files_button())
            await state.set_state(EditLabStates.editing_files)
        case "link":
            await callback_query.message.answer(
                _("Введите новую ссылку на задание."))
            await state.set_state(EditLabStates.editing_link)
        case "start_date":
            await callback_query.message.answer(
                _("Выберите новую дату начала выполнения задания."),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(EditLabStates.editing_start_date)
        case "end_date":
            await callback_query.message.answer(
                _("Выберите новую дату сдачи задания."),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(EditLabStates.editing_end_date)
        case "additional_info":
            await callback_query.message.answer(
                _("Введите новую дополнительную информацию о задании."))
            await state.set_state(EditLabStates.editing_additional_info)

    await callback_query.answer()


@router.callback_query(F.data == "delete_lab")
async def ask_deleting_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lab = state_data.get("chosen_lab")
    await callback_query.message.answer(
        _("Вы действительно хотите удалить задание {name}?")
        .format(name=chosen_lab["name"]),
        reply_markup=kb.confirm_delete_lab()
    )


@router.callback_query(F.data == "confirm_deleting_lab")
async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lab = state_data.get("chosen_lab")
    url_req = f"{settings.API_URL}/delete_lab"
    response = requests.delete(url_req, json={"task_id": chosen_lab["task_id"]})
    if response.status_code == 200:
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        await callback_query.message.answer(
            _("Задание {name} успешно удалено.")
            .format(name=chosen_lab["name"])
        )
        await show_lab_list(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_deleting_lab")
async def cancel_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lab = state_data.get("chosen_lab")
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.message.answer(
        _("Вы отменили удаление задания {name}.")
        .format(name=chosen_lab["name"])
    )
    await show_chosen_lab_menu(callback_query.message, state, False)


@router.callback_query(F.data == "back_to_lab_menu")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await show_lab_list(callback_query.message, state)


@router.callback_query(F.data == "back_to_chosen_lab_menu")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id - 1,
    )
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await show_chosen_lab_menu(callback_query.message, state, False)


@router.callback_query(F.data == "use_ai")
async def use_ai(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lab = state_data.get("chosen_lab")
    if chosen_lab["task_text"]:
        await callback_query.message.answer(
            __("Использовать текущий текст задания для запроса или ввести новый?\n\nТекущий текст задания:\n{text}")
            .format(text=chosen_lab["task_text"]),
            reply_markup=kb.use_text_in_ai()
        )
    else:
        await callback_query.message.answer(
            _("Введите текст задания для запроса.")
        )
        await state.set_state(AddLabStates.waiting_for_query_text)


def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!\\'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


@router.callback_query(F.data == "use_current_text")
async def use_ai(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lab = state_data.get("chosen_lab")
    await callback_query.message.answer(
        _("Обработка запроса... Это может занять некоторое время.")
    )
    response = await create_answer(chosen_lab["task_text"])
    if response:
        escaped_response = escape_markdown(response)
        await callback_query.message.answer(
            escaped_response,
            parse_mode="MarkdownV2"
        )
    else:
        await callback_query.message.answer(
            _("Ошибка выполнения запроса :(")
        )


@router.callback_query(F.data == "use_new_text")
async def use_ai(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        _("Введите текст задания для запроса.")
    )
    await state.set_state(AddLabStates.waiting_for_query_text)


@router.message(AddLabStates.waiting_for_query_text)
async def get_task_text(message: Message, state: FSMContext):
    text = message.text
    await message.answer(
        _("Обработка запроса... Это может занять некоторое время.")
    )
    response = await create_answer(text)
    if response:
        escaped_response = escape_markdown(response)
        await message.answer(
            escaped_response,
            parse_mode="MarkdownV2"
        )
    else:
        await message.answer(
            _("Ошибка выполнения запроса :(")
        )
