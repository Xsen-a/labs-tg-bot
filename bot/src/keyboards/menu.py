from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

# back_button = [KeyboardButton(text=_("⬅ Назад"))]
#
# main_menu = [
#     [KeyboardButton(text=_("Лабораторные работы"))],
#     [KeyboardButton(text=_("Диаграмма Ганта"))],
#     [KeyboardButton(text=_("Дисциплины")), KeyboardButton(text=_("Преподаватели"))],
#     [KeyboardButton(text=_("Преподаватели и дисциплины"))],
#     [KeyboardButton(text=_("Пары"))],
#     [KeyboardButton(text=_("Настройки"))],
# ]
#
# main_menu_panel = ReplyKeyboardMarkup(keyboard=main_menu)

back_button = [KeyboardButton(text="⬅ Назад")]

main_menu = [
    [KeyboardButton(text="Лабораторные работы")], [KeyboardButton(text="Диаграммы Ганта")],
    [KeyboardButton(text="Дисциплины"), KeyboardButton(text="Преподаватели")],
    [KeyboardButton(text="Преподаватели и дисциплины"), KeyboardButton(text="Пары")],
    [KeyboardButton(text="Настройки")],
]

main_menu_panel = ReplyKeyboardMarkup(keyboard=main_menu)