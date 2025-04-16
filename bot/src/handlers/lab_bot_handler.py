import re
import json
import requests
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, Document

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.lab_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit

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
        start_date=format_value(state_data.get("start_date")),
        end_date=format_value(state_data.get("end_date")),
        additional_info=format_value(state_data.get("additional_info"))
    )

    await message.answer(
        confirmation_text,
        reply_markup=kb.add_lab_confirm(True)
    )

    # Затем отправляем файлы по одному
    if state_data.get("files"):
        for file_info in state_data["files"]:
            try:
                if isinstance(file_info, dict):
                    file_id = file_info['file_id']
                    #file_name = file_info.get('file_name', 'file')

                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=file_id,
                        #caption=f"Файл: {file_name}"
                    )
                else:
                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=file_info
                    )
            except Exception as e:
                await message.answer(
                    _("Не удалось отправить файл: {error}").format(error=str(e))
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


@router.callback_query(F.data.startswith("lab_discipline_index_"), AddLabStates.waiting_for_discipline)
async def select_discipline(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()

    discipline_index = int(callback_query.data.split("_")[-1])
    discipline_id = state_data.get("disciplines_id")[discipline_index]
    discipline_name = state_data.get("disciplines")[discipline_index]

    await state.update_data(discipline_id=discipline_id)
    await state.update_data(discipline_name=discipline_name)
    print(discipline_id, discipline_name)

    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.message.answer(_("Введите название лабораторной работы."),
                                        reply_markup=None)
    await state.set_state(AddLabStates.waiting_for_name)


@router.message(AddLabStates.waiting_for_name)
async def get_lab_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(lab_name=name)
    await message.answer(
        _("Введите текст лабораторной работы"),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddLabStates.waiting_for_description)


@router.message(AddLabStates.waiting_for_description)
async def get_lab_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer(
        _("Прикрепите файл с заданием для лабораторной работы размером до 1 ГБ"),
        reply_markup=kb.finish_files_button()
    )
    await state.set_state(AddLabStates.waiting_for_files)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_description)
async def skip_description(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(description=None)
    await callback_query.message.edit_text(
        _("Прикрепите файл с заданием для лабораторной работы размером до 1 ГБ"),
        reply_markup=kb.finish_files_button()
    )
    await state.set_state(AddLabStates.waiting_for_files)


@router.message(AddLabStates.waiting_for_files, F.document)
async def get_lab_file(message: Message, state: FSMContext):
    document = message.document
    if document.file_size > 1073741824:
        await message.answer(_("Файл слишком большой. Максимальный размер - 1 ГБ"))
        return

    try:
        file_info = {
            'file_id': document.file_id,
            'file_name': document.file_name or "Без названия",
            'file_size': document.file_size,
            'mime_type': document.mime_type
        }

        state_data = await state.get_data()
        files = state_data.get("files", [])
        files.append(file_info)
        await state.update_data(files=files)

        await message.answer(
            _("Файл '{file_name}' успешно загружен. Прикрепите еще один файл или нажмите 'Завершить добавление файлов'").format(
                file_name=file_info['file_name']
            ),
            reply_markup=kb.finish_files_button()
        )
    except Exception as e:
        await message.answer(_("Произошла ошибка при загрузке файла: {error}").format(error=str(e)))


@router.callback_query(F.data == "finish_files", AddLabStates.waiting_for_files)
async def finish_files(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_text(
        _("Вставьте ссылку на задание лабораторной работы"),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddLabStates.waiting_for_link)


@router.message(AddLabStates.waiting_for_link)
async def get_lab_link(message: Message, state: FSMContext):
    link = message.text
    if not re.match(r'^https?://', link):
        await message.answer(_("Пожалуйста, введите корректную ссылку (начинается с http:// или https://)"))
        return

    await state.update_data(link=link)
    await message.answer(
        _("Выберите дату начала выполнения лабораторной работы"),
        reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
    )
    await state.set_state(AddLabStates.waiting_for_start_date)


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


@router.callback_query(F.data.startswith("calendar_date_"), AddLabStates.waiting_for_start_date)
async def select_start_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split("_")[-1]
    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Сохраняем как строку в формате DD.MM.YYYY
    await state.update_data(start_date=start_date.strftime("%d.%m.%Y"))

    await callback.message.edit_text(
        _("Выберите дату сдачи лабораторной работы"),
        reply_markup=kb.calendar(datetime.now().year, datetime.now().month)
    )
    print(await state.get_data())
    await state.set_state(AddLabStates.waiting_for_end_date)


@router.callback_query(F.data.startswith("calendar_date_"), AddLabStates.waiting_for_end_date)
async def select_end_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    # Получаем выбранную дату
    date_str = callback.data.split("_")[-1]
    end_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Получаем дату начала из состояния
    state_data = await state.get_data()
    start_date_str = state_data.get("start_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()

        # Сравниваем даты
        if end_date < start_date:
            await callback.message.answer(
                _("Дата сдачи не может быть раньше даты начала. Пожалуйста, выберите другую дату.")
            )
            return

    # Сохраняем дату сдачи
    await state.update_data(end_date=end_date.strftime("%d.%m.%Y"))

    await callback.message.edit_text(
        _("Введите дополнительную информацию о лабораторной работе"),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddLabStates.waiting_for_additional_info)


@router.message(AddLabStates.waiting_for_additional_info)
async def get_additional_info(message: Message, state: FSMContext):
    additional_info = message.text
    await state.update_data(additional_info=additional_info)
    await show_lab_confirmation(message, state, bot_unit)


@router.callback_query(F.data == "skip", AddLabStates.waiting_for_additional_info)
async def skip_additional_info(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(additional_info=None)
    await show_lab_confirmation(callback_query.message, state, bot_unit)



#     @router.callback_query(F.data == "confirm_lab", AddLabWorkStates.confirmation)
#     async def confirm_lab(callback_query: CallbackQuery, state: FSMContext):
#         await callback_query.answer()
#         state_data = await state.get_data()
#
#         lab_data = {
#             "user_id": state_data.get("user_id"),
#             "discipline_id": state_data.get("discipline_id"),
#             "name": state_data.get("lab_name"),
#             "description": state_data.get("description"),
#             "files": state_data.get("files", []),
#             "link": state_data.get("link"),
#             "start_date": state_data.get("start_date"),
#             "end_date": state_data.get("end_date"),
#             "additional_info": state_data.get("additional_info"),
#             "status": "not_started"
#         }
#
#         url_req = f"{settings.API_URL}/add_lab"
#         response = requests.post(url_req, json=lab_data)
#
#         if response.status_code == 200:
#             await callback_query.message.edit_text(
#                 _("Лабораторная работа {name} со статусом 'Не начато' для дисциплины {discipline} успешно добавлена. Если необходимо, измените статус в меню лабораторной работы").format(
#                     name=state_data.get("lab_name"),
#                     discipline=state_data.get("discipline_name")
#                 )
#             )
#             await main_bot_handler.open_lab_menu(callback_query.message, state, state_data.get("telegram_id"))
#         else:
#             await callback_query.message.answer(json.loads(response.text).get('detail'))
#
#     @router.callback_query(F.data.startswith("edit_lab_"), AddLabWorkStates.confirmation)
#     async def edit_lab_field(callback_query: CallbackQuery, state: FSMContext):
#         await callback_query.answer()
#         field = callback_query.data.split("_")[-1]
#
#         match field:
#             case "discipline":
#                 await callback_query.message.edit_text(
#                     _("Выберите дисциплину для лабораторной работы"),
#                     reply_markup=kb.disciplines_list(state_data.get("disciplines"),
#                                                      page=state_data.get("current_page", 0))
#                 await state.set_state(AddLabWorkStates.waiting_for_discipline)
#                 case
#                 "name":
#                 await callback_query.message.edit_text(_("Введите название лабораторной работы"))
#                 await state.set_state(AddLabWorkStates.waiting_for_name)
#                 case
#                 "description":
#                 await callback_query.message.edit_text(
#                     _("Введите текст лабораторной работы"),
#                     reply_markup=kb.skip_button())
#                 await state.set_state(AddLabWorkStates.waiting_for_description)
#                 case
#                 "files":
#                 await callback_query.message.edit_text(
#                     _("Прикрепите файл с заданием для лабораторной работы размером до 1 ГБ"),
#                     reply_markup=kb.finish_files_button())
#                 await state.set_state(AddLabWorkStates.waiting_for_files)
#                 case
#                 "link":
#                 await callback_query.message.edit_text(
#                     _("Вставьте ссылку на задание лабораторной работы"),
#                     reply_markup=kb.skip_button())
#                 await state.set_state(AddLabWorkStates.waiting_for_link)
#                 case
#                 "start_date":
#                 await callback_query.message.edit_text(
#                     _("Выберите дату начала выполнения лабораторной работы"),
#                     reply_markup=kb.calendar(datetime.now()))
#                 await state.set_state(AddLabWorkStates.waiting_for_start_date)
#                 case
#                 "end_date":
#                 await callback_query.message.edit_text(
#                     _("Выберите дату сдачи лабораторной работы"),
#                     reply_markup=kb.calendar(datetime.now()))
#                 await state.set_state(AddLabWorkStates.waiting_for_end_date)
#                 case
#                 "additional_info":
#                 await callback_query.message.edit_text(
#                     _("Введите дополнительную информацию о лабораторной работе"),
#                     reply_markup=kb.skip_button())
#                 await state.set_state(AddLabWorkStates.waiting_for_additional_info)
#
#                 @ router.callback_query(F.data == "cancel_lab", AddLabWorkStates.confirmation)
#                 async
#
#                 def cancel_lab(callback_query: CallbackQuery, state: FSMContext):
#         await callback_query.answer()
#         await callback_query.message.edit_text(_("Добавление лабораторной работы отменено"))
#         await main_bot_handler.open_lab_menu(callback_query.message, state, state_data.get("telegram_id"))
