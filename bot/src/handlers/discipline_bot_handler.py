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
        sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
        lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
        await state.update_data(lecturers_dict=lecturers_dict)
        await state.update_data(lecturers=list(lecturers_dict.values()))
        await state.update_data(lecturers_id=list(lecturers_dict.keys()))
        await message.answer(
            _("Выберите преподавателя, ведущего дисциплину.\n"),
            reply_markup=kb.lecturers_list(list(lecturers_dict.values()), page=0))
    await state.set_state(AddDisciplineStates.waiting_for_teacher)


@router.callback_query(F.data.startswith("disciplines_lecturers_page_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    lecturers = state_data.get("lecturers", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.lecturers_list(lecturers, page=page)
    )


@router.callback_query(F.data.startswith("disciplines_lecturer_index_"), or_f(AddDisciplineStates.waiting_for_teacher, AddDisciplineStates.waiting_for_new_teacher))
async def get_discipline_teacher(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    state_data = await state.get_data()
    await state.update_data(teacher_id=state_data.get("lecturers_id")[int(callback_query.data.split("_")[-1])])
    await state.update_data(teacher_name=state_data.get("lecturers")[int(callback_query.data.split("_")[-1])])
    await show_confirmation(callback_query.message, state)


@router.callback_query(F.data == "skip_disciplines_lecturer", AddDisciplineStates.waiting_for_teacher)
async def get_discipline_teacher(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(teacher_id=None)
    await show_confirmation(callback_query.message, state)


@router.callback_query(F.data == "add_discipline")
async def add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
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
async def cancel_add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
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
async def edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
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
            await callback_query.message.answer(_("Выберите другого преподавателя."),
                                                reply_markup=kb.lecturers_list(state_data.get("lecturers"), page=0))
            await state.set_state(AddDisciplineStates.waiting_for_new_teacher)

    await callback_query.answer()


@router.message(or_f(AddDisciplineStates.waiting_for_new_name, EditDisciplineStates.editing_name))
async def request_new_fio(message: Message, state: FSMContext):
    name = message.text
    if await state.get_state() == AddDisciplineStates.waiting_for_new_name:
        await state.update_data(name=name)
        await show_confirmation(message, state)
    elif await state.get_state() == EditDisciplineStates.editing_name:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        state_data = await state.get_data()
        prev_val = state_data.get("name")
        await state.update_data(editing_value=name)
        url_req = f"{settings.API_URL}/edit_discipline"
        response = requests.post(url_req, json={
            "discipline_id": state_data.get("chosen_discipline_id"),
            "editing_attribute": state_data.get("editing_attribute"),
            "editing_value": name})
        if response.status_code == 200:
            await state.update_data(chosen_discipline_name=name)
            await message.answer(
                _("Вы изменили название дисциплины {prev_val} на {val}.").format(prev_val=format_value(prev_val),
                                                                                 val=name)
            )
            menu_message = await message.answer(
                str(__("Вы в меню дисциплины {name}.\n")).format(
                    name=format_value(name),
                ),
                reply_markup=kb.discipline_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "add_discipline_by_hand")
async def add_teacher_by_hand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(is_from_api=False)
    await callback_query.message.edit_text(_("Введите название дисциплины."))
    await state.set_state(AddDisciplineStates.waiting_for_name)


@router.callback_query(F.data == "show_discipline_api_list")
async def add_teacher_by_api(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_group"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})
    if response.status_code == 200:
        group = response.json().get("group")
        url_req = "https://petrsu.egipti.com/api/v2/schedule/{group}".format(group=group)
        response = requests.get(url_req)
        if response.status_code == 200:
            response_data = response.json()

            disciplines = set()
            for day in response_data['denominator']:
                for lesson in day:
                    if 'title' in lesson:
                        disciplines.add(lesson['title'])

            for day in response_data['numerator']:
                for lesson in day:
                    if 'title' in lesson:
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
                    _("Список дисциплин:"),
                    reply_markup=kb.disciplines_list(unique_disciplines, page=0)
                )
            else:
                await callback_query.message.answer(json.loads(response.text).get('detail'))
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("disciplines_page_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    disciplines = state_data.get("disciplines", [])

    page = int(callback_query.data.split("_")[-1])
    print(page)
    print(state)
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.disciplines_list(disciplines, page=page)
    )


@router.callback_query(F.data.startswith("discipline_index_"))
async def add_teacher_by_api_phone(callback_query: CallbackQuery, state: FSMContext):
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
            await state.update_data(lecturers_dict=lecturers_dict)
            await state.update_data(lecturers=list(lecturers_dict.values()))
            await state.update_data(lecturers_id=list(lecturers_dict.keys()))
            await callback_query.message.answer(
                _("Выберите преподавателя, ведущего дисциплину.\n"),
                reply_markup=kb.lecturers_list(list(lecturers_dict.values()), page=0))
        await state.set_state(AddDisciplineStates.waiting_for_teacher)

    elif await state.get_state() == ShowDisciplineStates.showing_list:
        disciplines = state_data.get("disciplines")
        url_req = f"{settings.API_URL}/get_discipline"
        response = requests.get(url_req, json={"discipline_id": state_data.get("disciplines_id")[int(discipline_index)]})
        if response.status_code == 200:
            response_data = response.json()
            await state.update_data(chosen_discipline_id=state_data.get("disciplines_id")[int(discipline_index)])
            await state.update_data(chosen_discipline_name=response_data.get("name"))
            await state.update_data(chosen_discipline_teacher=state_data.get("lecturers_dict")[response_data.get("teacher_id")])
            menu_message = await callback_query.message.edit_text(
                str(__("Вы в меню дисциплины {name}.\n\n"
                       "Преподаватель: {teacher}\n")).format(
                    name=format_value(response_data.get("name")),
                    teacher=state_data.get("lecturers_dict")[response_data.get("teacher_id")],
                ),
                reply_markup=kb.discipline_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(F.text == __("Посмотреть список дисциплин"))
async def add_teacher_start(message: Message, state: FSMContext):
    await state.set_state(ShowDisciplineStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        url_req = f"{settings.API_URL}/get_disciplines"
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            print(response_data)
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


# @router.callback_query(F.data == "edit_teacher")
# async def edit_teacher(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     await callback_query.message.bot.edit_message_reply_markup(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#         reply_markup=None
#     )
#     state_data = await state.get_data()
#     url_req = f"{settings.API_URL}/get_teacher_api_status"
#     response = requests.get(url_req, json={"teacher_id": state_data.get("chosen_lecturer_id")})
#     if response.status_code == 200:
#         response_data = response.json()
#         api_status = response_data.get("is_from_API")
#         await state.update_data(chosen_teacher_api_status=api_status)
#         await callback_query.message.answer(
#             _("Выберите изменения"),
#             reply_markup=kb.edit_options(api_status)
#         )
#     else:
#         await callback_query.message.answer(json.loads(response.text).get('detail'))
#
#
# @router.callback_query(F.data.startswith("edit_teacher_"))
# async def edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#     )
#     field = callback_query.data.split("_")[-1]
#
#     match field:
#         case "fio":
#             await state.update_data(editing_attribute="name")
#             await callback_query.message.answer(_("Введите новые ФИО преподавателя."),
#                                                 reply_markup=kb.cancel_editing_attr())
#             await state.set_state(EditTeacherStates.editing_fio)
#         case "phone":
#             await state.update_data(editing_attribute="phone_number")
#             await callback_query.message.answer(_("Введите новый номер телефона преподавателя."),
#                                                 reply_markup=kb.cancel_editing_attr())
#             await state.set_state(EditTeacherStates.editing_phone_number)
#         case "email":
#             await state.update_data(editing_attribute="email")
#             await callback_query.message.answer(_("Введите новый адрес электронной почты преподавателя."),
#                                                 reply_markup=kb.cancel_editing_attr())
#             await state.set_state(EditTeacherStates.editing_email)
#         case "link":
#             await state.update_data(editing_attribute="social_page_link")
#             await callback_query.message.answer(_("Введите новую ссылку на социальную сеть преподавателя."),
#                                                 reply_markup=kb.cancel_editing_attr())
#             await state.set_state(EditTeacherStates.editing_link)
#         case "classroom":
#             await state.update_data(editing_attribute="classroom")
#             await callback_query.message.answer(
#                 _("Введите новый номер аудитории или кафедры, где можно найти преподавателя."),
#                 reply_markup=kb.cancel_editing_attr())
#             await state.set_state(EditTeacherStates.editing_classroom)
#
#     await callback_query.answer()
#
#
# @router.callback_query(F.data == "cancel_editing")
# async def cancel_edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#     )
#     await callback_query.message.bot.edit_message_reply_markup(
#         chat_id=callback_query.message.chat.id,
#         message_id=state_data.get("menu_message_id"),
#         reply_markup=kb.teacher_menu()
#     )
#
#
# @router.callback_query(F.data == "cancel_editing_attr")
# async def cancel_edit_teacher_data_attr(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#     )
#     if state_data.get("validation_status"):
#         menu_message = await callback_query.message.answer(
#             str(__("Вы в меню преподавателя {name}.\n\n"
#                    "Номер телефона: {phone_number}\n"
#                    "Почта: {email}\n"
#                    "Социальная сеть: {social_page_link}\n"
#                    "Аудитория: {classroom}")).format(
#                 name=format_value(state_data.get("chosen_lecturer_name")),
#                 phone_number=format_value(state_data.get("chosen_lecturer_phone")),
#                 email=format_value(state_data.get("chosen_lecturer_email")),
#                 social_page_link=format_value(state_data.get("chosen_lecturer_link")),
#                 classroom=format_value(state_data.get("chosen_lecturer_classroom")),
#             ),
#             reply_markup=kb.teacher_menu()
#         )
#         await state.update_data(menu_message_id=menu_message.message_id)
#     else:
#         await callback_query.message.answer(
#             _("Выберите изменения"),
#             reply_markup=kb.edit_options(state_data.get("chosen_teacher_api_status"))
#         )
#
#
# @router.callback_query(F.data == "delete_teacher")
# async def ask_deleting_teacher(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     await callback_query.message.bot.edit_message_reply_markup(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#         reply_markup=None
#     )
#     state_data = await state.get_data()
#     await callback_query.message.answer(
#         _("Вы действительно хотите удалить преподавателя {name}?").format(name=state_data.get("chosen_lecturer_name")),
#         reply_markup=kb.confirm_delete_teacher()
#     )
#
#
# @router.callback_query(F.data == "confirm_deleting")
# async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     url_req = f"{settings.API_URL}/delete_teacher"
#     response = requests.delete(url_req, json={"teacher_id": state_data.get("chosen_lecturer_id")})
#     if response.status_code == 200:
#         await callback_query.message.bot.delete_message(
#             chat_id=callback_query.message.chat.id,
#             message_id=callback_query.message.message_id,
#         )
#         await callback_query.message.answer(
#             _("Преподаватель {name} успешно удален.").format(name=state_data.get("chosen_lecturer_name"))
#         )
#         await add_teacher_start(callback_query.message, state)
#     else:
#         await callback_query.message.answer(json.loads(response.text).get('detail'))
#
#
# @router.callback_query(F.data == "cancel_deleting")
# async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     state_data = await state.get_data()
#     await callback_query.message.bot.edit_message_reply_markup(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#         reply_markup=None
#     )
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=state_data.get("menu_message_id"),
#     )
#     await callback_query.message.answer(
#         _("Вы отменили удаление преподавателя {name}.").format(name=state_data.get("chosen_lecturer_name"))
#     )
#     menu_message = await callback_query.message.answer(
#         str(__("Вы в меню преподавателя {name}.\n\n"
#                "Номер телефона: {phone_number}\n"
#                "Почта: {email}\n"
#                "Социальная сеть: {social_page_link}\n"
#                "Аудитория: {classroom}")).format(
#             name=format_value(state_data.get("name")),
#             phone_number=format_value(state_data.get("phone_number")),
#             email=format_value(state_data.get("email")),
#             social_page_link=format_value(state_data.get("social_page_link")),
#             classroom=format_value(state_data.get("classroom")),
#         ),
#         reply_markup=kb.teacher_menu()
#     )
#     await state.update_data(menu_message_id=menu_message.message_id)
#
#
# @router.callback_query(F.data == "back_to_list")
# async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#     await callback_query.message.bot.delete_message(
#         chat_id=callback_query.message.chat.id,
#         message_id=callback_query.message.message_id,
#     )
#     await add_teacher_start(callback_query.message, state)
