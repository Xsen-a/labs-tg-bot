import re
import json
import requests

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.discipline_keyboard as kb
from ..settings import settings

router = Router()


def format_value(value):
    return "-" if value is None else value


class AddDisciplineStates(StatesGroup):
    adding_discipline = State()
    waiting_for_name = State()
    waiting_for_new_name = State()
    waiting_for_teacher = State()
    waiting_for_new_teacher = State()


class ShowDisciplineStates(StatesGroup):
    showing_list = State()


class EditDisciplineStates(StatesGroup):
    editing_discipline = State()
    editing_name = State()
    editing_teacher = State()


async def show_confirmation(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if await state.get_state() != AddDisciplineStates.waiting_for_new_name:
        if state_data.get("teacher_name"):
            await message.edit_text(
                _("Вы действительно хотите добавить дисциплину {name}?\n\n"
                  "Преподаватель: {teacher}")
                .format(
                    name=format_value(state_data.get("name")),
                    teacher=state_data.get("teacher_name")
                ),
                reply_markup=kb.add_discipline_confirm(state_data.get("is_from_api")))
        else:
            await message.edit_text(
                _("Вы действительно хотите добавить дисциплину {name}?\n\n"
                  "Преподаватель: -")
                .format(
                    name=format_value(state_data.get("name"))
                ),
                reply_markup=kb.add_discipline_confirm(state_data.get("is_from_api")))
    else:
        if state_data.get("teacher_name"):
            await message.answer(
                _("Вы действительно хотите добавить дисциплину {name}?\n\n"
                  "Преподаватель: {teacher}")
                .format(
                    name=format_value(state_data.get("name")),
                    teacher=state_data.get("teacher_name")
                ),
                reply_markup=kb.add_discipline_confirm(state_data.get("is_from_api")))
        else:
            await message.answer(
                _("Вы действительно хотите добавить дисциплину {name}?\n\n"
                  "Преподаватель: -")
                .format(
                    name=format_value(state_data.get("name"))
                ),
                reply_markup=kb.add_discipline_confirm(state_data.get("is_from_api")))


@router.message(F.text == __("Добавить дисциплину"))
async def add_discipline_start(message: Message, state: FSMContext):
    await state.set_state(AddDisciplineStates.adding_discipline)
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})
    if response.status_code == 200:
        await state.update_data(user_id=response.json().get("user_id"))

        url_req = f"{settings.API_URL}/check_is_petrsu_student"
        response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

        if response.status_code == 200:
            if response.json().get("is_petrsu_student", True):
                await message.answer(_("Выбрать дисциплину из расписания или добавить вручную?"),
                                     reply_markup=kb.add_option())
            else:
                await state.update_data(is_from_api=False)
                await message.answer(_("Введите название дисциплины."))
                await state.set_state(AddDisciplineStates.waiting_for_name)
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.message(AddDisciplineStates.waiting_for_name)
async def add_discipline_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_teachers"
    response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
    if response.status_code == 200:
        response_data = response.json()
        if len(response_data.get("teachers")) == 0:
            await message.answer(
                _("Выберите преподавателя, ведущего дисциплину.\n\nПреподавателей не найдено. Пожалуйста, если необходимо, добавьте преподавателя в меню преподавателей."),
                reply_markup=kb.lecturers_list([], page=0,
                                               state=str(await state.get_state())))
        else:
            sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
            lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
            await state.update_data(lecturers_dict=lecturers_dict)
            await state.update_data(lecturers=list(lecturers_dict.values()))
            await state.update_data(lecturers_id=list(lecturers_dict.keys()))
            await message.answer(
                _("Выберите преподавателя, ведущего дисциплину.\n"),
                reply_markup=kb.lecturers_list(list(lecturers_dict.values()), page=0, state=str(await state.get_state())))
    await state.set_state(AddDisciplineStates.waiting_for_teacher)


@router.callback_query(F.data.startswith("disciplines_lecturers_page_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    lecturers = state_data.get("lecturers", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.lecturers_list(lecturers, page=page, state=str(await state.get_state()))
    )


@router.callback_query(F.data.startswith("disciplines_lecturer_index_"),
                       or_f(AddDisciplineStates.waiting_for_teacher, AddDisciplineStates.waiting_for_new_teacher, EditDisciplineStates.editing_teacher))
async def get_discipline_teacher(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state.update_data(teacher_id=state_data.get("lecturers_id")[int(callback_query.data.split("_")[-1])])
    await state.update_data(teacher_name=state_data.get("lecturers")[int(callback_query.data.split("_")[-1])])
    if await state.get_state() in [AddDisciplineStates.waiting_for_teacher,  AddDisciplineStates.waiting_for_new_teacher]:
        await show_confirmation(callback_query.message, state)
    else:
        await state.set_state(EditDisciplineStates.editing_teacher)
        await callback_query.message.bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None
        )
        state_data = await state.get_data()
        await state.update_data(editing_value=state_data.get("teacher_id"))
        url_req = f"{settings.API_URL}/edit_discipline"
        response = requests.post(url_req, json={
            "discipline_id": state_data.get("chosen_discipline_id"),
            "editing_attribute": "teacher_id",
            "editing_value": str(state_data.get("teacher_id"))})
        if response.status_code == 200:
            await state.update_data(chosen_teacher_name=state_data.get("teacher_name"))
            await callback_query.message.edit_text(
                str(__("Преподаватель успешно изменен на {teacher_name}").format(
                    teacher_name=format_value(state_data.get("teacher_name")),
                )))
            menu_message = await callback_query.message.answer(
                str(__("Вы в меню дисциплины {name}.\n\n"
                       "Преподаватель: {teacher}\n")).format(
                    name=format_value(state_data.get("chosen_discipline_name")),
                    teacher=format_value(state_data.get("teacher_name")),
                ),
                reply_markup=kb.discipline_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "skip_disciplines_lecturer",
                       or_f(AddDisciplineStates.waiting_for_teacher, AddDisciplineStates.waiting_for_new_teacher))
async def skip_discipline_teacher(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(teacher_id=None)
    await state.update_data(teacher_name=None)
    await show_confirmation(callback_query.message, state)


@router.callback_query(F.data == "add_discipline")
async def add_discipline_end(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/add_discipline"
    response = requests.post(url_req, json={"user_id": state_data.get("user_id"),
                                            "teacher_id": state_data.get("teacher_id"),
                                            "name": state_data.get("name"),
                                            "is_from_API": state_data.get("is_from_api")})
    if response.status_code == 200:
        await callback_query.message.edit_text(
            str(__("Дисциплина {name} добавлена.\n\n"
                   "Преподаватель: {teacher_name}").format(
                name=format_value(state_data.get("name")),
                teacher_name=format_value(state_data.get("teacher_name")),
            )))
        await main_bot_handler.open_discipline_menu(callback_query.message, state, state_data.get("telegram_id"))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_add_discipline")
async def cancel_add_discipline_end(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.answer(_("Вы отменили добавление дисциплины."))
    await main_bot_handler.open_discipline_menu(callback_query.message, state, state_data.get("telegram_id"))


@router.callback_query(F.data.startswith("change_discipline_"))
async def edit_discipline_data(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    field = callback_query.data.split("_")[-1]
    await state.update_data(editing_attribute=field)

    match field:
        case "name":
            await callback_query.message.answer(_("Введите новое название дисциплины."))
            await state.set_state(AddDisciplineStates.waiting_for_new_name)
        case "teacher":
            url_req = f"{settings.API_URL}/get_teachers"
            response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
            if response.status_code == 200:
                response_data = response.json()
                sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
                lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
                await state.update_data(lecturers_dict=lecturers_dict)
                await state.update_data(lecturers=list(lecturers_dict.values()))
                await state.update_data(lecturers_id=list(lecturers_dict.keys()))
                if state_data.get("is_from_api"):
                    schedule_data = state_data.get("schedule_data")
                    api_lecturers = set()
                    for day in schedule_data['denominator']:
                        for lesson in day:
                            if lesson['title'] == state_data.get("name"):
                                api_lecturers.add(lesson['lecturer'])

                    for day in schedule_data['numerator']:
                        for lesson in day:
                            if lesson['title'] == state_data.get("name"):
                                api_lecturers.add(lesson['lecturer'])
                    available_lecturers = [lecturer for lecturer in list(lecturers_dict.values()) if
                                           lecturer in api_lecturers]
                    available_lecturers_full = {
                        teacher_id: name for teacher_id, name in lecturers_dict.items()
                        if name in api_lecturers
                    }
                    await state.update_data(lecturers_dict=available_lecturers_full)
                    await state.update_data(lecturers=available_lecturers)
                    await state.update_data(lecturers_id=list(available_lecturers_full.keys()))
                    await callback_query.message.answer(
                        _("Выберите преподавателя, ведущего дисциплину."),
                        reply_markup=kb.lecturers_list(available_lecturers, page=0, state=str(await state.get_state())))
                    await state.set_state(AddDisciplineStates.waiting_for_new_teacher)
                else:
                    await callback_query.message.answer(
                        _("Выберите преподавателя, ведущего дисциплину."),
                        reply_markup=kb.lecturers_list(list(lecturers_dict.values()), page=0, state=str(await state.get_state())))
                await state.set_state(AddDisciplineStates.waiting_for_new_teacher)
            else:
                await callback_query.message.answer(json.loads(response.text).get('detail'))
    await callback_query.answer()


@router.message(or_f(AddDisciplineStates.waiting_for_new_name, EditDisciplineStates.editing_name))
async def request_new_name(message: Message, state: FSMContext):
    name = message.text
    if await state.get_state() == AddDisciplineStates.waiting_for_new_name:
        await state.update_data(name=name)
        await show_confirmation(message, state)
    elif await state.get_state() == EditDisciplineStates.editing_name:
        state_data = await state.get_data()
        prev_val = state_data.get("name")
        await state.update_data(editing_value=name)
        url_req = f"{settings.API_URL}/edit_discipline"
        response = requests.post(url_req, json={
            "discipline_id": state_data.get("chosen_discipline_id"),
            "editing_attribute": "name",
            "editing_value": name})
        if response.status_code == 200:
            await state.update_data(chosen_discipline_name=name)
            await message.answer(
                _("Вы изменили название дисциплины {prev_val} на {val}.").format(prev_val=format_value(prev_val),
                                                                                 val=name)
            )
            menu_message = await message.answer(
                str(__("Вы в меню дисциплины {name}.\n\n"
                       "Преподаватель: {teacher}\n")).format(
                    name=format_value(name),
                    teacher=format_value(state_data.get("chosen_discipline_teacher")),
                ),
                reply_markup=kb.discipline_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "add_discipline_by_hand")
async def add_discopline_by_hand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(is_from_api=False)
    await callback_query.message.edit_text(_("Введите название дисциплины."))
    await state.set_state(AddDisciplineStates.waiting_for_name)


@router.callback_query(F.data == "show_discipline_api_list")
async def show_discipline_api_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    state_data = await state.get_data()
    schedule_data = state_data.get("schedule_data")
    disciplines = set()
    for day in schedule_data['denominator']:
        for lesson in day:
            disciplines.add(lesson['title'])

    for day in schedule_data['numerator']:
        for lesson in day:
            disciplines.add(lesson['title'])

    disciplines_list = sorted(disciplines)

    url_req = f"{settings.API_URL}/get_disciplines"
    response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
    if response.status_code == 200:
        response_data = response.json()
        disciplines_names = {discipline["name"] for discipline in response_data.get("disciplines", [])}
        unique_disciplines = [discipline for discipline in disciplines_list if discipline not in disciplines_names]
        await state.update_data(disciplines=unique_disciplines)
        await callback_query.message.edit_text(
            _("Список дисциплин"),
            reply_markup=kb.disciplines_list(unique_disciplines, page=0)
        )
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("disciplines_page_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    disciplines = state_data.get("disciplines", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.disciplines_list(disciplines, page=page)
    )


@router.callback_query(F.data.startswith("discipline_index_"))
async def add_discipline_by_api_phone(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    disciplines = state_data.get("disciplines", [])

    discipline_index = int(callback_query.data.split("_")[-1])
    selected_discipline = disciplines[discipline_index]

    await state.update_data(name=selected_discipline)
    await state.update_data(is_from_api=True)

    if await state.get_state() != ShowDisciplineStates.showing_list:
        url_req = f"{settings.API_URL}/get_teachers"
        response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
        if response.status_code == 200:
            response_data = response.json()
            sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
            lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
            schedule_data = state_data.get("schedule_data")
            api_lecturers = set()
            for day in schedule_data['denominator']:
                for lesson in day:
                    if lesson['title'] == selected_discipline:
                        api_lecturers.add(lesson['lecturer'])

            for day in schedule_data['numerator']:
                for lesson in day:
                    if lesson['title'] == selected_discipline:
                        api_lecturers.add(lesson['lecturer'])
            available_lecturers = [lecturer for lecturer in list(lecturers_dict.values()) if lecturer in api_lecturers]
            available_lecturers_full = {
                teacher_id: name for teacher_id, name in lecturers_dict.items()
                if name in api_lecturers
            }
            await state.update_data(lecturers_dict=available_lecturers_full)
            await state.update_data(lecturers=available_lecturers)
            await state.update_data(lecturers_id=list(available_lecturers_full.keys()))
            await callback_query.message.edit_text(
                _("Выберите преподавателя, ведущего дисциплину.\n"),
                reply_markup=kb.lecturers_list(available_lecturers, page=0, state=str(await state.get_state())))
        await state.set_state(AddDisciplineStates.waiting_for_teacher)

    elif await state.get_state() == ShowDisciplineStates.showing_list:
        url_req = f"{settings.API_URL}/get_discipline"
        response = requests.get(url_req,
                                json={"discipline_id": state_data.get("disciplines_id")[int(discipline_index)]})
        if response.status_code == 200:
            discipline_data = response.json()
            await state.update_data(chosen_discipline_id=state_data.get("disciplines_id")[int(discipline_index)])
            await state.update_data(chosen_discipline_name=discipline_data.get("name"))
            url_req = f"{settings.API_URL}/get_teacher_name"
            if discipline_data.get("teacher_id") is not None:
                response = requests.get(url_req,
                                        json={"teacher_id": discipline_data.get("teacher_id")})
                if response.status_code == 200:
                    teacher_data = response.json()
                    await state.update_data(chosen_discipline_teacher=teacher_data.get("name"))
                    menu_message = await callback_query.message.edit_text(
                        str(__("Вы в меню дисциплины {name}.\n\n"
                               "Преподаватель: {teacher}\n")).format(
                            name=format_value(discipline_data.get("name")),
                            teacher=teacher_data.get("name"),
                        ),
                        reply_markup=kb.discipline_menu()
                    )
                    await state.update_data(menu_message_id=menu_message.message_id)
                else:
                    await callback_query.message.answer(json.loads(response.text).get('detail'))
            else:
                await state.update_data(chosen_discipline_teacher=None)
                menu_message = await callback_query.message.edit_text(
                    str(__("Вы в меню дисциплины {name}.\n\n"
                           "Преподаватель: {teacher}\n")).format(
                        name=format_value(discipline_data.get("name")),
                        teacher="-",
                    ),
                    reply_markup=kb.discipline_menu()
                )
                await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(F.text == __("Посмотреть список дисциплин"))
async def show_discipline_list(message: Message, state: FSMContext):
    await state.set_state(ShowDisciplineStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)
        url_req = f"{settings.API_URL}/get_disciplines"
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            sorted_disciplines = sorted(response_data.get("disciplines"), key=lambda x: x["name"])
            disciplines_dict = {discipline["discipline_id"]: discipline["name"] for discipline in sorted_disciplines}
            await state.update_data(disciplines_dict=disciplines_dict)
            await state.update_data(disciplines=list(disciplines_dict.values()))
            await state.update_data(disciplines_id=list(disciplines_dict.keys()))
            await message.answer(
                _("Список дисциплин"),
                reply_markup=kb.disciplines_list(list(disciplines_dict.values()), page=0)
            )
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "edit_discipline")
async def edit_discipline(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_discipline_api_status"
    response = requests.get(url_req, json={"discipline_id": state_data.get("chosen_discipline_id")})
    if response.status_code == 200:
        response_data = response.json()
        api_status = response_data.get("is_from_API")
        await state.update_data(chosen_discipline_api_status=api_status)
        if state_data.get("chosen_discipline_teacher") is None:
            exists_teacher = False
            await state.update_data(exists_teacher=False)
        else:
            exists_teacher = True
            await state.update_data(exists_teacher=True)
        await callback_query.message.answer(
            _("Выберите изменения"),
            reply_markup=kb.edit_options(exists_teacher, api_status)
        )
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("edit_discipline_"))
async def edit_discipline_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    field = callback_query.data.split("_")[-1]

    state_data = await state.get_data()
    match field:
        case "name":
            await callback_query.message.answer(_("Введите новое название дисциплины."),
                                                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditDisciplineStates.editing_name)
        case "teacher":
            url_req = f"{settings.API_URL}/get_teachers"
            response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
            await state.set_state(EditDisciplineStates.editing_teacher)
            if response.status_code == 200:
                response_data = response.json()
                sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
                lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
                await state.update_data(lecturers_dict=lecturers_dict)
                await state.update_data(lecturers=list(lecturers_dict.values()))
                await state.update_data(lecturers_id=list(lecturers_dict.keys()))

                if state_data.get("chosen_discipline_api_status"):
                    schedule_data = state_data.get("schedule_data")
                    api_lecturers = set()
                    for day in schedule_data['denominator']:
                        for lesson in day:
                            if lesson['title'] == state_data.get("name"):
                                api_lecturers.add(lesson['lecturer'])

                    for day in schedule_data['numerator']:
                        for lesson in day:
                            if lesson['title'] == state_data.get("name"):
                                api_lecturers.add(lesson['lecturer'])
                    available_lecturers = [lecturer for lecturer in list(lecturers_dict.values()) if
                                           lecturer in api_lecturers]
                    available_lecturers_full = {
                        teacher_id: name for teacher_id, name in lecturers_dict.items()
                        if name in api_lecturers
                    }
                    await state.update_data(lecturers_dict=available_lecturers_full)
                    await state.update_data(lecturers=available_lecturers)
                    await state.update_data(lecturers_id=list(available_lecturers_full.keys()))
                    await state.set_state(EditDisciplineStates.editing_teacher)
                    await callback_query.message.answer(
                        _("Выберите другого преподавателя, ведущего дисциплину."),
                        reply_markup=kb.lecturers_list(available_lecturers, page=0, state=str(await state.get_state())))
                else:
                    await state.set_state(EditDisciplineStates.editing_teacher)
                    await callback_query.message.answer(
                        _("Выберите другого преподавателя, ведущего дисциплину."),
                        reply_markup=kb.lecturers_list(list(lecturers_dict.values()),
                                                       page=0, state=str(await state.get_state())))
            else:
                await callback_query.message.answer(json.loads(response.text).get('detail'))

    await callback_query.answer()


@router.callback_query(F.data == "cancel_editing_discipline")
async def cancel_edit_discipline_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=state_data.get("menu_message_id"),
        reply_markup=kb.discipline_menu()
    )


@router.callback_query(F.data == "cancel_editing_attr_discipline")
async def cancel_edit_discipline_data_attr(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    if state_data.get("validation_status"):
        menu_message = await callback_query.message.edit_text(
            str(__("Вы в меню дисциплины {name}.\n\n"
                   "Преподаватель: {teacher}\n")).format(
                name=format_value(state_data.get("chosen_discipline_name")),
                teacher=format_value(state_data.get("chosen_discipline_teacher")),
            ),
            reply_markup=kb.discipline_menu()
        )
        await state.update_data(menu_message_id=menu_message.message_id)
    else:
        await callback_query.message.answer(
            _("Выберите изменения"),
            reply_markup=kb.edit_options(state_data.get("exists_teacher"),
                                         state_data.get("chosen_discipline_api_status"))
        )


@router.callback_query(F.data == "delete_discipline")
async def ask_deleting_discipline(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    state_data = await state.get_data()
    await callback_query.message.answer(
        _("Вы действительно хотите удалить дисциплину {name}?").format(name=state_data.get("chosen_discipline_name")),
        reply_markup=kb.confirm_delete_discipline()
    )


@router.callback_query(F.data == "confirm_deleting_discipline")
async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/delete_discipline"
    response = requests.delete(url_req, json={"discipline_id": state_data.get("chosen_discipline_id")})
    if response.status_code == 200:
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        await callback_query.message.answer(
            _("Дисциплина {name} успешно удалена.").format(name=state_data.get("chosen_discipline_name"))
        )
        await show_discipline_list(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_deleting_discipline")
async def cancel_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=state_data.get("menu_message_id"),
    )
    await callback_query.message.answer(
        _("Вы отменили удаление дисциплины {name}.").format(name=state_data.get("chosen_discipline_name"))
    )
    menu_message = await callback_query.message.answer(
        str(__("Вы в меню дисциплины {name}.\n\n"
               "Преподаватель: {teacher}\n")).format(
            name=format_value(state_data.get("chosen_discipline_name")),
            teacher=format_value(state_data.get("chosen_discipline_teacher")),
        ),
        reply_markup=kb.discipline_menu()
    )
    await state.update_data(menu_message_id=menu_message.message_id)


@router.callback_query(F.data == "back_to_discipline_list")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await show_discipline_list(callback_query.message, state)
