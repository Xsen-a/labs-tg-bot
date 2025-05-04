import base64
import re
import json
from io import BytesIO
import io

import requests
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, Document, BufferedInputFile, InputFile, FSInputFile

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.lesson_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit

router = Router()


def format_value(value):
    return "-" if value is None else value


def validate_minutes(minutes):
    if minutes.isdigit() and 0 <= int(minutes) <= 59:
        return True
    else:
        return False


class AddLessonStates(StatesGroup):
    adding_lab = State()
    waiting_for_discipline = State()
    waiting_for_classroom = State()
    waiting_for_start_date = State()
    waiting_for_start_hours = State()
    waiting_for_start_minutes = State()
    waiting_for_another_start_minutes = State()
    waiting_for_end_hours = State()
    waiting_for_end_minutes = State()
    waiting_for_another_end_minutes = State()
    waiting_for_periodicity = State()
    waiting_for_new_discipline = State()
    waiting_for_new_classroom = State()
    waiting_for_new_start_hour = State()
    waiting_for_new_start_minutes = State()
    waiting_for_new_another_start_minutes =  State()
    waiting_for_new_end_hour = State()
    waiting_for_new_end_minutes = State()
    waiting_for_new_another_end_minutes = State()
    waiting_for_new_start_date = State()
    waiting_for_new_periodicity = State()


class ShowLessonStates(StatesGroup):
    showing_list = State()
    showing_chosen_lesson = State()


class EditLessonStates(StatesGroup):
    editing_discipline = State()
    editing_classroom = State()
    editing_start_time = State()
    editing_end_time = State()
    editing_start_date = State()
    editing_periodicity = State()


async def show_lesson_confirmation(message: Message, state: FSMContext, bot: Bot = bot_unit):
    try:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=None
        )
    except Exception:
        pass

    state_data = await state.get_data()
    start_time = f'{state_data.get("start_hour")}:{state_data.get("start_minutes")}'
    end_time = f'{state_data.get("end_hour")}:{state_data.get("end_minutes")}'

    confirmation_text = _(
        "Вы действительно хотите добавить пару по дисциплине {discipline}?\n\n"
        "Аудитория: {classroom}\n"
        "Время начала: {start_time}\n"
        "Время окончания: {end_time}\n"
        "Дата первого занятия: {start_date}\n"
        "Периодичность (дней): {periodicity}"
    ).format(
        discipline=format_value(state_data.get("discipline_name")),
        classroom=format_value(state_data.get("classroom")),
        start_time=format_value(start_time),
        end_time=format_value(end_time),
        start_date=format_value(datetime.strptime(state_data.get("start_date"), "%Y-%m-%d").strftime("%d.%m.%Y")),
        periodicity=format_value(state_data.get("periodicity"))
    )
    await message.answer(
        confirmation_text,
        reply_markup=kb.add_lesson_confirm()
    )


@router.message(F.text == __("Добавить пару"))
async def add_lesson_start(message: Message, state: FSMContext):
    await state.set_state(AddLessonStates.adding_lab)
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
                _("Выберите дисциплину для проведения занятия."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLessonStates.waiting_for_discipline)
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lesson_disciplines_page_"),
                       or_f(AddLessonStates.waiting_for_discipline, AddLessonStates.waiting_for_new_discipline,
                            ShowLessonStates.showing_list, EditLessonStates.editing_discipline))
async def handle_disciplines_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    disciplines = state_data.get("disciplines", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.disciplines_list(disciplines, page=page)
    )


@router.callback_query(F.data.startswith("lesson_discipline_index_"),
                       or_f(AddLessonStates.waiting_for_discipline, AddLessonStates.waiting_for_new_discipline,
                            ShowLessonStates.showing_list, EditLessonStates.editing_discipline))
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

    if await state.get_state() == AddLessonStates.waiting_for_discipline:
        await callback_query.message.answer(_("Введите аудиторию, в которой проходит занятие."),
                                            reply_markup=None)
        await state.set_state(AddLessonStates.waiting_for_classroom)
    elif await state.get_state() == AddLessonStates.waiting_for_new_discipline:
        await show_lesson_confirmation(callback_query.message, state)
    elif await state.get_state() == ShowLessonStates.showing_list:
        pass
    #     labs_data = state_data.get("lessons_response")
    #     disciplines_dict = state_data.get("disciplines_dict")
    #     filtered_lab_list = []
    #     for lab in labs_data["labs"]:
    #         if lab["discipline_id"] == discipline_id:
    #             filtered_lab_list.append(lab)
    #     filtered_lab_list.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
    #     await state.update_data(labs=filtered_lab_list)
    # 
    #     if filtered_lab_list:
    #         info_string = f"Лабораторные работы по дисциплине {disciplines_dict[discipline_id]}\n\n"
    #         for lab in filtered_lab_list:
    #             info_string += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
    #                               __(f'{lab["name"]}\n') +
    #                               __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
    #                               __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n\n'))
    #     else:
    #         info_string = f"Лабораторных работ по дисциплине {disciplines_dict[discipline_id]} не найдено.\n\n"
    #     await callback_query.message.answer(
    #         info_string,
    #         reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, False, page=0))
    # elif await state.get_state() == EditLessonStates.editing_discipline:
    #     chosen_lab = state_data.get("chosen_lab")
    #     url_req = f"{settings.API_URL}/edit_lab"
    #     response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
    #                                             "editing_attribute": "discipline_id",
    #                                             "editing_value": str(discipline_id)})
    #     if response.status_code == 200:
    #         await callback_query.message.answer(
    #             _("Дисциплина успешно изменена на {discipline_name}.").format(discipline_name=discipline_name))
    #         chosen_lab["discipline_id"] = discipline_id
    #         await state.update_data(chosen_lab=chosen_lab)
    #         await state.set_state(ShowLessonStates.showing_chosen_lab)
    #         await show_chosen_lab_menu(callback_query.message, state)


@router.message(or_f(AddLessonStates.waiting_for_classroom, AddLessonStates.waiting_for_new_classroom,
                     EditLessonStates.editing_classroom))
async def get_lesson_name(message: Message, state: FSMContext):
    classroom = message.text
    await state.update_data(classroom=classroom)
    state_data = await state.get_data()
    if await state.get_state() == AddLessonStates.waiting_for_classroom:
        await message.answer(
            _("Выберите дату проведения занятия."),
            reply_markup=kb.calendar()
        )
        await state.set_state(AddLessonStates.waiting_for_start_date)
    elif await state.get_state() == AddLessonStates.waiting_for_new_classroom:
        await show_lesson_confirmation(message, state)
    elif await state.get_state() == EditLessonStates.editing_classroom:
        pass
        # chosen_lab = state_data.get("chosen_lab")
        # url_req = f"{settings.API_URL}/edit_lab"
        # response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
        #                                         "editing_attribute": "classroom",
        #                                         "editing_value": classroom})
        # if response.status_code == 200:
        #     await message.answer(
        #         _("Название успешно изменено на {classroom}.").format(classroom=classroom))
        #     chosen_lab["classroom"] = classroom
        #     await state.update_data(chosen_lab=chosen_lab)
        #     await state.set_state(ShowLessonStates.showing_chosen_lab)
        #     await show_chosen_lab_menu(message, state)


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
                       or_f(AddLessonStates.waiting_for_start_date, AddLessonStates.waiting_for_new_start_date,
                            EditLessonStates.editing_start_date))
async def select_start_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split("_")[-1]
    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    await state.update_data(start_date=start_date.strftime("%Y-%m-%d"))

    if await state.get_state() == AddLessonStates.waiting_for_start_date:
        await callback.message.edit_text(
            _("Выберите час начала занятия."),
            reply_markup=kb.get_keyboard_hours()
        )
        await state.set_state(AddLessonStates.waiting_for_start_hours)
    elif await state.get_state() == AddLessonStates.waiting_for_new_start_date:
        await show_lesson_confirmation(callback.message, state)
    elif await state.get_state() == EditLessonStates.editing_start_date:
        pass
        # chosen_lab = state_data.get("chosen_lab")
        # url_req = f"{settings.API_URL}/edit_lab"
        # response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
        #                                         "editing_attribute": "start_date",
        #                                         "editing_value": start_date.strftime("%Y-%m-%d")})
        # if response.status_code == 200:
        #     await callback.message.answer(
        #         _("Дата начала успешно изменена на {start_date}.").format(start_date=start_date))
        #     chosen_lab["start_date"] = start_date.strftime("%Y-%m-%d")
        #     await state.update_data(chosen_lab=chosen_lab)
        #     await state.set_state(ShowLessonStates.showing_chosen_lab)
        #     await show_chosen_lab_menu(callback.message, state)


@router.callback_query(F.data.startswith("hour_"), or_f(AddLessonStates.waiting_for_start_hours, AddLessonStates.waiting_for_new_start_hour))
async def add_start_hours(callback_query: CallbackQuery, state: FSMContext):
    start_hour = callback_query.data.split("_")[-1]
    if len(start_hour) != 2:
        start_hour = "0" + start_hour
    await state.update_data(start_hour=start_hour)
    try:
        await callback_query.message.edit_text(
            _("Выберите минуты начала занятий."),
            reply_markup=kb.get_keyboard_minutes()
        )
    except:
        await callback_query.message.answer(
            _("Выберите минуты начала занятий."),
            reply_markup=kb.get_keyboard_minutes()
        )
    if await state.get_state() == AddLessonStates.waiting_for_start_hours:
        await state.set_state(AddLessonStates.waiting_for_start_minutes)
    elif await state.get_state() == AddLessonStates.waiting_for_new_start_hour:
        await state.set_state(AddLessonStates.waiting_for_new_start_minutes)


@router.callback_query((F.data.startswith("minutes_") | (F.data == "another_minutes")), or_f(AddLessonStates.waiting_for_start_minutes, AddLessonStates.waiting_for_new_start_minutes))
async def add_start_minutes(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "another_minutes":

        try:
            await callback_query.message.edit_reply_markup(
                _("Введите минуты начала занятия."),
                reply_markup=None)
        except:
            await callback_query.message.answer(
                _("Введите минуты начала занятия."),
                reply_markup=None)
        if await state.get_state() == AddLessonStates.waiting_for_start_minutes:
            await state.set_state(AddLessonStates.waiting_for_another_start_minutes)
        elif await state.get_state() == AddLessonStates.waiting_for_new_start_minutes:
            await state.set_state(AddLessonStates.waiting_for_new_another_start_minutes)
    else:
        start_minutes = callback_query.data.split("_")[-1]
        await state.update_data(start_minutes=start_minutes)
    if await state.get_state() == AddLessonStates.waiting_for_start_minutes:
        try:
            await callback_query.message.edit_text(
                _("Выберите час конца занятий."),
                reply_markup=kb.get_keyboard_hours()
            )
        except:
            await callback_query.message.answer(
                _("Выберите час конца занятий."),
                reply_markup=kb.get_keyboard_hours()
            )
        await state.set_state(AddLessonStates.waiting_for_end_hours)
    elif await state.get_state() == AddLessonStates.waiting_for_new_start_minutes:
        await show_lesson_confirmation(callback_query.message, state)


@router.message(or_f(AddLessonStates.waiting_for_another_start_minutes, AddLessonStates.waiting_for_new_another_start_minutes))
async def add_another_start_minutes(msg: Message, state: FSMContext):
    new_start_minutes = msg.text
    if not validate_minutes(new_start_minutes):
        await msg.answer(_("Неверный формат минут. Пожалуйста, введите чисто от 0 до 59."))
        return
    else:
        if len(new_start_minutes) != 2:
            new_start_minutes = "0" + new_start_minutes
        await state.update_data(start_minutes=new_start_minutes)
        if await state.get_state() == AddLessonStates.waiting_for_another_start_minutes:
            try:
                await msg.edit_text(
                    _("Выберите час конца занятий."),
                    reply_markup=kb.get_keyboard_hours()
                )
            except:
                await msg.answer(
                    _("Выберите час конца занятий."),
                    reply_markup=kb.get_keyboard_hours()
                )
            await state.set_state(AddLessonStates.waiting_for_end_hours)
        elif await state.get_state() == AddLessonStates.waiting_for_new_another_start_minutes:
            await show_lesson_confirmation(msg, state)


@router.callback_query(F.data.startswith("hour_"), or_f(AddLessonStates.waiting_for_end_hours, AddLessonStates.waiting_for_new_end_hour))
async def add_end_hours(callback_query: CallbackQuery, state: FSMContext):
    end_hour = callback_query.data.split("_")[-1]
    if len(end_hour) != 2:
        end_hour = "0" + end_hour
    await state.update_data(end_hour=end_hour)
    try:
        await callback_query.message.edit_text(
            _("Выберите минуты конца занятий."),
            reply_markup=kb.get_keyboard_minutes()
        )
    except:
        await callback_query.message.answer(
            _("Выберите минуты конца занятий."),
            reply_markup=kb.get_keyboard_minutes()
        )
    if await state.get_state() == AddLessonStates.waiting_for_end_hours:
        await state.set_state(AddLessonStates.waiting_for_end_minutes)
    elif await state.get_state() == AddLessonStates.waiting_for_new_end_hour:
        await state.set_state(AddLessonStates.waiting_for_new_end_minutes)


@router.callback_query((F.data.startswith("minutes_") | (F.data == "another_minutes")), or_f(AddLessonStates.waiting_for_end_minutes, AddLessonStates.waiting_for_new_end_minutes))
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "another_minutes":
        try:
            await callback_query.message.edit_reply_markup(
                _("Введите минуты конца занятия."),
                reply_markup=None)
        except:
            await callback_query.message.answer(
                _("Введите минуты конца занятия."),
                reply_markup=None)
        if await state.get_state() == AddLessonStates.waiting_for_end_minutes:
            await state.set_state(AddLessonStates.waiting_for_another_end_minutes)
        elif await state.get_state() == AddLessonStates.waiting_for_new_end_minutes:
            await state.set_state(AddLessonStates.waiting_for_new_another_end_minutes)
    else:
        end_minutes = callback_query.data.split("_")[-1]
        await state.update_data(end_minutes=end_minutes)
        if await state.get_state() == AddLessonStates.waiting_for_end_minutes:
            try:
                await callback_query.message.edit_text(_("Является ли пара периодической?"),
                                                       reply_markup=kb.is_periodicity())
            except:
                await callback_query.message.answer(_("Является ли пара периодической?"),
                                                    reply_markup=kb.is_periodicity())
            await state.set_state(AddLessonStates.waiting_for_periodicity)
        elif await state.get_state() == AddLessonStates.waiting_for_new_end_minutes:
            await show_lesson_confirmation(callback_query.message, state)


@router.message(or_f(AddLessonStates.waiting_for_another_end_minutes, AddLessonStates.waiting_for_new_another_end_minutes))
async def add_another_end_minutes(msg: Message, state: FSMContext):
    new_end_minutes = msg.text
    if not validate_minutes(new_end_minutes):
        await msg.answer("Неверный формат минут. Пожалуйста, введите чисто от 0 до 59.")
        return
    else:
        if len(new_end_minutes) != 2:
            new_end_minutes = "0" + new_end_minutes
        await state.update_data(end_minutes=new_end_minutes)
        if await state.get_state() == AddLessonStates.waiting_for_another_end_minutes:
            try:
                await msg.edit_text(_("Является ли пара периодической?"),
                                    reply_markup=kb.is_periodicity())
            except:
                await msg.answer(_("Является ли пара периодической?"),
                                 reply_markup=kb.is_periodicity())
        elif await state.get_state() == AddLessonStates.waiting_for_new_another_end_minutes:
            await show_lesson_confirmation(msg, state)


@router.callback_query(F.data == "periodicity")
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_text(_("Выберите периодичность."),
                                           reply_markup=kb.periodicity_type())


@router.callback_query(F.data.startswith("periodicity_"))
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    field = callback_query.data.split("_")[-1]
    field = "".join(field)

    match field:
        case "day":
            await state.update_data(period_type="day")
            await callback_query.message.edit_text(
                _("Введите количество дней, через которые повторяется занятие."), reply_markup=None)
            await state.set_state(AddLessonStates.waiting_for_periodicity)
        case "week":
            await state.update_data(period_type="week")
            await callback_query.message.edit_text(
                _("Введите количество недель, через которые повторяется занятие."), reply_markup=None)
            await state.set_state(AddLessonStates.waiting_for_periodicity)


@router.callback_query(F.data == "not_periodicity", AddLessonStates.waiting_for_periodicity)
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(periodicity=0)
    await show_lesson_confirmation(callback_query.message, state)


@router.message(or_f(AddLessonStates.waiting_for_periodicity, EditLessonStates.editing_periodicity))
async def get_additional_info(message: Message, state: FSMContext):
    periodicity = message.text
    try:
        periodicity = int(periodicity)
    except Exception:
        await message.answer(
            _("Периодичность должна быть числом"))
        return

    state_data = await state.get_data()
    if await state.get_state() != EditLessonStates.editing_periodicity:
        period_type = state_data.get("period_type")
        if period_type == "day":
            await state.update_data(periodicity=int(periodicity))
        elif period_type == "week":
            await state.update_data(periodicity=int(periodicity) * 7)
        await show_lesson_confirmation(message, state, bot_unit)
    else:
        pass
        # chosen_lab = state_data.get("chosen_lab")
        # url_req = f"{settings.API_URL}/edit_lab"
        # response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
        #                                         "editing_attribute": "extra_info",
        #                                         "editing_value": additional_info})
        # if response.status_code == 200:
        #     await message.answer(
        #         _("Дополнительная информация успешно изменена."))
        #     chosen_lab["extra-info"] = additional_info
        #     await state.update_data(chosen_lab=chosen_lab)
        #     await state.set_state(ShowLessonStates.showing_chosen_lab)
        #     await show_chosen_lab_menu(message, state)


@router.callback_query(F.data == "add_lesson")
async def confirm_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()

    start_time = f'{state_data.get("start_hour")}:{state_data.get("start_minutes")}:00'
    end_time = f'{state_data.get("end_hour")}:{state_data.get("end_minutes")}:00'
    lesson_data = {
        "user_id": state_data.get("user_id"),
        "discipline_id": state_data.get("discipline_id"),
        "classroom": state_data.get("classroom"),
        "start_date": state_data.get("start_date"),
        "start_time": start_time,
        "end_time": end_time,
        "periodicity_days": state_data.get("periodicity")
    }
    print(lesson_data)
    url_req = f"{settings.API_URL}/add_lesson"
    response = requests.post(url_req, json=lesson_data)

    if response.status_code == 200:
        await callback_query.message.answer(
            _("Занятие по дисциплине {discipline} на время {start_time} - {end_time} периодичностью {periodicity} дней добавлено.").format(
                discipline=state_data.get("discipline_name"),
                start_time=start_time,
                end_time=end_time,
                periodicity=state_data.get("periodicity")
            )
        )
        await main_bot_handler.open_labs_menu(callback_query.message, state, state_data.get("telegram_id"))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_add_lesson")
async def cancel_add_lesson(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    await callback_query.message.answer("Вы отменили добавление занятия.")
    state_data = await state.get_data()
    await main_bot_handler.open_lesson_menu(callback_query.message, state, state_data.get("telegram_id"))


@router.callback_query(F.data.startswith("change_lesson_"))
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
                _("Выберите новую дисциплину для занятия."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(AddLessonStates.waiting_for_new_discipline)
        case "classroom":
            await callback_query.message.answer(_("Введите новую аудиторию для занятия."))
            await state.set_state(AddLessonStates.waiting_for_new_classroom)
        case "start_date":
            await callback_query.message.answer(
                _("Выберите дату проведения занятия."),
                reply_markup=kb.calendar()
            )
            await state.set_state(AddLessonStates.waiting_for_new_start_date)
        case "start_time":
            await callback_query.message.answer(
                _("Выберите час начала занятия."),
                reply_markup=kb.get_keyboard_hours()
            )
            await state.set_state(AddLessonStates.waiting_for_new_start_hour)
        case "end_time":
            await callback_query.message.answer(
                _("Выберите час конца занятия."),
                reply_markup=kb.get_keyboard_hours()
            )
            await state.set_state(AddLessonStates.waiting_for_new_end_hour)
        case "periodicity":
            await callback_query.message.answer(_("Является ли пара периодической?"),
                                                reply_markup=kb.is_periodicity())
            await state.set_state(AddLessonStates.waiting_for_periodicity)

    await callback_query.answer()

# @router.message(F.text == __("Посмотреть список лабораторных работ"))
# async def show_lab_list(message: Message, state: FSMContext):
#     await state.set_state(ShowLessonStates.showing_list)
#
#     state_data = await state.get_data()
#     url_req = f"{settings.API_URL}/get_user_id"
#     response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})
#
#     if response.status_code == 200:
#         user_id = response.json().get("user_id")
#         await state.update_data(user_id=user_id)
#         url_req = f"{settings.API_URL}/get_labs"
#         response = requests.get(url_req, json={"user_id": user_id})
#         if response.status_code == 200:
#             response_data = response.json()
#             await state.update_data(labs_response=response_data)
#
#             url_req = f"{settings.API_URL}/get_disciplines"
#             response = requests.get(url_req, json={"user_id": user_id})
#
#             if response.status_code == 200:
#                 disciplines = response.json().get("disciplines", [])
#                 sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
#                 disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
#                 await state.update_data(disciplines_dict=disciplines_dict)
#                 await state.update_data(disciplines=list(disciplines_dict.values()))
#                 await state.update_data(disciplines_id=list(disciplines_dict.keys()))
#                 await message.answer(
#                     _("Выберите вид отображения списка."),
#                     reply_markup=kb.list_show_option()
#                 )
#         else:
#             await message.answer(json.loads(response.text).get('detail'))
#     else:
#         await message.answer(json.loads(response.text).get('detail'))
#
#
# @router.callback_query(F.data.startswith("lab_list_"))
# async def show_lab_list_option(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     field = callback_query.data.split("_")[-1]
#
#     match field:
#         case "status":
#             await callback_query.message.answer(
#                 _("Выберите статус."),
#                 reply_markup=kb.status_option())
#         case "discipline":
#             state_data = await state.get_data()
#             disciplines_dict = state_data.get("disciplines_dict")
#             await callback_query.message.answer(
#                 _("Выберите дисциплину."),
#                 reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
#         case "week":
#             state_data = await state.get_data()
#             labs_data = state_data.get("labs_response")
#             disciplines_dict = state_data.get("disciplines_dict")
#             await state.update_data(show_abb=True)
#             filtered_lab_list_undone = []
#             filtered_lab_list_process = []
#
#             today = datetime.now().date()
#             date_mark = today + timedelta(days=7)
#
#             for lab in labs_data["labs"]:
#                 if datetime.strptime(lab["end_date"], "%Y-%m-%d").date() < date_mark:
#                     if lab["status"] != 'Сдано' and datetime.strptime(lab["end_date"], "%Y-%m-%d").date() < today:
#                         filtered_lab_list_undone.append(lab)
#                     else:
#                         filtered_lab_list_process.append(lab)
#             filtered_lab_list_undone.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
#             filtered_lab_list_process.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
#             filtered_lab_list = filtered_lab_list_undone + filtered_lab_list_process
#             await state.update_data(labs=filtered_lab_list)
#
#             if filtered_lab_list_undone or filtered_lab_list_process:
#                 if filtered_lab_list_undone:
#                     info_string_undone = __(f"<b>Просроченные лабораторные работы:</b>\n\n")
#                     for lab in filtered_lab_list_undone:
#                         info_string_undone += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
#                                                  __(f'{lab["name"]}\n') +
#                                                  __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
#                                                  __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n\n'))
#                 else:
#                     info_string_undone = __(f"<b>Просроченных лабораторных работ не найдено.</b>\n\n")
#                 if filtered_lab_list_process:
#                     info_string_process = __(f"<b>Предстоящие лабораторные работы на следующие 7 дней:</b>\n\n")
#                     for lab in filtered_lab_list_process:
#                         info_string_process += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
#                                                   __(f'{lab["name"]}\n') +
#                                                   __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
#                                                   __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n\n'))
#                 else:
#                     info_string_process = __(f"<b>Лабораторных работ на ближайшие 7 дней не найдено.</b>\n\n")
#                 info_string = info_string_undone + info_string_process
#             else:
#                 info_string = __(f"Лабораторных работ не найдено.\n\n")
#             await callback_query.message.answer(
#                 info_string,
#                 reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, True, page=0),
#                 parse_mode="HTML")
#
#
# @router.callback_query(F.data == "back_to_options")
# async def back_to_options(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     await callback_query.message.answer(
#         _("Выберите вид отображения списка."),
#         reply_markup=kb.list_show_option()
#     )
#
#
# @router.callback_query(F.data.startswith("lab_status_"),
#                        or_f(ShowLessonStates.showing_list, ShowLessonStates.showing_chosen_lab))
# async def show_lab_list_status(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     state_data = await state.get_data()
#
#     status_name = callback_query.data.replace("lab_status_", "")
#     selected_status = Status[status_name]
#
#     if await state.get_state() == ShowLessonStates.showing_list:
#         labs_data = state_data.get("labs_response")
#         disciplines_dict = state_data.get("disciplines_dict")
#         await state.update_data(show_abb=True)
#         filtered_lab_list = []
#         for lab in labs_data["labs"]:
#             if lab["status"] == selected_status.value:
#                 filtered_lab_list.append(lab)
#         filtered_lab_list.sort(key=lambda x: datetime.strptime(x["end_date"], "%Y-%m-%d"))
#         await state.update_data(labs=filtered_lab_list)
#
#         if filtered_lab_list:
#             info_string = f"Лабораторные работы со статусом: {selected_status.value}\n\n"
#             for lab in filtered_lab_list:
#                 info_string += __(f'Дисциплина: {disciplines_dict[lab["discipline_id"]]}\n' +
#                                   __(f'{lab["name"]}\n') +
#                                   __(f'Дата начала: {datetime.strptime(lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n') +
#                                   __(f'Срок сдачи: {datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")}\n\n'))
#         else:
#             info_string = f"Лабораторных работ со статусом {selected_status.value} не найдено.\n\n"
#         await callback_query.message.answer(
#             info_string,
#             reply_markup=kb.labs_list(filtered_lab_list, disciplines_dict, True, page=0))
#     elif await state.get_state() == ShowLessonStates.showing_chosen_lab:
#         chosen_lab = state_data.get("chosen_lab")
#         url_req = f"{settings.API_URL}/edit_lab"
#         response = requests.post(url_req, json={"task_id": chosen_lab["task_id"],
#                                                 "editing_attribute": "status",
#                                                 "editing_value": status_name})
#         if response.status_code == 200:
#             await callback_query.message.answer(
#                 _("Статус успешно изменен на {new_status}.").format(new_status=selected_status.value))
#             chosen_lab["status"] = selected_status.value
#             await state.update_data(chosen_lab=chosen_lab)
#             await state.set_state(ShowLessonStates.showing_chosen_lab)
#             await show_chosen_lab_menu(callback_query.message, state)
#
#
# async def show_chosen_lab_menu(message: Message, state: FSMContext, bot: Bot = bot_unit):
#     state_data = await state.get_data()
#     disciplines_dict = state_data.get("disciplines_dict")
#     chosen_lab = state_data.get("chosen_lab")
#
#     url_req = f"{settings.API_URL}/get_lab_files"
#     response = requests.get(url_req, json={"task_id": chosen_lab["task_id"]})
#     if response.status_code == 200:
#         response_data = response.json()
#         file_names = [file['file_name'] for file in response_data.get("files", [])]
#         confirmation_text = _(
#             "Вы в меню лабораторной работы:\n\n"
#             "Дисциплина: {discipline}\n"
#             "Название: {name}\n"
#             "Текст задания: {description}\n"
#             "Файлы: {files}\n"
#             "Ссылка: {link}\n"
#             "Дата начала: {start_date}\n"
#             "Срок сдачи: {end_date}\n"
#             "Доп. информация: {additional_info}\n"
#             "Статус: <b>{status}</b>"
#         ).format(
#             name=format_value(chosen_lab["name"]),
#             discipline=format_value(disciplines_dict[chosen_lab["discipline_id"]]),
#             description=format_value(chosen_lab["task_text"]),
#             files=", ".join(file_names) if file_names else "-",
#             link=format_value(chosen_lab["task_link"]),
#             start_date=format_value(datetime.strptime(chosen_lab["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
#             end_date=format_value(datetime.strptime(chosen_lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
#             additional_info=format_value(chosen_lab["extra_info"]),
#             status=chosen_lab["status"]
#         )
#
#         await message.answer(
#             confirmation_text,
#             reply_markup=kb.lab_menu(),
#             parse_mode="HTML"
#         )
#
#         for file_info in response_data["files"]:
#             try:
#                 file_bytes = base64.b64decode(file_info['file_data'])
#                 file_data = BufferedInputFile(file_bytes, filename=file_info["file_name"])
#                 if file_info['file_type'] == 'document':
#                     await bot.send_document(
#                         chat_id=message.chat.id,
#                         document=file_data
#                     )
#                 elif file_info['file_type'] == 'photo':
#                     await bot.send_photo(
#                         chat_id=message.chat.id,
#                         photo=file_data
#                     )
#                 elif file_info['file_type'] == 'video':
#                     await bot.send_video(
#                         chat_id=message.chat.id,
#                         video=file_data,
#                         supports_streaming=True
#                     )
#                 elif file_info['file_type'] == 'audio':
#                     await bot.send_audio(
#                         chat_id=message.chat.id,
#                         audio=file_data,
#                     )
#             except Exception as e:
#                 await message.answer(
#                     _("Не удалось отправить файл").format(error=str(e))
#                 )
#
#
# @router.callback_query(F.data.startswith("lab_page_"), ShowLessonStates.showing_list)
# async def handle_lab_pagination(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     show_abb = state_data.get("show_abb")
#     labs = state_data.get("labs", [])
#     disciplines_dict = state_data.get("disciplines_dict")
#
#     page = int(callback_query.data.split("_")[-1])
#     await state.update_data(current_page=page)
#
#     await callback_query.message.edit_reply_markup(
#         reply_markup=kb.labs_list(labs, disciplines_dict, show_abb, page=page)
#     )
#
#
# @router.callback_query(F.data.startswith("lab_index_"))
# async def show_chosen_lab_info(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
#     await state.set_state(ShowLessonStates.showing_chosen_lab)
#     await callback_query.answer()
#     state_data = await state.get_data()
#
#     lab_index = int(callback_query.data.split("_")[-1])
#     labs = state_data.get("labs")
#     chosen_lab = next((lab for lab in labs if lab["task_id"] == lab_index), None)
#     await state.update_data(chosen_lab=chosen_lab)
#
#     await show_chosen_lab_menu(callback_query.message, state)
#
#
# @router.callback_query(F.data == "edit_status")
# async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     await callback_query.answer()
#     await callback_query.message.answer(
#         _("Выберите статус для изменения."),
#         reply_markup=kb.status_option()
#     )
#
#
# @router.callback_query(F.data == "edit_lab")
# async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     await callback_query.answer()
#     state_data = await state.get_data()
#     await callback_query.message.answer(
#         _("Выберите информацию для изменения."),
#         reply_markup=kb.lab_edit_menu()
#     )
#
#
# @router.callback_query(F.data.startswith("edit_lab_"))
# async def edit_lab_status(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     await callback_query.answer()
#
#     field = callback_query.data.split("_")[2:]
#     if len(field) > 1:
#         field = "_".join(field)
#     else:
#         field = "".join(field)
#     await state.update_data(editing_attribute=field)
#
#     match field:
#         case "discipline":
#             state_data = await state.get_data()
#             disciplines_dict = state_data.get("disciplines_dict")
#             await callback_query.message.answer(
#                 _("Выберите новую дисциплину для лабораторной работы."),
#                 reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
#             await state.set_state(EditLessonStates.editing_discipline)
#         case "name":
#             await callback_query.message.answer(_("Введите новое название лабораторной работы."))
#             await state.set_state(EditLessonStates.editing_name)
#         case "description":
#             await callback_query.message.answer(_("Введите новый текст лабораторной работы."))
#             await state.set_state(EditLessonStates.editing_description)
#         case "files":
#             await callback_query.message.answer(
#                 _("Прикрепите заново файл(ы) с заданием для лабораторной работы размером до 50 МБ."),
#                 reply_markup=kb.finish_files_button())
#             await state.set_state(EditLessonStates.editing_files)
#         case "link":
#             await callback_query.message.answer(
#                 _("Введите новую ссылку на задание для лабораторной работы."))
#             await state.set_state(EditLessonStates.editing_link)
#         case "start_date":
#             await callback_query.message.answer(
#                 _("Выберите новую дату начала выполнения лабораторной работы."),
#                 reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
#             await state.set_state(EditLessonStates.editing_start_date)
#         case "end_date":
#             await callback_query.message.answer(
#                 _("Выберите новую дату сдачи лабораторной работы."),
#                 reply_markup=kb.calendar(datetime.now().year, datetime.now().month))
#             await state.set_state(EditLessonStates.editing_end_date)
#         case "additional_info":
#             await callback_query.message.answer(
#                 _("Введите новую дополнительную информацию о лабораторной работе."))
#             await state.set_state(EditLessonStates.editing_additional_info)
#
#     await callback_query.answer()
#
#
# @router.callback_query(F.data == "delete_lab")
# async def ask_deleting_lab(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.message.edit_reply_markup(
#         reply_markup=None
#     )
#     await callback_query.answer()
#     state_data = await state.get_data()
#     chosen_lab = state_data.get("chosen_lab")
#     await callback_query.message.answer(
#         _("Вы действительно хотите удалить лабораторную работу {name}?")
#         .format(name=chosen_lab["name"]),
#         reply_markup=kb.confirm_delete_lab()
#     )
#
#
# @router.callback_query(F.data == "confirm_deleting_lab")
# async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     chosen_lab = state_data.get("chosen_lab")
#     url_req = f"{settings.API_URL}/delete_lab"
#     response = requests.delete(url_req, json={"task_id": chosen_lab["task_id"]})
#     if response.status_code == 200:
#         await callback_query.message.bot.delete_message(
#             chat_id=callback_query.message.chat.id,
#             message_id=callback_query.message.message_id,
#         )
#         await callback_query.message.answer(
#             _("Лабораторная работа {name} успешно удалена.")
#             .format(name=chosen_lab["name"])
#         )
#         await show_lab_list(callback_query.message, state)
#     else:
#         await callback_query.message.answer(json.loads(response.text).get('detail'))
#
#
# @router.callback_query(F.data == "cancel_deleting_lab")
# async def cancel_deleting(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     chosen_lab = state_data.get("chosen_lab")
#     await callback_query.message.bot.edit_message_reply_markup(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#         reply_markup=None
#     )
#     await callback_query.message.answer(
#         _("Вы отменили удаление лабораторной работы {name}.")
#         .format(name=chosen_lab["name"])
#     )
#     await show_chosen_lab_menu(callback_query.message, state)
#
#
# @router.callback_query(F.data == "back_to_lab_menu")
# async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#     )
#     await show_lab_list(callback_query.message, state)
