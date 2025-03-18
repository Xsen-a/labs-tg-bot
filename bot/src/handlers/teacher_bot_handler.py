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


def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, email):
        return True
    else:
        return False


@router.message(F.text == __("Добавить преподавателя"))
async def add_teacher_start(msg: Message, state: FSMContext):
    await msg.answer(_("Введите ФИО преподавателя."))
    await state.set_state(AddTeacherStates.waiting_for_FIO)


@router.message(AddTeacherStates.waiting_for_FIO)
async def add_teacher_fio(msg: Message, state: FSMContext):
    fio = msg.text
    if not validate_fio(fio):
        await msg.answer(
            _("Неверный формат ФИО. Введите, пожалуйста, в формате Фамилия Имя Отчество (если имеется).")
        )
        return
    else:
        await state.update_data(name=fio)
        await msg.answer(
            _("Введите номер телефона преподавателя.")
        )
        await state.set_state(AddTeacherStates.waiting_for_phone_number)


@router.message(AddTeacherStates.waiting_for_phone_number)
async def add_teacher_phone_number(msg: Message, state: FSMContext):
    phone_number = msg.text
    if not validate_phone_number(phone_number):
        await msg.answer(
            _("Неверный формат номера телефона. Пожалуйста, введите номер в формате +79999999999.")
        )
        return
    else:
        await state.update_data(phone_number=phone_number)
        await msg.answer(
            _("Введите почту преподавателя.")
        )
        await state.set_state(AddTeacherStates.waiting_for_email)


@router.message(AddTeacherStates.waiting_for_email)
async def add_teacher_email(msg: Message, state: FSMContext):
    email = msg.text
    if not validate_email(email):
        await msg.answer(
            _("Неверный формат почты. Введите, пожалуйста, в формате name@mail.ru.")
        )
        return
    else:
        await state.update_data(email=email)
        await msg.answer(
            _("Введите ссылку на социальную сеть преподавателя.")
        )
        await state.set_state(AddTeacherStates.waiting_for_link)


@router.message(AddTeacherStates.waiting_for_link)
async def add_teacher_link(msg: Message, state: FSMContext):
    social_page_link = msg.text
    await state.update_data(social_page_link=social_page_link)
    await msg.answer(
        _("Введите номер аудитории или кафедры, где можно найти преподавателя.")
    )
    await state.set_state(AddTeacherStates.waiting_for_classroom)


@router.message(AddTeacherStates.waiting_for_classroom)
async def add_teacher_phone_number(msg: Message, state: FSMContext):
    classroom = msg.text
    await state.update_data(classroom=classroom)
    user_data = await state.get_data()
    name = user_data.get("name")
    email = user_data.get("email")
    phone_number = user_data.get("phone_number")
    social_page_link = user_data.get("social_page_link")
    classroom = user_data.get("classroom")

    await msg.answer(
        _("Вы действительно хотите добавить преподавателя\n{name}?\n\n"
          "Номер телефона: {phone_number}\n"
          "Почта: {email}\n"
          "Социальная сеть: {social_page_link}\n"
          "Аудитория:{classroom}\n")
        .format(name=name, phone_number=phone_number, email=email, social_page_link=social_page_link,
                classroom=classroom),
        reply_markup=kb.add_teacher_confirm(),
    )


@router.callback_query(F.data == "add_teacher")
async def add_teacher_end(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name")
    email = user_data.get("email")
    phone_number = user_data.get("phone_number")
    social_page_link = user_data.get("social_page_link")
    classroom = user_data.get("classroom")
    url_req = f"{settings.API_URL}/add_teacher"
    response = requests.post(url_req, json={"user_id": 1,
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
                name=name,
                phone_number=phone_number,
                email=email,
                social_page_link=social_page_link,
                classroom=classroom
            )
        )
        await state.clear()
        await main.open_teacher_menu(callback_query.message, state)
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "change_fio")
async def change_teacher_fio(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите новые ФИО.")
    await state.set_state(AddTeacherStates.waiting_for_new_fio)


@router.message(AddTeacherStates.waiting_for_new_fio)
async def request_new_fio(msg: Message, state: FSMContext):
    fio = msg.text
    if not validate_fio(fio):
        await msg.answer(
            "Неверный формат ФИО. Введите, пожалуйста, в формате Фамилия Имя Отчество (если имеется)."
        )
        return
    else:
        await state.update_data(name=fio)
        await msg.answer(f"Введенные ФИО:\n\n" f"{fio}")
        user_data = await state.get_data()
        name = user_data.get("name")
        phone_number = user_data.get("phone_number")
        await msg.answer(
            f"Добавить преподавателя:\n\n" f"ФИО: {name}\n" f"Номер телефона: {phone_number}",
            reply_markup=kb.add_teacher_confirm,
        )


@router.callback_query(F.data == "change_phone_number")
async def change_teacher_fio(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите новый номер телефона.")
    await state.set_state(AddTeacherStates.waiting_for_new_phone_number)


@router.message(AddTeacherStates.waiting_for_new_phone_number)
async def request_new_phone_number(msg: Message, state: FSMContext):
    phone_number = msg.text
    if not validate_phone_number(phone_number):
        await msg.answer(
            "Неверный формат номера телефона. Пожалуйста, введите номер в формате +79999999999."
        )
        return
    else:
        await state.update_data(phone=phone_number)
        await msg.answer(f"Введенный номер телефона: {phone_number}")
        user_data = await state.get_data()
        name = user_data.get("name")
        phone = user_data.get("phone")

        await msg.answer(
            f"Добавить преподавателя:\n\n" f"ФИО: {name}\n" f"Номер телефона: {phone}",
            reply_markup=kb.add_teacher_confirm,
        )
