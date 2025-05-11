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
    editing_start_hour = State()
    editing_start_minutes = State()
    editing_another_start_minutes = State()
    editing_end_hour = State()
    editing_end_minutes = State()
    editing_another_end_minutes = State()
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
    elif await state.get_state() == EditLessonStates.editing_discipline:
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "discipline_id",
                                                "editing_value": str(discipline_id)})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Дисциплина успешно изменена на {discipline_name}.").format(discipline_name=discipline_name))
            chosen_lesson["discipline_id"] = discipline_id
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(callback_query.message, state)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddLessonStates.waiting_for_classroom, AddLessonStates.waiting_for_new_classroom,
                     EditLessonStates.editing_classroom))
async def get_lesson_name(message: Message, state: FSMContext):
    classroom = message.text
    await state.update_data(classroom=classroom)
    state_data = await state.get_data()
    if await state.get_state() == AddLessonStates.waiting_for_classroom:
        await message.answer(
            _("Выберите дату проведения первого (или единичного) занятия."),
            reply_markup=kb.calendar()
        )
        await state.set_state(AddLessonStates.waiting_for_start_date)
    elif await state.get_state() == AddLessonStates.waiting_for_new_classroom:
        await show_lesson_confirmation(message, state)
    elif await state.get_state() == EditLessonStates.editing_classroom:
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "classroom",
                                                "editing_value": classroom})
        if response.status_code == 200:
            await message.answer(
                _("Аудитория успешно изменена на {classroom}.").format(classroom=classroom))
            chosen_lesson["classroom"] = classroom
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(message, state)
        else:
            await message.answer(json.loads(response.text).get('detail'))


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
        state_data = await state.get_data()
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "start_date",
                                                "editing_value": start_date.strftime("%Y-%m-%d")})
        if response.status_code == 200:
            await callback.message.answer(
                _("Дата начала успешно изменена на {start_date}.").format(start_date=start_date))
            chosen_lesson["start_date"] = start_date.strftime("%Y-%m-%d")
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(callback.message, state)
        else:
            await callback.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("hour_"),
                       or_f(AddLessonStates.waiting_for_start_hours,
                            AddLessonStates.waiting_for_new_start_hour,
                            EditLessonStates.editing_start_hour))
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
    elif await state.get_state() == EditLessonStates.editing_start_hour:
        await state.set_state(EditLessonStates.editing_start_minutes)


@router.callback_query((F.data.startswith("minutes_") | (F.data == "another_minutes")),
                       or_f(AddLessonStates.waiting_for_start_minutes,
                            AddLessonStates.waiting_for_new_start_minutes,
                            EditLessonStates.editing_start_minutes))
async def add_start_minutes(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "another_minutes":
        try:
            await callback_query.message.edit_reply_markup(
                _("Введите минуты начала занятия, число от 0 до 59."),
                reply_markup=None)
        except:
            await callback_query.message.answer(
                _("Введите минуты начала занятия, число от 0 до 59."),
                reply_markup=None)
        if await state.get_state() == AddLessonStates.waiting_for_start_minutes:
            await state.set_state(AddLessonStates.waiting_for_another_start_minutes)
        elif await state.get_state() == AddLessonStates.waiting_for_new_start_minutes:
            await state.set_state(AddLessonStates.waiting_for_new_another_start_minutes)
        elif await state.get_state() == EditLessonStates.editing_start_minutes:
            await state.set_state(EditLessonStates.editing_another_start_minutes)
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
    elif await state.get_state() == EditLessonStates.editing_start_minutes:
        state_data = await state.get_data()
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "start_time",
                                                "editing_value": f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Время начала успешно изменено на {start_time}.").format(start_time=f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'))
            chosen_lesson["start_time"] = f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(callback_query.message, state)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddLessonStates.waiting_for_another_start_minutes, AddLessonStates.waiting_for_new_another_start_minutes, EditLessonStates.editing_another_start_minutes))
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
        elif await state.get_state() == EditLessonStates.editing_another_start_minutes:
            state_data = await state.get_data()
            chosen_lesson = state_data.get("chosen_lesson")
            url_req = f"{settings.API_URL}/edit_lesson"
            response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                    "editing_attribute": "start_time",
                                                    "editing_value": f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'})
            if response.status_code == 200:
                await msg.answer(
                    _("Время начала успешно изменено на {start_time}.").format(
                        start_time=f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'))
                chosen_lesson["start_time"] = f'{state_data["start_hour"]}:{state_data["start_minutes"]}:00'
                await state.update_data(chosen_lesson=chosen_lesson)
                await state.set_state(ShowLessonStates.showing_chosen_lesson)
                await show_chosen_lesson_menu(msg, state)
            else:
                await msg.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("hour_"),
                       or_f(AddLessonStates.waiting_for_end_hours,
                            AddLessonStates.waiting_for_new_end_hour,
                            EditLessonStates.editing_end_hour))
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
    elif await state.get_state() == EditLessonStates.editing_end_hour:
        await state.set_state(EditLessonStates.editing_end_minutes)


@router.callback_query((F.data.startswith("minutes_") | (F.data == "another_minutes")),
                       or_f(AddLessonStates.waiting_for_end_minutes,
                            AddLessonStates.waiting_for_new_end_minutes,
                            EditLessonStates.editing_end_minutes))
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "another_minutes":
        try:
            await callback_query.message.edit_reply_markup(
                _("Введите минуты конца занятия, число от 0 до 59."),
                reply_markup=None)
        except:
            await callback_query.message.answer(
                _("Введите минуты конца занятия, число от 0 до 59."),
                reply_markup=None)
        if await state.get_state() == AddLessonStates.waiting_for_end_minutes:
            await state.set_state(AddLessonStates.waiting_for_another_end_minutes)
        elif await state.get_state() == AddLessonStates.waiting_for_new_end_minutes:
            await state.set_state(AddLessonStates.waiting_for_new_another_end_minutes)
        elif await state.get_state() == EditLessonStates.editing_end_minutes:
            await state.set_state(EditLessonStates.editing_another_end_minutes)
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
        elif await state.get_state() == EditLessonStates.editing_end_minutes:
            state_data = await state.get_data()
            chosen_lesson = state_data.get("chosen_lesson")
            url_req = f"{settings.API_URL}/edit_lesson"
            response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                    "editing_attribute": "end_time",
                                                    "editing_value": f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'})
            if response.status_code == 200:
                await callback_query.message.answer(
                    _("Время окончания успешно изменено на {end_time}.").format(
                        end_time=f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'))
                chosen_lesson["end_time"] = f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'
                await state.update_data(chosen_lesson=chosen_lesson)
                await state.set_state(ShowLessonStates.showing_chosen_lesson)
                await show_chosen_lesson_menu(callback_query.message, state)
            else:
                await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddLessonStates.waiting_for_another_end_minutes, AddLessonStates.waiting_for_new_another_end_minutes, EditLessonStates.editing_another_end_minutes))
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
            await state.set_state(AddLessonStates.waiting_for_periodicity)
        elif await state.get_state() == AddLessonStates.waiting_for_new_another_end_minutes:
            await show_lesson_confirmation(msg, state)
        elif await state.get_state() == EditLessonStates.editing_another_end_minutes:
            state_data = await state.get_data()
            chosen_lesson = state_data.get("chosen_lesson")
            url_req = f"{settings.API_URL}/edit_lesson"
            response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                    "editing_attribute": "end_time",
                                                    "editing_value": f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'})
            if response.status_code == 200:
                await msg.answer(
                    _("Время начала успешно изменено на {end_time}.").format(
                        end_time=f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'))
                chosen_lesson["end_time"] = f'{state_data["end_hour"]}:{state_data["end_minutes"]}:00'
                await state.update_data(chosen_lesson=chosen_lesson)
                await state.set_state(ShowLessonStates.showing_chosen_lesson)
                await show_chosen_lesson_menu(msg, state)
            else:
                await msg.answer(json.loads(response.text).get('detail'))


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
        case "week":
            await state.update_data(period_type="week")
            await callback_query.message.edit_text(
                _("Введите количество недель, через которые повторяется занятие."), reply_markup=None)


@router.callback_query(F.data == "not_periodicity", or_f(AddLessonStates.waiting_for_periodicity, EditLessonStates.editing_periodicity))
async def add_end_minutes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(periodicity=0)
    if await state.get_state() == AddLessonStates.waiting_for_periodicity:
        await show_lesson_confirmation(callback_query.message, state)
    elif await state.get_state() == EditLessonStates.editing_periodicity:
        state_data = await state.get_data()
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "periodicity_days",
                                                "editing_value": '0'})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Периодичность в днях успешно изменена на {days}.").format(
                    days=0))
            chosen_lesson["periodicity_days"] = 0
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(callback_query.message, state)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


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
    period_type = state_data.get("period_type")
    if period_type == "day":
        periodicity = int(periodicity)
    elif period_type == "week":
        periodicity = int(periodicity) * 7
    await state.update_data(periodicity=periodicity)

    if await state.get_state() == AddLessonStates.waiting_for_periodicity:
        await show_lesson_confirmation(message, state, bot_unit)
    elif await state.get_state() == EditLessonStates.editing_periodicity:
        state_data = await state.get_data()
        chosen_lesson = state_data.get("chosen_lesson")
        url_req = f"{settings.API_URL}/edit_lesson"
        response = requests.post(url_req, json={"lesson_id": chosen_lesson["lesson_id"],
                                                "editing_attribute": "periodicity_days",
                                                "editing_value": str(periodicity)})
        if response.status_code == 200:
            await message.answer(
                _("Периодичность в днях успешно изменена на {days}.").format(
                    days=periodicity))
            chosen_lesson["periodicity_days"] = periodicity
            await state.update_data(chosen_lesson=chosen_lesson)
            await state.set_state(ShowLessonStates.showing_chosen_lesson)
            await show_chosen_lesson_menu(message, state)
        else:
            await message.answer(json.loads(response.text).get('detail'))


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

    url_req = f"{settings.API_URL}/add_lesson"
    response = requests.post(url_req, json=lesson_data)

    if response.status_code == 200:
        await callback_query.message.answer(
            _("Занятие по дисциплине {discipline} на время {start_time} - {end_time} периодичностью {periodicity} дней добавлено.").format(
                discipline=state_data.get("discipline_name"),
                start_time=start_time[:-3],
                end_time=end_time[:-3],
                periodicity=state_data.get("periodicity")
            )
        )
        await main_bot_handler.open_lesson_menu(callback_query.message, state, state_data.get("telegram_id"))
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


@router.message(F.text == __("Посмотреть список пар"))
async def show_lesson_list(message: Message, state: FSMContext):
    await state.set_state(ShowLessonStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)
        url_req = f"{settings.API_URL}/get_lessons"
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            lessons_response = response_data
            await state.update_data(lessons_response=response_data)

            url_req = f"{settings.API_URL}/get_disciplines"
            response = requests.get(url_req, json={"user_id": user_id})

            if response.status_code == 200:
                disciplines = response.json().get("disciplines", [])
                sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
                disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
                await state.update_data(disciplines_dict=disciplines_dict)
                await state.update_data(disciplines=list(disciplines_dict.values()))
                await state.update_data(disciplines_id=list(disciplines_dict.keys()))
                filtered_lessons_list = lessons_response["lessons"]
                filtered_lessons_list.sort(key=lambda x: datetime.strptime(x["start_date"], "%Y-%m-%d"))
                await state.update_data(lessons=filtered_lessons_list)
                await message.answer(
                    _("Список занятий."),
                    reply_markup=kb.lessons_list(filtered_lessons_list, disciplines_dict, page=0)
                )
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


async def show_chosen_lesson_menu(message: Message, state: FSMContext, bot: Bot = bot_unit):
    state_data = await state.get_data()
    disciplines_dict = state_data.get("disciplines_dict")
    chosen_lesson = state_data.get("chosen_lesson")

    confirmation_text = _(
        "Вы в меню занятия по дисциплине {discipline}.\n\n"
        "Аудитория: {classroom}\n"
        "Время начала: {start_time}\n"
        "Время окончания: {end_time}\n"
        "Дата первого занятия: {start_date}\n"
        "Периодичность (дней): {periodicity}"
    ).format(
        discipline=format_value(disciplines_dict[chosen_lesson["discipline_id"]]),
        classroom=format_value(chosen_lesson["classroom"]),
        start_time=format_value(chosen_lesson["start_time"][:-3]),
        end_time=format_value(chosen_lesson["end_time"][:-3]),
        start_date=format_value(datetime.strptime(chosen_lesson["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
        periodicity=format_value(chosen_lesson["periodicity_days"])
    )

    try:
        await message.edit_text(
            confirmation_text,
            reply_markup=kb.lesson_menu()
        )
    except:
        await message.answer(
            confirmation_text,
            reply_markup=kb.lesson_menu()
        )


@router.callback_query(F.data.startswith("lesson_page_"), ShowLessonStates.showing_list)
async def handle_lab_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    lessons = state_data.get("lessons", [])
    disciplines_dict = state_data.get("disciplines_dict")

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.lessons_list(lessons, disciplines_dict, page=page)
    )


@router.callback_query(F.data.startswith("lesson_index_"))
async def show_chosen_lab_info(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
    await state.set_state(ShowLessonStates.showing_chosen_lesson)
    await callback_query.answer()
    state_data = await state.get_data()

    lesson_index = int(callback_query.data.split("_")[-1])
    lessons = state_data.get("lessons")
    chosen_lesson = next((lesson for lesson in lessons if lesson["lesson_id"] == lesson_index), None)
    await state.update_data(chosen_lesson=chosen_lesson)

    await show_chosen_lesson_menu(callback_query.message, state)


@router.callback_query(F.data == "edit_lesson")
async def edit_lesson(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    await callback_query.message.answer(
        _("Выберите информацию для изменения."),
        reply_markup=kb.lesson_edit_menu()
    )


@router.callback_query(F.data.startswith("edit_lesson_"))
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
                _("Выберите новую дисциплину для занятия."),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0))
            await state.set_state(EditLessonStates.editing_discipline)
        case "classroom":
            await callback_query.message.answer(_("Введите новую аудиторию для занятия."))
            await state.set_state(EditLessonStates.editing_classroom)
        case "start_date":
            await callback_query.message.answer(
                _("Выберите новую дату проведения первого (или единичного) занятия."),
                reply_markup=kb.calendar()
            )
            await state.set_state(EditLessonStates.editing_start_date)
        case "start_time":
            await callback_query.message.answer(
                _("Выберите час начала занятия."),
                reply_markup=kb.get_keyboard_hours()
            )
            await state.set_state(EditLessonStates.editing_start_hour)
        case "end_time":
            await callback_query.message.answer(
                _("Выберите час окончания занятия."),
                reply_markup=kb.get_keyboard_hours()
            )
            await state.set_state(EditLessonStates.editing_end_hour)
        case "periodicity":
            await callback_query.message.edit_text(_("Является ли пара периодической?"),
                                                   reply_markup=kb.is_periodicity())
            await state.set_state(EditLessonStates.editing_periodicity)

    await callback_query.answer()


@router.callback_query(F.data == "delete_lesson")
async def ask_deleting_lab(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lesson = state_data.get("chosen_lesson")
    disciplines_dict = state_data.get("disciplines_dict")

    await callback_query.message.answer(
        _("Вы действительно хотите удалить занятие по дисциплине {discipline} на дату {date} со временем проведения {time}?")
        .format(discipline=disciplines_dict[chosen_lesson["discipline_id"]],
                date=chosen_lesson["start_date"],
                time=chosen_lesson["start_time"][:-3] + " - " + chosen_lesson["end_time"][:-3]
                ),
        reply_markup=kb.confirm_delete_lesson()
    )


@router.callback_query(F.data == "confirm_deleting_lesson")
async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lesson = state_data.get("chosen_lesson")
    disciplines_dict = state_data.get("disciplines_dict")
    url_req = f"{settings.API_URL}/delete_lesson"
    response = requests.delete(url_req, json={"lesson_id": chosen_lesson["lesson_id"]})
    if response.status_code == 200:
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        await callback_query.message.answer(
            _("Занятие по дисциплине {discipline} успешно удалено.")
            .format(discipline=disciplines_dict[chosen_lesson["discipline_id"]])
        )
        await show_lesson_list(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_deleting_lesson")
async def cancel_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    chosen_lesson = state_data.get("chosen_lesson")
    disciplines_dict = state_data.get("disciplines_dict")
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.message.answer(
        _("Вы отменили удаление занятия по дисциплине {discipline}.")
        .format(discipline=disciplines_dict[chosen_lesson["discipline_id"]])
    )
    await show_chosen_lesson_menu(callback_query.message, state)


@router.callback_query(F.data == "back_to_lesson_menu")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await show_lesson_list(callback_query.message, state)


@router.callback_query(F.data == "back_to_chosen_lesson_menu")
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
    await show_chosen_lesson_menu(callback_query.message, state)
