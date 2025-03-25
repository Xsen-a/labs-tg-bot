import re
import json
import requests

from aiogram import Router, F
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


def format_value(value):
    return "-" if value is None else value


def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, email):
        return True
    else:
        return False


@router.message(F.text == __("Добавить преподавателя"))
async def add_teacher_start(message: Message, state: FSMContext):
    user_data = await state.get_data()
    telegram_id = user_data.get("telegram_id")
    url_req = f"{settings.API_URL}/check_is_petrsu_student"
    print(telegram_id)
    response = requests.get(url_req, json={"telegram_id": telegram_id})
    if response.json().get("is_petrsu_student", True):
        await message.answer(_("Выбрать преподавателя из списка или добавить вручную?"))
    else:
        await message.answer(_("Введите ФИО преподавателя."))
        await state.set_state(AddTeacherStates.waiting_for_FIO)


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
    await callback_query.message.answer(
        _("Введите почту преподавателя в формате name@mail.ru."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_email)


@router.message(AddTeacherStates.waiting_for_email)
async def add_teacher_email(message: Message, state: FSMContext):
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
    await callback_query.message.answer(
        _("Введите ссылку на социальную сеть преподавателя."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_link)


@router.message(AddTeacherStates.waiting_for_link)
async def add_teacher_link(message: Message, state: FSMContext):
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
    await callback_query.message.answer(
        _("Введите номер аудитории или кафедры, где можно найти преподавателя."),
        reply_markup=kb.skip_button()
    )
    await state.set_state(AddTeacherStates.waiting_for_classroom)


@router.message(AddTeacherStates.waiting_for_classroom)
async def add_teacher_classroom(message: Message, state: FSMContext):
    classroom = message.text
    await state.update_data(classroom=classroom)
    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name")
    email = user_data.get("email")
    phone_number = user_data.get("phone_number")
    social_page_link = user_data.get("social_page_link")
    classroom = user_data.get("classroom")

    await message.answer(
        _("Вы действительно хотите добавить преподавателя {name}?\n\n"
          "Номер телефона: {phone_number}\n"
          "Почта: {email}\n"
          "Социальная сеть: {social_page_link}\n"
          "Аудитория: {classroom}\n")
        .format(
            name=format_value(name),
            phone_number=format_value(phone_number),
            email=format_value(email),
            social_page_link=format_value(social_page_link),
            classroom=format_value(classroom),
        ),
        reply_markup=kb.add_teacher_confirm(),
    )


@router.callback_query(F.data == "skip", AddTeacherStates.waiting_for_classroom)
async def skip_classroom(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.update_data(classroom=None)
    await show_confirmation(callback_query.message, state)


@router.callback_query(F.data == "add_teacher")
async def add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name")
    email = user_data.get("email")
    phone_number = user_data.get("phone_number")
    social_page_link = user_data.get("social_page_link")
    classroom = user_data.get("classroom")
    telegram_id = user_data.get("telegram_id")
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": telegram_id})
    url_req = f"{settings.API_URL}/add_teacher"
    response = requests.post(url_req, json={"user_id": response.json().get("user_id"),
                                            "name": name,
                                            "phone_number": phone_number,
                                            "email": email,
                                            "social_page_link": social_page_link,
                                            "classroom": classroom,
                                            "is_from_API": False})
    if response.status_code == 200:
        await callback_query.message.answer(
            str(__("Преподаватель {name} добавлен.\n\n"
                   "Номер телефона: {phone_number}\n"
                   "Почта: {email}\n"
                   "Социальная сеть: {social_page_link}\n"
                   "Аудитория: {classroom}")).format(
                name=format_value(name),
                phone_number=format_value(phone_number),
                email=format_value(email),
                social_page_link=format_value(social_page_link),
                classroom=format_value(classroom),
            )
        )
        await main_bot_handler.open_teacher_menu(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "cancel_add_teacher")
async def cancel_add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(_("Вы отменили добавление преподавателя."))
    await main_bot_handler.open_teacher_menu(callback_query.message, state)


@router.callback_query(F.data.startswith("change_teacher_"))
async def edit_teacher_data(callback_query: CallbackQuery, state: FSMContext):
    print(callback_query.data)
    field = callback_query.data.split("_")[-1]
    print(field)

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
            await callback_query.message.answer(_("Введите новый номер аудитории или кафедры, где можно найти преподавателя."))
            await state.set_state(AddTeacherStates.waiting_for_new_classroom)

    await callback_query.answer()


@router.message(AddTeacherStates.waiting_for_new_fio)
async def request_new_fio(message: Message, state: FSMContext):
    fio = message.text
    if not validate_fio(fio):
        await message.answer(
            _("Неверный формат ФИО. Введите, пожалуйста, в формате Фамилия Имя Отчество (если имеется).")
        )
        return
    else:
        await state.update_data(name=fio)
        await show_confirmation(message, state)


@router.message(AddTeacherStates.waiting_for_new_phone_number)
async def request_new_phone_number(message: Message, state: FSMContext):
    phone_number = message.text
    if not validate_phone_number(phone_number):
        await message.answer(
            _("Неверный формат номера телефона. Пожалуйста, введите номер в формате +79999999999.")
        )
        return
    else:
        await state.update_data(phone_number=phone_number)
        await show_confirmation(message, state)


@router.message(AddTeacherStates.waiting_for_new_email)
async def request_new_email(message: Message, state: FSMContext):
    email = message.text
    if not validate_email(email):
        await message.answer(
            _("Неверный формат почты. Введите, пожалуйста, в формате name@mail.ru.")
        )
        return
    else:
        await state.update_data(email=email)
        await show_confirmation(message, state)


@router.message(AddTeacherStates.waiting_for_new_link)
async def request_new_link(message: Message, state: FSMContext):
    social_page_link = message.text
    await state.update_data(social_page_link=social_page_link)
    await show_confirmation(message, state)


@router.message(AddTeacherStates.waiting_for_new_classroom)
async def request_new_classroom(message: Message, state: FSMContext):
    classroom = message.text
    await state.update_data(classroom=classroom)
    await show_confirmation(message, state)
