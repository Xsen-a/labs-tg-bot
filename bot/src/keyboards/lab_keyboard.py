from datetime import datetime, timedelta, date
from calendar import monthrange

from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from api.src.models import Status


def add_lab_confirm():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_lab")
    builder.button(text=_("Нет"), callback_data="cancel_add_lab")
    builder.button(text=_("Изменить дисциплину"), callback_data="change_lab_discipline")
    builder.button(text=_("Изменить название"), callback_data="change_lab_name")
    builder.button(text=_("Изменить текст"), callback_data="change_lab_description")
    builder.button(text=_("Изменить файлы"), callback_data="change_lab_files")
    builder.button(text=_("Изменить ссылку"), callback_data="change_lab_link")
    builder.button(text=_("Изменить доп. информацию"), callback_data="change_lab_additional_info")
    builder.button(text=_("Изменить дату начала"), callback_data="change_lab_start_date")
    builder.button(text=_("Изменить срок сдачи"), callback_data="change_lab_end_date")
    builder.adjust(1, 1, 2, 2, 2, 2)
    return builder.as_markup()


def lab_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Изменить статус"), callback_data="edit_status")
    builder.button(text=_("Изменить"), callback_data="edit_lab")
    builder.button(text=_("Удалить"), callback_data="delete_lab")
    builder.button(text=_("Сгенерировать подсказку"), callback_data="use_ai")
    builder.button(text=_("Назад"), callback_data="back_to_lab_menu")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_lab():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Да"), callback_data="confirm_deleting_lab")
    builder.button(text=_("Нет"), callback_data="cancel_deleting_lab")
    builder.adjust(1)
    return builder.as_markup()


def lab_edit_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Изменить дисциплину"), callback_data="edit_lab_discipline")
    builder.button(text=_("Изменить название"), callback_data="edit_lab_name")
    builder.button(text=_("Изменить текст"), callback_data="edit_lab_description")
    builder.button(text=_("Изменить файлы"), callback_data="edit_lab_files")
    builder.button(text=_("Изменить ссылку"), callback_data="edit_lab_link")
    builder.button(text=_("Изменить доп. информацию"), callback_data="edit_lab_additional_info")
    builder.button(text=_("Изменить дату начала"), callback_data="edit_lab_start_date")
    builder.button(text=_("Изменить срок сдачи"), callback_data="edit_lab_end_date")
    builder.button(text=_("Назад"), callback_data="back_to_chosen_lab_menu")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def use_text_in_ai():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Использовать текущий текст задания"), callback_data="use_current_text")
    builder.button(text=_("Ввести новый текст задания"), callback_data="use_new_text")
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


def list_show_option():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("По статусу"), callback_data="lab_list_status")
    builder.button(text=_("По дисциплине"), callback_data="lab_list_discipline")
    builder.button(text=_("На 7 дней"), callback_data="lab_list_week")
    builder.adjust(1)
    return builder.as_markup()


def status_option():
    builder = InlineKeyboardBuilder()

    for status in Status:
        builder.button(
            text=str(status.value),
            callback_data=f"lab_status_{status.name}"
        )
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


def cancel_editing_attr():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Отмена"), callback_data="cancel_editing_attr_discipline")
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

    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    _, num_days = monthrange(year, month)
    first_day = date(year, month, 1)
    starting_weekday = first_day.weekday()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(text="<<", callback_data=f"calendar_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{MONTH_NAMES[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">>", callback_data=f"calendar_next_{year}_{month}")
    ])

    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="ignore") for day in DAY_SHORT_NAMES
    ])

    row = []
    for _ in range(starting_weekday):
        row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"calendar_date_{date_str}"))
        if len(row) == 7:
            keyboard.append(row)
            row = []

    if row:
        for cell in range(7 - len(row)):
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        keyboard.append(row)

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


# def back_to_options_button():
#     builder = InlineKeyboardBuilder()
#
#     builder.button(text=_("Назад"), callback_data="back_to_options")
#     builder.adjust(1)
#     return builder.as_markup()


def labs_list(labs, disciplines_dict, show_abb, page: int = 0, items_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_labs = labs[start_idx:end_idx]

    builder.button(text=_("Назад"), callback_data="back_to_options")

    for i, lab in enumerate(current_page_labs, start=start_idx):
        if show_abb:
            builder.button(text=_("{abb} - {date} - {lab}"
                                  .format(abb=generate_abbreviation(disciplines_dict[lab["discipline_id"]]),
                                          date=datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y"),
                                          lab=labs[i]["name"])),
                           callback_data=f'lab_index_{lab["task_id"]}'
                           )
        else:
            builder.button(text=_("{date} - {lab}".format(
                lab=labs[i]["name"],
                date=datetime.strptime(lab["end_date"], "%Y-%m-%d").strftime("%d.%m.%Y"),
            )),
                callback_data=f'lab_index_{lab["task_id"]}'
            )

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            back_l_list(page)
        )

    if end_idx < len(labs):
        navigation_buttons.append(
            continue_l_list(page)
        )

    builder.adjust(1)
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def back_l_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"lab_page_{page - 1}")


def continue_l_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"lab_page_{page + 1}")
