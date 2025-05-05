from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def choose_gant_diagram():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Общая"), callback_data="gant_full")
    builder.button(text=_("Месяц"), callback_data="gant_month")
    builder.button(text=_("Две недели"), callback_data="gant_two_weeks")
    builder.adjust(1)
    return builder.as_markup()


month_translation = {
    # Полные названия
    'January': 'Январь',
    'February': 'Февраль',
    'March': 'Март',
    'April': 'Апрель',
    'May': 'Май',
    'June': 'Июнь',
    'July': 'Июль',
    'August': 'Август',
    'September': 'Сентябрь',
    'October': 'Октябрь',
    'November': 'Ноябрь',
    'December': 'Декабрь',

    # Сокращенные (3 буквы)
    'Jan': 'Янв',
    'Feb': 'Фев',
    'Mar': 'Мар',
    'Apr': 'Апр',
    'Jun': 'Июн',
    'Jul': 'Июл',
    'Aug': 'Авг',
    'Sep': 'Сен',
    'Oct': 'Окт',
    'Nov': 'Ноя',
    'Dec': 'Дек',

    # Числовое представление (1-12 → название)
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

month_numbers = {
    'January': '1',
    'February': '2',
    'March': '3',
    'April': '4',
    'May': '5',
    'June': '6',
    'July': '7',
    'August': '8',
    'September': '9',
    'October': '10',
    'November': '11',
    'December': '12',
}

def translate_date(english_date):
    try:
        # Пробуем разные варианты разделителей
        parts = english_date.replace(',', ' ').split()
        month = parts[0]
        year = parts[-1]
        return f"{month_translation.get(month, month)} {year}"
    except:
        return english_date  # Возвращаем как есть в случае ошибки


def months(months_list):
    builder = InlineKeyboardBuilder()
    for i in months_list:
        builder.button(text=translate_date(i), callback_data=f"gant_month_{month_numbers[i.split(' ')[0]]}_{i.split(' ')[1]}")
    builder.adjust(1)
    return builder.as_markup()
