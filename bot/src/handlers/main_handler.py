from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message
from ..settings import settings
import requests
import json

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

import src.keyboards.menu as menu_keyboards


router = Router()


@router.message(CommandStart())
async def get_contact_handler(message: Message, state: FSMContext):
    await message.answer(
        _("Лабораторные работы"),
        reply_markup=menu_keyboards.main_menu_keyboard(),
    )