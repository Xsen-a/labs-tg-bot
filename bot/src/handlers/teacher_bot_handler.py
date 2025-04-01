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
import bot.src.keyboards.teacher_keyboard as kb
from ..settings import settings

router = Router()


class AddTeacherStates(StatesGroup):
    adding_teacher = State()
    waiting_for_FIO = State()
    waiting_for_phone_number = State()
    waiting_for_email = State()
    waiting_for_link = State()
    waiting_for_classroom = State()
    waiting_for_new_fio = State()
    waiting_for_new_phone_number = State()
    waiting_for_new_email = State()
    waiting_for_new_link = State()
    waiting_for_new_classroom = State()


class ShowTeacherStates(StatesGroup):
    showing_list = State()


class EditTeacherStates(StatesGroup):
    editing_teacher = State()
    editing_fio = State()
    editing_phone_number = State()
    editing_email = State()
    editing_link = State()
    editing_classroom = State()


def validate_fio(fio):
    pattern = r"([А-ЯЁ][а-яё-]+\s){1,2}([А-ЯЁ][а-яё-]+)"
    if re.match(pattern, fio):
        return True
    else:
        return False


def validate_phone_number(phone_number):
    pattern = r"^\+7\d{10}$"
    if re.match(pattern, phone_number):
        return True
    else:
        return False


def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, email):
        return True
    else:
        return False


def format_value(value):
    return "-" if value is None else value


async def show_confirmation(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await message.answer(
        _("Вы действительно хотите добавить преподавателя {name}?\n\n"
          "Номер телефона: {phone_number}\n"
          "Почта: {email}\n"
          "Социальная сеть: {social_page_link}\n"
          "Аудитория: {classroom}\n")
        .format(
            name=format_value(state_data.get("name")),
            phone_number=format_value(state_data.get("phone_number")),
            email=format_value(state_data.get("email")),
            social_page_link=format_value(state_data.get("social_page_link")),
            classroom=format_value(state_data.get("classroom")),
        ),
        reply_markup=kb.add_teacher_confirm(state_data.get("is_from_api")),
    )


@router.message(F.text == __("Добавить преподавателя"))
async def add_teacher_start(message: Message, state: FSMContext):
    await state.set_state(AddTeacherStates.adding_teacher)
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})
    if response.status_code == 200:
        await state.update_data(user_id=response.json().get("user_id"))

        url_req = f"{settings.API_URL}/check_is_petrsu_student"
        response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

        if response.status_code == 200:
            if response.json().get("is_petrsu_student", True):
                await message.answer(_("Выбрать преподавателя из списка или добавить вручную?"),
                                     reply_markup=kb.add_option())
            else:
                await state.update_data(is_from_api=False)
                await message.answer(_("Введите ФИО преподавателя."))
                await state.set_state(AddTeacherStates.waiting_for_FIO)
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.message(AddTeacherStates.waiting_for_FIO)
async def add_teacher_fio(message: Message, state: FSMContext):
    fio = message.text
    if not validate_fio(fio):
        await message.answer(
            _("Неверный формат ФИО. Введите, пожалуйста, в формате Фамилия Имя Отчество (если имеется).")
        )
        return
    else:
        await state.update_data(name=fio)
        await message.answer(
            _("Введите номер телефона преподавателя в формате +79999999999."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddTeacherStates.waiting_for_phone_number)


@router.message(AddTeacherStates.waiting_for_phone_number)
async def add_teacher_phone_number(message: Message, state: FSMContext):
    phone_number = message.text
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None
    )
    if not validate_phone_number(phone_number):
        await message.answer(
            _("Неверный формат номера телефона. Пожалуйста, введите номер в формате +79999999999."),
            reply_markup=kb.skip_button()
        )
        return
    else:
        await state.update_data(phone_number=phone_number)
        await message.answer(
            _("Введите почту преподавателя в формате name@mail.ru."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddTeacherStates.waiting_for_email)


@router.callback_query(F.data == "skip", AddTeacherStates.waiting_for_phone_number)
async def skip_phone_number(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(phone_number=None)
    await callback_query.message.edit_text(
        _("Введите почту преподавателя в формате name@mail.ru."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_email)


@router.message(AddTeacherStates.waiting_for_email)
async def add_teacher_email(message: Message, state: FSMContext):
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None
    )
    email = message.text
    if not validate_email(email):
        await message.answer(
            _("Неверный формат почты. Введите, пожалуйста, в формате name@mail.ru."),
            reply_markup=kb.skip_button()
        )
        return
    else:
        await state.update_data(email=email)
        await message.answer(
            _("Введите ссылку на социальную сеть преподавателя."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddTeacherStates.waiting_for_link)


@router.callback_query(F.data == "skip", AddTeacherStates.waiting_for_email)
async def skip_email(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(email=None)
    await callback_query.message.edit_text(
        _("Введите ссылку на социальную сеть преподавателя."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_link)


@router.message(AddTeacherStates.waiting_for_link)
async def add_teacher_link(message: Message, state: FSMContext):
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None
    )
    social_page_link = message.text
    await state.update_data(social_page_link=social_page_link)
    await message.answer(
        _("Введите номер аудитории или кафедры, где можно найти преподавателя."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_classroom)


@router.callback_query(F.data == "skip", AddTeacherStates.waiting_for_link)
async def skip_link(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(social_page_link=None)
    await callback_query.message.edit_text(
        _("Введите номер аудитории или кафедры, где можно найти преподавателя."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_classroom)


@router.message(AddTeacherStates.waiting_for_classroom)
async def add_teacher_classroom(message: Message, state: FSMContext):
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None
    )
    classroom = message.text
    await state.update_data(classroom=classroom)
    await show_confirmation(message, state)


@router.callback_query(F.data == "skip", AddTeacherStates.waiting_for_classroom)
async def skip_classroom(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await callback_query.answer()
    await state.update_data(classroom=None)
    await show_confirmation(callback_query.message, state)


@router.callback_query(F.data == "add_teacher")
async def add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/add_teacher"
    response = requests.post(url_req, json={"user_id": state_data.get("user_id"),
                                            "name": state_data.get("name"),
                                            "phone_number": state_data.get("phone_number"),
                                            "email": state_data.get("email"),
                                            "social_page_link": state_data.get("social_page_link"),
                                            "classroom": state_data.get("classroom"),
                                            "is_from_API": state_data.get("is_from_api")})
    if response.status_code == 200:
        await callback_query.message.edit_text(
            str(__("Преподаватель {name} добавлен.\n\n"
                   "Номер телефона: {phone_number}\n"
                   "Почта: {email}\n"
                   "Социальная сеть: {social_page_link}\n"
                   "Аудитория: {classroom}")).format(
                name=format_value(state_data.get("name")),
                phone_number=format_value(state_data.get("phone_number")),
                email=format_value(state_data.get("email")),
                social_page_link=format_value(state_data.get("social_page_link")),
                classroom=format_value(state_data.get("classroom")),
            )
        )
        await main_bot_handler.open_teacher_menu(callback_query.message, state, state_data.get("telegram_id"))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_add_teacher")
async def cancel_add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.answer(_("Вы отменили добавление преподавателя."))
    await main_bot_handler.open_teacher_menu(callback_query.message, state, state_data.get("telegram_id"))


@router.callback_query(F.data.startswith("change_teacher_"))
async def edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    field = callback_query.data.split("_")[-1]
    await state.update_data(editing_attribute=field)

    match field:
        case "fio":
            await callback_query.message.answer(_("Введите новые ФИО преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_fio)
        case "phone":
            await callback_query.message.answer(_("Введите новый номер телефона преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_phone_number)
        case "email":
            await callback_query.message.answer(_("Введите новый адрес электронной почты преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_email)
        case "link":
            await callback_query.message.answer(_("Введите новую ссылку на социальную сеть преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_link)
        case "classroom":
            await callback_query.message.answer(
                _("Введите новый номер аудитории или кафедры, где можно найти преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_classroom)

    await callback_query.answer()


@router.message(or_f(AddTeacherStates.waiting_for_new_fio, EditTeacherStates.editing_fio))
async def request_new_fio(message: Message, state: FSMContext):
    fio = message.text
    if not validate_fio(fio):
        await state.update_data(validation_status=True)
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        await message.answer(
            _("Неверный формат ФИО. Введите, пожалуйста, в формате Фамилия Имя Отчество (если имеется)."),
            reply_markup=kb.cancel_editing_attr()
        )
        return
    else:
        if await state.get_state() == AddTeacherStates.waiting_for_new_fio:
            await state.update_data(name=fio)
            await show_confirmation(message, state)
        elif await state.get_state() == EditTeacherStates.editing_fio:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id - 1,
                reply_markup=None
            )
            state_data = await state.get_data()
            prev_val = state_data.get("name")
            await state.update_data(editing_value=fio)
            url_req = f"{settings.API_URL}/edit_teacher"
            response = requests.post(url_req, json={
                "teacher_id": state_data.get("chosen_lecturer_id"),
                "editing_attribute": state_data.get("editing_attribute"),
                "editing_value": fio})
            if response.status_code == 200:
                await state.update_data(chosen_lecturer_name=fio)
                await message.answer(
                    _("Вы изменили ФИО преподавателя {prev_val} на {val}.").format(prev_val=format_value(prev_val),
                                                                                   val=fio)
                )
                menu_message = await message.answer(
                    str(__("Вы в меню преподавателя {name}.\n\n"
                           "Номер телефона: {phone_number}\n"
                           "Почта: {email}\n"
                           "Социальная сеть: {social_page_link}\n"
                           "Аудитория: {classroom}")).format(
                        name=format_value(fio),
                        phone_number=format_value(state_data.get("chosen_lecturer_phone")),
                        email=format_value(state_data.get("chosen_lecturer_email")),
                        social_page_link=format_value(state_data.get("chosen_lecturer_link")),
                        classroom=format_value(state_data.get("chosen_lecturer_classroom")),
                    ),
                    reply_markup=kb.teacher_menu()
                )
                await state.update_data(menu_message_id=menu_message.message_id)
            else:
                await message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddTeacherStates.waiting_for_new_phone_number, EditTeacherStates.editing_phone_number))
async def request_new_phone_number(message: Message, state: FSMContext):
    phone_number = message.text
    if not validate_phone_number(phone_number):
        await state.update_data(validation_status=True)
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        await message.answer(
            _("Неверный формат номера телефона. Пожалуйста, введите номер в формате +79999999999."),
            reply_markup=kb.cancel_editing_attr()
        )
        return
    else:
        if await state.get_state() == AddTeacherStates.waiting_for_new_phone_number:
            await state.update_data(phone_number=phone_number)
            await show_confirmation(message, state)
        elif await state.get_state() == EditTeacherStates.editing_phone_number:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id - 1,
                reply_markup=None
            )
            state_data = await state.get_data()
            prev_val = state_data.get("phone_number")
            await state.update_data(editing_value=phone_number)
            url_req = f"{settings.API_URL}/edit_teacher"
            response = requests.post(url_req, json={
                "teacher_id": state_data.get("chosen_lecturer_id"),
                "editing_attribute": state_data.get("editing_attribute"),
                "editing_value": phone_number})
            if response.status_code == 200:
                await state.update_data(chosen_lecturer_phone=phone_number)
                await message.answer(
                    _("Вы изменили номер телефона преподавателя {prev_val} на {val}.").format(
                        prev_val=format_value(prev_val), val=phone_number)
                )
                menu_message = await message.answer(
                    str(__("Вы в меню преподавателя {name}.\n\n"
                           "Номер телефона: {phone_number}\n"
                           "Почта: {email}\n"
                           "Социальная сеть: {social_page_link}\n"
                           "Аудитория: {classroom}")).format(
                        name=format_value(state_data.get("chosen_lecturer_name")),
                        phone_number=format_value(phone_number),
                        email=format_value(state_data.get("chosen_lecturer_email")),
                        social_page_link=format_value(state_data.get("chosen_lecturer_link")),
                        classroom=format_value(state_data.get("chosen_lecturer_classroom")),
                    ),
                    reply_markup=kb.teacher_menu()
                )
                await state.update_data(menu_message_id=menu_message.message_id)
            else:
                await message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddTeacherStates.waiting_for_new_email, EditTeacherStates.editing_email))
async def request_new_email(message: Message, state: FSMContext):
    email = message.text
    if not validate_email(email):
        await state.update_data(validation_status=True)
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        await message.answer(
            _("Неверный формат почты. Введите, пожалуйста, в формате name@mail.ru."),
            reply_markup=kb.cancel_editing_attr()
        )
        return
    else:
        if await state.get_state() == AddTeacherStates.waiting_for_new_email:
            await state.update_data(email=email)
            await show_confirmation(message, state)
        elif await state.get_state() == EditTeacherStates.editing_email:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id - 1,
                reply_markup=None
            )
            state_data = await state.get_data()
            prev_val = state_data.get("email")
            await state.update_data(editing_value=email)
            url_req = f"{settings.API_URL}/edit_teacher"
            response = requests.post(url_req, json={
                "teacher_id": state_data.get("chosen_lecturer_id"),
                "editing_attribute": state_data.get("editing_attribute"),
                "editing_value": email})
            if response.status_code == 200:
                await state.update_data(chosen_lecturer_email=email)
                await message.answer(
                    _("Вы изменили почту преподавателя {prev_val} на {val}.").format(
                        prev_val=format_value(prev_val), val=email)
                )
                menu_message = await message.answer(
                    str(__("Вы в меню преподавателя {name}.\n\n"
                           "Номер телефона: {phone_number}\n"
                           "Почта: {email}\n"
                           "Социальная сеть: {social_page_link}\n"
                           "Аудитория: {classroom}")).format(
                        name=format_value(state_data.get("chosen_lecturer_name")),
                        phone_number=format_value(state_data.get("chosen_lecturer_phone")),
                        email=format_value(email),
                        social_page_link=format_value(state_data.get("chosen_lecturer_link")),
                        classroom=format_value(state_data.get("chosen_lecturer_classroom")),
                    ),
                    reply_markup=kb.teacher_menu()
                )
                await state.update_data(menu_message_id=menu_message.message_id)
            else:
                await message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddTeacherStates.waiting_for_new_link, EditTeacherStates.editing_link))
async def request_new_link(message: Message, state: FSMContext):
    social_page_link = message.text
    if await state.get_state() == AddTeacherStates.waiting_for_new_link:
        await state.update_data(social_page_link=social_page_link)
        await show_confirmation(message, state)
    elif await state.get_state() == EditTeacherStates.editing_link:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        state_data = await state.get_data()
        prev_val = state_data.get("social_page_link")
        await state.update_data(editing_value=social_page_link)
        url_req = f"{settings.API_URL}/edit_teacher"
        response = requests.post(url_req, json={
            "teacher_id": state_data.get("chosen_lecturer_id"),
            "editing_attribute": state_data.get("editing_attribute"),
            "editing_value": social_page_link})
        if response.status_code == 200:
            await state.update_data(chosen_lecturer_link=social_page_link)
            await message.answer(
                _("Вы изменили почту преподавателя {prev_val} на {val}.").format(
                    prev_val=format_value(prev_val), val=social_page_link)
            )
            menu_message = await message.answer(
                str(__("Вы в меню преподавателя {name}.\n\n"
                       "Номер телефона: {phone_number}\n"
                       "Почта: {email}\n"
                       "Социальная сеть: {social_page_link}\n"
                       "Аудитория: {classroom}")).format(
                    name=format_value(state_data.get("chosen_lecturer_name")),
                    phone_number=format_value(state_data.get("chosen_lecturer_phone")),
                    email=format_value(state_data.get("chosen_lecturer_email")),
                    social_page_link=format_value(social_page_link),
                    classroom=format_value(state_data.get("chosen_lecturer_classroom")),
                ),
                reply_markup=kb.teacher_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await message.answer(json.loads(response.text).get('detail'))


@router.message(or_f(AddTeacherStates.waiting_for_new_classroom, EditTeacherStates.editing_classroom))
async def request_new_classroom(message: Message, state: FSMContext):
    classroom = message.text
    if await state.get_state() == AddTeacherStates.waiting_for_new_classroom:
        await state.update_data(classroom=classroom)
        await show_confirmation(message, state)
    elif await state.get_state() == EditTeacherStates.editing_classroom:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            reply_markup=None
        )
        state_data = await state.get_data()
        prev_val = state_data.get("classroom")
        await state.update_data(editing_value=classroom)
        url_req = f"{settings.API_URL}/edit_teacher"
        response = requests.post(url_req, json={
            "teacher_id": state_data.get("chosen_lecturer_id"),
            "editing_attribute": state_data.get("editing_attribute"),
            "editing_value": classroom})
        if response.status_code == 200:
            await state.update_data(chosen_lecturer_classroom=classroom)
            await message.answer(
                _("Вы изменили почту преподавателя {prev_val} на {val}.").format(
                    prev_val=format_value(prev_val), val=classroom)
            )
            menu_message = await message.answer(
                str(__("Вы в меню преподавателя {name}.\n\n"
                       "Номер телефона: {phone_number}\n"
                       "Почта: {email}\n"
                       "Социальная сеть: {social_page_link}\n"
                       "Аудитория: {classroom}")).format(
                    name=format_value(state_data.get("chosen_lecturer_name")),
                    phone_number=format_value(state_data.get("chosen_lecturer_phone")),
                    email=format_value(state_data.get("chosen_lecturer_email")),
                    social_page_link=format_value(state_data.get("chosen_lecturer_link")),
                    classroom=format_value(classroom),
                ),
                reply_markup=kb.teacher_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "add_teacher_by_hand")
async def add_teacher_by_hand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(is_from_api=False)
    await callback_query.message.edit_text(_("Введите ФИО преподавателя."))
    await state.set_state(AddTeacherStates.waiting_for_FIO)


@router.callback_query(F.data == "show_teacher_api_list")
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

            lecturers = set()
            for day in response_data['denominator']:
                for lesson in day:
                    if 'lecturer' in lesson:
                        lecturers.add(lesson['lecturer'])

            for day in response_data['numerator']:
                for lesson in day:
                    if 'lecturer' in lesson:
                        lecturers.add(lesson['lecturer'])

            lecturers_list = sorted(lecturers)

            url_req = f"{settings.API_URL}/get_teachers"
            response = requests.get(url_req, json={"user_id": state_data.get("user_id")})
            if response.status_code == 200:
                response_data = response.json()
                teachers_names = {teacher["name"] for teacher in response_data.get("teachers", [])}
                unique_lecturers = [lecturer for lecturer in lecturers_list if lecturer not in teachers_names]
                await state.update_data(lecturers=unique_lecturers)
                await callback_query.message.edit_text(
                    _("Список преподавателей:"),
                    reply_markup=kb.lecturers_list(unique_lecturers, page=0)
                )
            else:
                await callback_query.message.answer(json.loads(response.text).get('detail'))
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("lecturers_page_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    lecturers = state_data.get("lecturers", [])

    page = int(callback_query.data.split("_")[-1])
    await state.update_data(current_page=page)

    await callback_query.message.edit_reply_markup(
        reply_markup=kb.lecturers_list(lecturers, page=page)
    )


@router.callback_query(F.data.startswith("lecturer_index_"))
async def add_teacher_by_api_phone(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    lecturers = state_data.get("lecturers", [])

    lecturer_index = int(callback_query.data.split("_")[-1])
    selected_lecturer = lecturers[lecturer_index]

    await state.update_data(name=selected_lecturer)
    await state.update_data(is_from_api=True)

    if await state.get_state() != ShowTeacherStates.showing_list:
        await callback_query.message.edit_text(
            _("Введите номер телефона преподавателя в формате +79999999999."),
            reply_markup=kb.skip_button()
        )
        await state.set_state(AddTeacherStates.waiting_for_phone_number)

    elif await state.get_state() == ShowTeacherStates.showing_list:
        lecturers_id = state_data.get("lecturers_id")
        url_req = f"{settings.API_URL}/get_teacher"
        response = requests.get(url_req, json={"teacher_id": lecturers_id[int(lecturer_index)]})
        if response.status_code == 200:
            response_data = response.json()
            await state.update_data(chosen_lecturer_id=lecturers_id[int(lecturer_index)])
            await state.update_data(chosen_lecturer_name=response_data.get("name"))
            await state.update_data(chosen_lecturer_phone=response_data.get("phone_number"))
            await state.update_data(chosen_lecturer_email=response_data.get("email"))
            await state.update_data(chosen_lecturer_link=response_data.get("social_page_link"))
            await state.update_data(chosen_lecturer_classroom=response_data.get("classroom"))
            menu_message = await callback_query.message.edit_text(
                str(__("Вы в меню преподавателя {name}.\n\n"
                       "Номер телефона: {phone_number}\n"
                       "Почта: {email}\n"
                       "Социальная сеть: {social_page_link}\n"
                       "Аудитория: {classroom}")).format(
                    name=format_value(response_data.get("name")),
                    phone_number=format_value(response_data.get("phone_number")),
                    email=format_value(response_data.get("email")),
                    social_page_link=format_value(response_data.get("social_page_link")),
                    classroom=format_value(response_data.get("classroom")),
                ),
                reply_markup=kb.teacher_menu()
            )
            await state.update_data(menu_message_id=menu_message.message_id)
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.message(F.text == __("Посмотреть список преподавателей"))
async def add_teacher_start(message: Message, state: FSMContext):
    await state.set_state(ShowTeacherStates.showing_list)

    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        url_req = f"{settings.API_URL}/get_teachers"
        response = requests.get(url_req, json={"user_id": user_id})
        await state.update_data(user_id=user_id)
        if response.status_code == 200:
            response_data = response.json()
            sorted_teachers = sorted(response_data.get("teachers"), key=lambda x: x["name"])
            lecturers_dict = {teacher["teacher_id"]: teacher["name"] for teacher in sorted_teachers}
            await state.update_data(lecturers=list(lecturers_dict.values()))
            await state.update_data(lecturers_id=list(lecturers_dict.keys()))
            await message.answer(
                _("Список преподавателей:"),
                reply_markup=kb.lecturers_list(list(lecturers_dict.values()), page=0)
            )
        else:
            await message.answer(json.loads(response.text).get('detail'))
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "edit_teacher")
async def edit_teacher(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_teacher_api_status"
    response = requests.get(url_req, json={"teacher_id": state_data.get("chosen_lecturer_id")})
    if response.status_code == 200:
        response_data = response.json()
        api_status = response_data.get("is_from_API")
        await state.update_data(chosen_teacher_api_status=api_status)
        await callback_query.message.answer(
            _("Выберите изменения"),
            reply_markup=kb.edit_options(api_status)
        )
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("edit_teacher_"))
async def edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    field = callback_query.data.split("_")[-1]

    match field:
        case "fio":
            await state.update_data(editing_attribute="name")
            await callback_query.message.answer(_("Введите новые ФИО преподавателя."),
                                                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditTeacherStates.editing_fio)
        case "phone":
            await state.update_data(editing_attribute="phone_number")
            await callback_query.message.answer(_("Введите новый номер телефона преподавателя."),
                                                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditTeacherStates.editing_phone_number)
        case "email":
            await state.update_data(editing_attribute="email")
            await callback_query.message.answer(_("Введите новый адрес электронной почты преподавателя."),
                                                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditTeacherStates.editing_email)
        case "link":
            await state.update_data(editing_attribute="social_page_link")
            await callback_query.message.answer(_("Введите новую ссылку на социальную сеть преподавателя."),
                                                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditTeacherStates.editing_link)
        case "classroom":
            await state.update_data(editing_attribute="classroom")
            await callback_query.message.answer(
                _("Введите новый номер аудитории или кафедры, где можно найти преподавателя."),
                reply_markup=kb.cancel_editing_attr())
            await state.set_state(EditTeacherStates.editing_classroom)

    await callback_query.answer()


@router.callback_query(F.data == "cancel_editing")
async def cancel_edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=state_data.get("menu_message_id"),
        reply_markup=kb.teacher_menu()
    )


@router.callback_query(F.data == "cancel_editing_attr")
async def cancel_edit_teacher_data_attr(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    if state_data.get("validation_status"):
        menu_message = await callback_query.message.answer(
            str(__("Вы в меню преподавателя {name}.\n\n"
                   "Номер телефона: {phone_number}\n"
                   "Почта: {email}\n"
                   "Социальная сеть: {social_page_link}\n"
                   "Аудитория: {classroom}")).format(
                name=format_value(state_data.get("chosen_lecturer_name")),
                phone_number=format_value(state_data.get("chosen_lecturer_phone")),
                email=format_value(state_data.get("chosen_lecturer_email")),
                social_page_link=format_value(state_data.get("chosen_lecturer_link")),
                classroom=format_value(state_data.get("chosen_lecturer_classroom")),
            ),
            reply_markup=kb.teacher_menu()
        )
        await state.update_data(menu_message_id=menu_message.message_id)
    else:
        await callback_query.message.answer(
            _("Выберите изменения"),
            reply_markup=kb.edit_options(state_data.get("chosen_teacher_api_status"))
        )


@router.callback_query(F.data == "delete_teacher")
async def ask_deleting_teacher(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    state_data = await state.get_data()
    await callback_query.message.answer(
        _("Вы действительно хотите удалить преподавателя {name}?").format(name=state_data.get("chosen_lecturer_name")),
        reply_markup=kb.confirm_delete_teacher()
    )


@router.callback_query(F.data == "confirm_deleting")
async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/delete_teacher"
    response = requests.delete(url_req, json={"teacher_id": state_data.get("chosen_lecturer_id")})
    if response.status_code == 200:
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        await callback_query.message.answer(
            _("Преподаватель {name} успешно удален.").format(name=state_data.get("chosen_lecturer_name"))
        )
        await add_teacher_start(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_deleting")
async def confirm_deleting(callback_query: CallbackQuery, state: FSMContext):
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
        _("Вы отменили удаление преподавателя {name}.").format(name=state_data.get("chosen_lecturer_name"))
    )
    menu_message = await callback_query.message.answer(
        str(__("Вы в меню преподавателя {name}.\n\n"
               "Номер телефона: {phone_number}\n"
               "Почта: {email}\n"
               "Социальная сеть: {social_page_link}\n"
               "Аудитория: {classroom}")).format(
            name=format_value(state_data.get("name")),
            phone_number=format_value(state_data.get("phone_number")),
            email=format_value(state_data.get("email")),
            social_page_link=format_value(state_data.get("social_page_link")),
            classroom=format_value(state_data.get("classroom")),
        ),
        reply_markup=kb.teacher_menu()
    )
    await state.update_data(menu_message_id=menu_message.message_id)


@router.callback_query(F.data == "back_to_teachers_list")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await add_teacher_start(callback_query.message, state)
