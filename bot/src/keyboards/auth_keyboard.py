from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def send_tg_id():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Отправить Telegram ID"), callback_data="send_tg_id")
    builder.adjust(1)
    return builder.as_markup()


def is_petrsu_student():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Да, я студент ПетрГУ"), callback_data="petrsu_true")
    builder.button(text=_("Нет, я не студент ПетрГУ"), callback_data="petrsu_false")
    builder.adjust(1)
    return builder.as_markup()