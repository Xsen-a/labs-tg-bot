from datetime import datetime, timedelta, date
from calendar import monthrange

from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from api.src.models import Status


def add_lesson_confirm():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_lesson")
    builder.button(text=_("Нет"), callback_data="cancel_add_lesson")
    builder.button(text=_("Изменить дисциплину"), callback_data="change_lesson_discipline")
    builder.button(text=_("Изменить аудиторию"), callback_data="change_lesson_classroom")
    builder.button(text=_("Изменить дату первого занятия"), callback_data="change_lesson_start_date")
    builder.button(text=_("Изменить периодичность"), callback_data="change_lesson_periodicity")
    builder.button(text=_("Изменить время начала"), callback_data="change_lesson_start_time")
    builder.button(text=_("Изменить время окончания"), callback_data="change_lesson_end_time")
    builder.adjust(1, 1, 2, 2, 2)
    return builder.as_markup()


def is_periodicity():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Да"), callback_data="periodicity")
    builder.button(text=_("Нет"), callback_data="not_periodicity")
    builder.adjust(1)
    return builder.as_markup()


def periodicity_type():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Дни"), callback_data="periodicity_day")
    builder.button(text=_("Недели"), callback_data="periodicity_week")
    builder.adjust(1)
    return builder.as_markup()


def get_keyboard_hours():
    builder = InlineKeyboardBuilder()
    for i in range(24):
        builder.button(text=str(i), callback_data=f"hour_{str(i)}")
    builder.adjust(4)
    return builder.as_markup()


def get_keyboard_minutes():
    builder = InlineKeyboardBuilder()
    for i in range(0, 60, 5):
        minutes = str(i)
        if len(minutes) != 2:
            minutes = "0" + minutes
        builder.button(text=minutes, callback_data=f"minutes_{minutes}")
    builder.button(text="Другое", callback_data="another_minutes")
    builder.adjust(6)
    return builder.as_markup()


def lesson_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Изменить"), callback_data="edit_lesson")
    builder.button(text=_("Удалить"), callback_data="delete_lesson")
    builder.button(text=_("Назад"), callback_data="back_to_lesson_menu")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_lesson():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Да"), callback_data="confirm_deleting_lesson")
    builder.button(text=_("Нет"), callback_data="cancel_deleting_lesson")
    builder.adjust(1)
    return builder.as_markup()


def lesson_edit_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Изменить дисциплину"), callback_data="edit_lesson_discipline")
    builder.button(text=_("Изменить аудиторию"), callback_data="edit_lesson_classroom")
    builder.button(text=_("Изменить дату первого занятия"), callback_data="edit_lesson_start_date")
    builder.button(text=_("Изменить периодичность"), callback_data="edit_lesson_periodicity")
    builder.button(text=_("Изменить время начала"), callback_data="edit_lesson_start_time")
    builder.button(text=_("Изменить время окончания"), callback_data="edit_lesson_end_time")
    builder.button(text=_("Назад"), callback_data="back_to_chosen_lesson_menu")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def disciplines_list(disciplines, page: int = 0, items_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_disciplines = disciplines[start_idx:end_idx]

    for i, discipline in enumerate(current_page_disciplines, start=start_idx):
        builder.button(text=_("{discipline}".format(discipline=disciplines[i])),
                       callback_data=f"lesson_discipline_index_{i}"
                       )

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            back_d_list(page)
        )

    if end_idx < len(disciplines):
        navigation_buttons.append(
            continue_d_list(page)
        )

    builder.adjust(1)
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def back_d_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"lesson_disciplines_page_{page - 1}")


def continue_d_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"lesson_disciplines_page_{page + 1}")


MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

DAY_SHORT_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    # def calendar(current_date: datetime = None) -> InlineKeyboardMarkup:
    """Генератор клавиатуры календаря"""

    now = datetime.now()
    # if current_date is None:
    #     year = now.year
    #     month = now.month
    # else:
    #     year = current_date.year
    #     month = current_date.month
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    # Получаем информацию о месяце
    _, num_days = monthrange(year, month)
    first_day = date(year, month, 1)
    starting_weekday = first_day.weekday()  # 0-пн, 6-вс

    # Создаем список для кнопок
    keyboard = []

    # Заголовок (месяц и год + навигация)
    keyboard.append([
        InlineKeyboardButton(text="<<", callback_data=f"calendar_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{MONTH_NAMES[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">>", callback_data=f"calendar_next_{year}_{month}")
    ])

    # Дни недели
    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="ignore") for day in DAY_SHORT_NAMES
    ])

    # Дни месяца
    row = []
    # Пустые клетки перед первым днем
    for _ in range(starting_weekday):
        row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"calendar_date_{date_str}"))
        if len(row) == 7:
            keyboard.append(row)
            row = []

    if row:  # Добавляем оставшиеся дни
        for cell in range(7 - len(row)):
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        keyboard.append(row)

    # Кнопка "Сегодня"
    keyboard.append([
        InlineKeyboardButton(text="Сегодня", callback_data=f"calendar_date_{now.strftime('%Y-%m-%d')}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_abbreviation(full_name):
    if not full_name or not isinstance(full_name, str):
        return ""

    cleaned = ''.join(c for c in full_name if c.isalpha() or c.isspace() or c == '-')

    words = []
    for part in cleaned.split():
        words.extend(part.split('-'))

    abbreviation = ''.join(word[0].upper() for word in words if word and len(word) > 1)

    return abbreviation


def lessons_list(lessons, disciplines_dict, page: int = 0, items_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_lessons = lessons[start_idx:end_idx]

    for i, lesson in enumerate(current_page_lessons, start=start_idx):
        abb = generate_abbreviation(disciplines_dict[lesson["discipline_id"]])
        date = datetime.strptime(lesson["start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        time = f"{lessons[i]['start_time'][:-3]} - {lessons[i]['end_time'][:-3]}"

        # Формирование текста в зависимости от условия
        if int(lesson["periodicity_days"]) != 0:
            text = _("{abb} - {date}, раз в {days} дней, {time}").format(
                abb=abb, date=date, days=lesson["periodicity_days"], time=time)
        else:
            text = _("{abb} - {date}, {time}").format(abb=abb, date=date, time=time)

        builder.button(
            text=text,
            callback_data=f'lesson_index_{lesson["lesson_id"]}'
        )

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            back_l_list(page)
        )

    if end_idx < len(lessons):
        navigation_buttons.append(
            continue_l_list(page)
        )

    builder.adjust(1)
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def back_l_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"lesson_page_{page - 1}")


def continue_l_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"lesson_page_{page + 1}")
