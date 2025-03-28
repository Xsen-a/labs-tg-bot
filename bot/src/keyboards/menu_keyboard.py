from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def back_button():
    return KeyboardButton(text=_("⬅ Назад"))


def main_menu_keyboard():
    builder_column = ReplyKeyboardBuilder()

    builder_column.button(text=_("Лабораторные работы"))
    builder_column.button(text=_("Диаграммы Ганта"))
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


def labs_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Добавить лабораторную работу"))
    builder.button(text=_("Посмотреть список лабораторных работ"))
    builder.row(back_button())
    builder.adjust(1)
    return builder.as_markup()


def labs_list_filer():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("По статусу"), callback_data="list_status")
    builder.button(text=_("По дисциплине"), callback_data="list_discipline")
    builder.button(text=_("На 7 дней"), callback_data="list_seven_days")
    builder.adjust(1)
    return builder.as_markup()


def choose_gant_diagram():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Общая"), callback_data="gant_full")
    builder.button(text=_("Месяц"), callback_data="gant_month")
    builder.button(text=_("Две недели"), callback_data="gant_two_weeks")
    builder.adjust(1)
    return builder.as_markup()


def discipline_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Добавить дисциплину"))
    builder.button(text=_("Посмотреть список дисциплин"))
    builder.row(back_button())
    builder.adjust(1)
    return builder.as_markup()


def teacher_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Добавить преподавателя"))
    builder.button(text=_("Посмотреть список преподавателей"))
    builder.row(back_button())
    builder.adjust(1)
    return builder.as_markup()


def lesson_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Добавить пару"))
    builder.button(text=_("Посмотреть список пар"))
    builder.row(back_button())
    builder.adjust(1)
    return builder.as_markup()
