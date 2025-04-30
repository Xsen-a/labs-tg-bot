import base64
import re
import json
from io import BytesIO

import requests
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, Document, BufferedInputFile

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.lab_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit
from api.src.models import Status

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


class ShowLabStates(StatesGroup):
    showing_list = State()
    waiting_for_lab = State()


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
        "Вы действительно хотите добавить лабораторную работу {name} для дисциплины {discipline}?\n\n"
        "Название: {name}\n"
        "Описание: {description}\n"
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
                # file_data = BufferedInputFile(
                #     file=file_info['file_data'],
                #     filename=file_info['file_name']
                # )
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
                print(str(e))
                await message.answer(
                    _("Не удалось отправить файл").format(error=str(e))
                )


@router.message(F.text == __("Добавить лабораторную работу"))
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
            sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
            disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
            await state.update_data(disciplines_dict=disciplines_dict)
            await state.update_data(disciplines=list(disciplines_dict.values()))
            await state.update_data(disciplines_id=list(disciplines_dict.keys()))

            await message.answer(
                _("Выберите дисциплину для лабораторной работы"),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_discipline)
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lab_disciplines_page_"), AddLabStates.waiting_for_discipline)
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
                       or_f(AddLabStates.waiting_for_discipline, AddLabStates.waiting_for_new_discipline))
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
        await callback_query.message.answer(_("Введите название лабораторной работы."),
                                            reply_markup=None)
        await state.set_state(AddLabStates.waiting_for_name)
    else:
        await show_lab_confirmation(callback_query.message, state)


@router.message(or_f(AddLabStates.waiting_for_name, AddLabStates.waiting_for_new_name))
async def get_lab_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(lab_name=name)
    if await state.get_state() == AddLabStates.waiting_for_name:
        await message.answer(
            _("Введите текст лабораторной работы"),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_description)
    else:
        await show_lab_confirmation(message, state)


@router.message(or_f(AddLabStates.waiting_for_description, AddLabStates.waiting_for_new_description))
async def get_lab_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    if await state.get_state() == AddLabStates.waiting_for_description:
        await message.answer(
            _("Прикрепите файл с заданием для лабораторной работы размером до 50 МБ"),
            reply_markup=kb.finish_files_button()
        )
        await state.set_state(AddLabStates.waiting_for_files)
    else:
        await show_lab_confirmation(message, state)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_description)
async def skip_description(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(description=None)
    await callback_query.message.edit_text(
        _("Прикрепите файл с заданием для лабораторной работы размером до 50 МБ."),
        reply_markup=kb.finish_files_button()
    )
    await state.set_state(AddLabStates.waiting_for_files)


@router.message(or_f(AddLabStates.waiting_for_files, AddLabStates.waiting_for_new_files),
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
    if await state.get_state() == AddLabStates.waiting_for_new_files and \
            (state_data.get("is_editing_files") is False or state_data.get("is_editing_files") is None):
        await state.update_data(is_editing_files=True)
        await state.update_data(files=[])

    max_file_size = 50 * 1024 * 1024
    file_info = None

    if message.document:
        document = message.document

        if document.file_size > max_file_size:
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ"))
            return

        # if document.mime_type.startswith('image/'):
        #     file_type = 'photo'
        # elif document.mime_type.startswith('video/'):
        #     file_type = 'video'
        # elif document.mime_type.startswith('audio/'):
        #     file_type = 'audio'
        # else:
        #     file_type = 'document'

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
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ"))
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
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ"))
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
            await message.answer(_("Файл слишком большой. Максимальный размер - 50 МБ"))
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
                       or_f(AddLabStates.waiting_for_files, AddLabStates.waiting_for_new_files))
async def finish_files(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_editing_files=False)
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    if await state.get_state() == AddLabStates.waiting_for_files:
        await callback_query.message.edit_text(
            _("Вставьте ссылку на задание лабораторной работы"),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_link)
    else:
        await show_lab_confirmation(callback_query.message, state)


@router.message(or_f(AddLabStates.waiting_for_link, AddLabStates.waiting_for_new_link))
async def get_lab_link(message: Message, state: FSMContext):
    link = message.text
    if not re.match(r'^https?://', link):
        await message.answer(_("Пожалуйста, введите корректную ссылку (начинается с http:// или https://)"))
        return

    await state.update_data(link=link)
    if await state.get_state() == AddLabStates.waiting_for_link:
        await message.answer(
            _("Выберите дату начала выполнения лабораторной работы"),
            reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
        )
        await state.set_state(AddLabStates.waiting_for_start_date)
    else:
        await show_lab_confirmation(message, state)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_link)
async def skip_link(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(link=None)
    await callback_query.message.edit_text(
        _("Выберите дату начала выполнения лабораторной работы"),
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
                       or_f(AddLabStates.waiting_for_start_date, AddLabStates.waiting_for_new_start_date))
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
                    _("Выберите дату начала выполнения лабораторной работы.\n\n"
                      "Дата начала не может быть позже даты сдачи. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return
            else:
                await callback.message.edit_text(
                    _("Выберите новую дату начала выполнения лабораторной работы.\n\n"
                      "Дата начала не может быть позже даты сдачи. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return

    # Сохраняем как строку в формате DD.MM.YYYY
    await state.update_data(start_date=start_date.strftime("%Y-%m-%d"))

    if await state.get_state() == AddLabStates.waiting_for_start_date:
        await callback.message.edit_text(
            _("Выберите дату сдачи лабораторной работы"),
            reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
        )
        await state.set_state(AddLabStates.waiting_for_end_date)
    else:
        await show_lab_confirmation(callback.message, state)


@router.callback_query(F.data.startswith("calendar_date_"),
                       or_f(AddLabStates.waiting_for_end_date, AddLabStates.waiting_for_new_end_date))
async def select_end_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    # Получаем выбранную дату
    date_str = callback.data.split("_")[-1]
    end_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Получаем дату начала из состояния
    state_data = await state.get_data()
    start_date_str = state_data.get("start_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        # Сравниваем даты
        if end_date < start_date:
            if await state.get_state() == AddLabStates.waiting_for_end_date:
                await callback.message.edit_text(
                    _("Выберите дату сдачи лабораторной работы.\n\n"
                      "Дата сдачи не может быть раньше даты начала. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return
            else:
                await callback.message.edit_text(
                    _("Выберите новую дату сдачи лабораторной работы.\n\n"
                      "Дата сдачи не может быть раньше даты начала. Пожалуйста, выберите другую дату."),
                    reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
                )
                return

    # Сохраняем дату сдачи
    await state.update_data(end_date=end_date.strftime("%Y-%m-%d"))

    if await state.get_state() == AddLabStates.waiting_for_end_date:
        await callback.message.edit_text(
            _("Введите дополнительную информацию о лабораторной работе"),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddLabStates.waiting_for_additional_info)
    else:
        await show_lab_confirmation(callback.message, state)


@router.message(or_f(AddLabStates.waiting_for_additional_info, AddLabStates.waiting_for_new_additional_info))
async def get_additional_info(message: Message, state: FSMContext):
    additional_info = message.text
    print(additional_info)
    print(await state.get_state())
    await state.update_data(additional_info=additional_info)
    await show_lab_confirmation(message, state, bot_unit)


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
                _("Лабораторная работа {name} со статусом 'Не начато' для дисциплины {discipline} успешно добавлена. Если необходимо, измените статус в меню лабораторной работы.").format(
                    name=state_data.get("lab_name"),
                    discipline=state_data.get("discipline_name")
                )
            )
            await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))
        else:
            await callback_query.message.answer(
                _("Лабораторная работа {name} со статусом 'Не начато' для дисциплины {discipline} успешно добавлена. Если необходимо, измените статус в меню лабораторной работы. Ошибка добавления файлов. Добавьте файлы в меню лабораторной работы.").format(
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
    await callback_query.message.answer("Вы отменили добавление лабораторной работы.")
    state_data = await state.get_data()
    await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))


@router.callback_query(F.data.startswith("change_lab_"))
async def edit_lab_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    field = callback_query.data.split("_")[2:]
    if len(field) > 1:
        field = "_".join(field)
    await state.update_data(editing_attribute=field)

    match field:
        case "discipline":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите новую дисциплину для лабораторной работы"),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_new_discipline)
        case "name":
            await callback_query.message.answer(_("Введите новое название лабораторной работы."))
            await state.set_state(AddLabStates.waiting_for_new_name)
        case "description":
            await callback_query.message.answer(_("Введите новый текст лабораторной работы."))
            await state.set_state(AddLabStates.waiting_for_new_description)
        case "files":
            await callback_query.message.answer(
                _("Прикрепите заново файл с заданием для лабораторной работы размером до 50 МБ."),
                reply_markup=kb.finish_files_button())
            await state.set_state(AddLabStates.waiting_for_new_files)
        case "link":
            await callback_query.message.answer(
                _("Выберите новую ссылку на задание для лабораторной работы"))
            await state.set_state(AddLabStates.waiting_for_new_link)
        case "start_date":
            await callback_query.message.answer(
                _("Выберите новую дату начала выполнения лабораторной работы"),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(AddLabStates.waiting_for_new_start_date)
        case "end_date":
            await callback_query.message.answer(
                _("Выберите новую дату сдачи лабораторной работы"),
                reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
            await state.set_state(AddLabStates.waiting_for_new_end_date)
        case "additional_info":
            print(await state.get_state())
            await callback_query.message.answer(
                _("Введите новую дополнительную информацию о лабораторной работе."))
            await state.set_state(AddLabStates.waiting_for_new_additional_info)
            print(await state.get_state())

    await callback_query.answer()


@router.message(F.text == __("Посмотреть список лабораторных работ"))
async def show_lab_list(message: Message, state: FSMContext):
    await state.set_state(ShowLabStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)
        url_req = f"{settings.API_URL}/get_labs"
        print(user_id)
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            print(response_data)
            sorted_labs = sorted(response_data.get("labs"), key=lambda x: x["name"])
            labs_dict = {lab["task_id"]: lab["name"] for lab in sorted_labs}
            await state.update_data(labs_dict=labs_dict)
            await state.update_data(labs=list(labs_dict.values()))
            await state.update_data(labs_id=list(labs_dict.keys()))
            await state.update_data(labs_response=response_data)
            await message.answer(
                _("Выберите вид отображения списка:"),
                reply_markup=kb.list_show_option()
            )
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lab_list_"))
async def show_lab_list_option(callback_query: CallbackQuery, state: FSMContext):
    print(callback_query.data)
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    field = callback_query.data.split("_")[-1]
    print("field", field)

    match field:
        case "status":
            await callback_query.message.answer(
                _("Выберите статус:"),
                reply_markup=kb.status_option())
        case "discipline":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите новую дисциплину для лабораторной работы"),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_new_discipline)
        case "week":
            state_data = await state.get_data()
            disciplines_dict = state_data.get("disciplines_dict")
            await callback_query.message.answer(
                _("Выберите новую дисциплину для лабораторной работы"),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLabStates.waiting_for_new_discipline)


# @router.callback_query()
# async def debug_all_callbacks(callback: CallbackQuery):
#     print(f"Received callback: {callback.data}")
#     await callback.answer(f"Got: {callback.data}")


@router.callback_query(F.data.startswith("lab_status_"))
async def show_lab_list_status(callback_query: CallbackQuery, state: FSMContext):
    print(callback_query.data)
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    status_name = callback_query.data.replace("lab_status_", "")
    selected_status = Status[status_name]
    print(selected_status)

    state_data = await state.get_data()
    labs_data = state_data.get("labs_response")
    filtered_lab_list = []
    print(labs_data)
    for lab in labs_data["labs"]:
        print(lab)
        if lab["status"] == selected_status.value:
            filtered_lab_list.append(lab)
    print(filtered_lab_list)
    kb_list = [l["name"] for l in filtered_lab_list]
    await callback_query.message.answer(
        _("Выберите новую дисциплину для лабораторной работы"),
        reply_markup=kb.labs_list(kb_list, page=0))
    # TODO: отсортировать по сроку сдачи, создать список лаб с аббревиатурой предмета и вывести в виде кнопок


@router.callback_query(F.data.startswith("lab_page_"), ShowLabStates.waiting_for_lab)
async def handle_lab_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    labs = state_data.get("labs", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.labs_list(labs, page=page)
    )


@router.callback_query(F.data.startswith("lab_index_"),
                       or_f(AddLabStates.waiting_for_discipline, AddLabStates.waiting_for_new_discipline))
async def select_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()

    lab_index = int(callback_query.data.split("_")[-1])
    lab_id = state_data.get("labs_id")[lab_index]
    lab_name = state_data.get("labs")[lab_index]

    await state.update_data(lab_id=lab_id)
    await state.update_data(lab_name=lab_name)
    #
    # await callback_query.message.edit_reply_markup(
    #     reply_markup=None
    # )
    # if await state.get_state() == AddLabStates.waiting_for_discipline:
    #     await callback_query.message.answer(_("Введите название лабораторной работы."),
    #                                         reply_markup=None)
    #     await state.set_state(AddLabStates.waiting_for_name)
    # else:
    #     await show_lab_confirmation(callback_query.message, state)

# @router.message(EditLabStates.editing_name)
# async def request_new_name(message: Message, state: FSMContext):
#     state_data = await state.get_data()
#     prev_val = state_data.get("name")
#     await state.update_data(editing_value=name)
#     url_req = f"{settings.API_URL}/edit_lab"
#     response = requests.post(url_req, json={
#         "lab_id": state_data.get("chosen_lab_id"),
#         "editing_attribute": "name",
#         "editing_value": name})
#     if response.status_code == 200:
#         await state.update_data(chosen_discipline_name=name)
#         await message.answer(
#             _("Вы изменили название дисциплины {prev_val} на {val}.").format(prev_val=format_value(prev_val),
#                                                                              val=name)
#         )
#         menu_message = await message.answer(
#             str(__("Вы в меню дисциплины {name}.\n\n"
#                    "Преподаватель: {teacher}\n")).format(
#                 name=format_value(name),
#                 teacher=format_value(state_data.get("chosen_discipline_teacher")),
#             ),
#             reply_markup=kb.discipline_menu()
#         )
#         await state.update_data(menu_message_id=menu_message.message_id)
#     else:
#         await message.answer(json.loads(response.text).get('detail'))
