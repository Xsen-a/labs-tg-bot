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

import bot.src.keyboards.menu as menu_keyboards

router = Router()


@router.message(CommandStart())
async def start_dialog(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в главном меню."),
        reply_markup=menu_keyboards.main_menu_keyboard(),
    )


@router.message(F.text == __("⬅ Назад"))
async def back_handler(msg: Message, state: FSMContext):
    await state.clear()
    await start_dialog(msg, state)


@router.message(F.text == __("Лабораторные работы"))
async def open_labs_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню лабораторных работ."),
        reply_markup=menu_keyboards.labs_menu_keyboard(),
    )


@router.message(F.text == __("Посмотреть список лабораторных работ"))
async def open_labs_list(message: Message, state: FSMContext):
    await message.answer(
        _("Выберите вид отображения списка."),
        reply_markup=menu_keyboards.labs_list_filer(),
    )


@router.message(F.text == __("Диаграммы Ганта"))
async def open_gant_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Выберите период для диаграммы Ганта."),
        reply_markup=menu_keyboards.choose_gant_diagram(),
    )


@router.message(F.text == __("Дисциплины"))
async def open_discipline_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню дисциплин."),
        reply_markup=menu_keyboards.discipline_menu_keyboard(),
    )


@router.message(F.text == __("Преподаватели"))
async def open_teacher_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню преподавателей."),
        reply_markup=menu_keyboards.teacher_menu_keyboard(),
    )


@router.message(F.text == __("Пары"))
async def open_lesson_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в меню пар."),
        reply_markup=menu_keyboards.lesson_menu_keyboard(),
    )


@router.message(F.text == __("Настройки"))
async def open_settings_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Вы находитесь в разделе пользовательских настроек. (дополнить по статусу)"),
        reply_markup=menu_keyboards.settings_menu_keyboard(),
    )