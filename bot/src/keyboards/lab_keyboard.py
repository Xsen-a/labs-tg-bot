from datetime import datetime, timedelta, date
from calendar import monthrange

from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def add_lab_confirm():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_discipline")
    builder.button(text=_("Нет"), callback_data="cancel_add_discipline")
    builder.button(text=_("Изменить дисциплину"), callback_data="change_lab_discipline")
    builder.button(text=_("Изменить название"), callback_data="change_lab_name")
    builder.button(text=_("Изменить текст"), callback_data="change_lab_text")
    builder.button(text=_("Изменить файлы"), callback_data="change_lab_files")
    builder.button(text=_("Изменить ссылку"), callback_data="change_lab_link")
    builder.button(text=_("Изменить дату начала"), callback_data="change_lab_start_date")
    builder.button(text=_("Изменить срок сдачи"), callback_data="change_lab_end_date")
    builder.button(text=_("Изменить доп. информацию"), callback_data="change_lab_additional_info")
    builder.adjust(1)
    return builder.as_markup()


def skip_button():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Пропустить"), callback_data="skip")
    builder.adjust(1)
    return builder.as_markup()


def finish_files_button():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Завершить добавление файлов"), callback_data="finish_files")
    builder.adjust(1)
    return builder.as_markup()


def add_option():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Показать список"), callback_data="show_discipline_api_list")
    builder.button(text=_("Ввести вручную"), callback_data="add_discipline_by_hand")
    builder.adjust(1)
    return builder.as_markup()


def disciplines_list(disciplines, page: int = 0, items_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_disciplines = disciplines[start_idx:end_idx]

    for i, discipline in enumerate(current_page_disciplines, start=start_idx):
        builder.button(text=_("{discipline}".format(discipline=disciplines[i])),
                       callback_data=f"lab_discipline_index_{i}"
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


def discipline_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Изменить"), callback_data="edit_discipline")
    builder.button(text=_("Удалить"), callback_data="delete_discipline")
    builder.button(text=_("Назад"), callback_data="back_to_discipline_list")
    builder.adjust(1)
    return builder.as_markup()


def edit_options(exist_teacher, is_from_api):
    builder = InlineKeyboardBuilder()
    if not is_from_api:
        builder.button(text=_("Изменить название"), callback_data="edit_discipline_name")
    if exist_teacher:
        builder.button(text=_("Изменить преподавателя"), callback_data="edit_discipline_teacher")
    else:
        builder.button(text=_("Добавить преподавателя"), callback_data="edit_discipline_teacher")
    builder.adjust(1)
    return builder.as_markup()


def cancel_editing_attr():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Отмена"), callback_data="cancel_editing_attr_discipline")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_discipline():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Да"), callback_data="confirm_deleting_discipline")
    builder.button(text=_("Нет"), callback_data="cancel_deleting_discipline")
    builder.adjust(1)
    return builder.as_markup()


def back_d_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"lab_disciplines_page_{page - 1}")


def continue_d_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"lab_disciplines_page_{page + 1}")


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
