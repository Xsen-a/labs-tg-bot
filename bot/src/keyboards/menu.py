from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def back_button():
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("⬅ Назад"))
    return builder.as_markup()

def main_menu_keyboard():
    builder_column = ReplyKeyboardBuilder()

    builder_column.button(text=_("Лабораторные работы"))
    builder_column.button(text=_("Диаграмма Ганта"))
    builder_column.adjust(1)

    builder_row = ReplyKeyboardBuilder()
    builder_row.button(text=_("Дисциплины"))
    builder_row.button(text=_("Преподаватели"))
    builder_row.button(text=_("Преподаватели и дисциплины"))
    builder_row.button(text=_("Пары"))
    builder_row.button(text=_("Настройки"))
    builder_row.adjust(2)

    builder_column.attach(builder_row)
    return builder_column.as_markup()
