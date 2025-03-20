from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def settings_menu_keyboard(is_petrsu_student):
    if is_petrsu_student:
        builder = InlineKeyboardBuilder()
        builder.button(text=_("Изменить группу"), callback_data="change_group")
        builder.button(text=_("Изменить статус студента ПетрГУ"), callback_data="change_petrsu_status")
        builder.adjust(1)
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text=_("Изменить статус студента ПетрГУ"), callback_data="change_petrsu_status")
        builder.adjust(1)
    return builder.as_markup()