from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def back_button():
    return KeyboardButton(text=_("⬅ Назад"))


def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Задания"))

    builder.button(text=_("Диаграмма Ганта"))
    builder.button(text=_("Канбан-доска"))

    builder.button(text=_("Занятия"))
    builder.button(text=_("Дисциплины"))
    builder.button(text=_("Преподаватели"))

    builder.button(text=_("Настройки"))

    builder.adjust(1, 2, 2, 2)

    return builder.as_markup(resize_keyboard=True)


def labs_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_("Добавить задание"))
    builder.button(text=_("Посмотреть список заданий"))
    builder.row(back_button())
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

    builder.button(text=_("Добавить занятие"))
    builder.button(text=_("Посмотреть список занятий"))
    builder.row(back_button())
    builder.adjust(1)
    return builder.as_markup()
