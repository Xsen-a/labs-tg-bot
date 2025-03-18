from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils import i18n

from ..settings import settings
import requests
import json

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

import bot.src.keyboards.menu_keyboard as kb
import bot.src.keyboards.auth_keyboard as kb_auth
import bot.src.handlers.auth_bot_handler as auth

router = Router()


@router.message(CommandStart())
async def start_dialog(message: Message, state: FSMContext, telegram_id: int = None):

    if telegram_id is not None:
        current_user_tg_id = telegram_id
    else:
        current_user_tg_id = message.from_user.id

    url_req = f"{settings.API_URL}/check_user"
    response = requests.get(url_req, json={"telegram_id": str(current_user_tg_id)})
    response_data = response.json()
    if response_data.get("exists", True):
        url_req = f"{settings.API_URL}/check_is_petrsu_student"
        response = requests.get(url_req, json={"telegram_id": str(current_user_tg_id)})
        response_data = response.json()
        if response_data.get("is_petrsu_student", True):
            if telegram_id is None:
                await message.answer(
                    _("Добро пожаловать! Ваша группа {group}.").format(group=response_data.get("group"))
                )
            await message.answer(
                _("Вы находитесь в главном меню."),
                reply_markup=kb.main_menu_keyboard(),
            )
        else:
            if telegram_id is None:
                await message.answer(
                    _("Добро пожаловать!")
                )
            await message.answer(
                _("Вы находитесь в главном меню."),
                reply_markup=kb.main_menu_keyboard(),
            )
    else:
        await state.update_data(tg_id=str(current_user_tg_id))
        await message.answer(
            _("Подтвердите, пожалуйста, отправку Telegram ID для регистрации."),
            reply_markup=kb_auth.send_tg_id(),
        )



@router.message(F.text == __("⬅ Назад"))
async def back_handler(msg: Message, state: FSMContext):
    await state.clear()
    await start_dialog(msg, state)


@router.message(F.text == __("Лабораторные работы"))
async def open_labs_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню лабораторных работ."),
        reply_markup=kb.labs_menu_keyboard(),
    )


@router.message(F.text == __("Посмотреть список лабораторных работ"))
async def open_labs_list(message: Message, state: FSMContext):
    await message.answer(
        _("Выберите вид отображения списка."),
        reply_markup=kb.labs_list_filer(),
    )


@router.message(F.text == __("Диаграммы Ганта"))
async def open_gant_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Выберите период для диаграммы Ганта."),
        reply_markup=kb.choose_gant_diagram(),
    )


@router.message(F.text == __("Дисциплины"))
async def open_discipline_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню дисциплин."),
        reply_markup=kb.discipline_menu_keyboard(),
    )


@router.message(F.text == __("Преподаватели"))
async def open_teacher_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню преподавателей."),
        reply_markup=kb.teacher_menu_keyboard(),
    )


@router.message(F.text == __("Пары"))
async def open_lesson_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню пар."),
        reply_markup=kb.lesson_menu_keyboard(),
    )


@router.message(F.text == __("Настройки"))
async def open_settings_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в разделе пользовательских настроек. (дополнить по статусу)"),
        reply_markup=kb.settings_menu_keyboard(),
    )