from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def add_teacher_confirm(is_from_api):
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_teacher")
    builder.button(text=_("Нет"), callback_data="cancel_add_teacher")
    if not is_from_api:
        builder.button(text=_("Изменить ФИО"), callback_data="change_teacher_fio")
    builder.button(text=_("Изменить номер телефона"), callback_data="change_teacher_phone")
    builder.button(text=_("Изменить почту"), callback_data="change_teacher_email")
    builder.button(text=_("Изменить социальную сеть"), callback_data="change_teacher_link")
    builder.button(text=_("Изменить аудиторию"), callback_data="change_teacher_classroom")
    builder.adjust(1)
    return builder.as_markup()


def skip_button():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Пропустить"), callback_data="skip")
    builder.adjust(1)
    return builder.as_markup()


def add_option():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Показать список"), callback_data="show_teacher_api_list")
    builder.button(text=_("Ввести вручную"), callback_data="add_by_hand")
    builder.adjust(1)
    return builder.as_markup()


def lecturers_list(lecturers, page: int = 0, items_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_lecturers = lecturers[start_idx:end_idx]

    for i, lecturer in enumerate(current_page_lecturers, start=start_idx):
        builder.button(text=_("{lecturer}".format(lecturer=lecturers[i])), callback_data=f"lecturer_index_{i}"
    )

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            back_list(page)
        )

    if end_idx < len(lecturers):
        navigation_buttons.append(
            continue_list(page)
        )

    builder.adjust(1)
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def back_list(page):
    return InlineKeyboardButton(text=_("⬅"), callback_data=f"lecturers_page_{page - 1}")


def continue_list(page):
    return InlineKeyboardButton(text=_("➡"), callback_data=f"lecturers_page_{page + 1}")


def teacher_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Изменить"), callback_data="edit_teacher")
    builder.button(text=_("Удалить"), callback_data="delete_teacher")
    builder.adjust(1)
    return builder.as_markup()


def edit_options(is_from_api):
    builder = InlineKeyboardBuilder()
    if not is_from_api:
        builder.button(text=_("Изменить ФИО"), callback_data="edit_teacher_fio")
    builder.button(text=_("Изменить номер телефона"), callback_data="edit_teacher_phone")
    builder.button(text=_("Изменить почту"), callback_data="edit_teacher_email")
    builder.button(text=_("Изменить социальную сеть"), callback_data="edit_teacher_link")
    builder.button(text=_("Изменить аудиторию"), callback_data="edit_teacher_classroom")
    builder.button(text=_("Отмена"), callback_data="cancel_editing")
    builder.adjust(1)
    return builder.as_markup()
