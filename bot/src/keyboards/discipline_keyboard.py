from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def add_discipline_confirm(is_from_api):
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_discipline")
    builder.button(text=_("Нет"), callback_data="cancel_add_discipline")
    if not is_from_api:
        builder.button(text=_("Изменить название"), callback_data="change_discipline_name")
    builder.button(text=_("Изменить преподавателя"), callback_data="change_discipline_teacher")
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
        builder.button(text=_("{discipline}".format(discipline=disciplines[i])), callback_data=f"discipline_index_{i}"
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


def lecturers_list(lecturers, page: int = 0, items_per_page: int = 5, state: str = None):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_lecturers = lecturers[start_idx:end_idx]

    print(state)
    if state is None:
        builder.button(text=_("Отмена"), callback_data="cancel_editing_attr_discipline")
    else:
        builder.button(text=_("Пропустить"), callback_data="skip_disciplines_lecturer")
    for i, lecturer in enumerate(current_page_lecturers, start=start_idx):
        builder.button(text=_("{lecturer}".format(lecturer=lecturers[i])), callback_data=f"disciplines_lecturer_index_{i}"
    )

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            back_t_list(page)
        )

    if end_idx < len(lecturers):
        navigation_buttons.append(
            continue_t_list(page)
        )

    builder.adjust(1)
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def back_t_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"disciplines_lecturers_page_{page - 1}")


def continue_t_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"disciplines_lecturers_page_{page + 1}")


def back_d_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"disciplines_page_{page - 1}")


def continue_d_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"disciplines_page_{page + 1}")


