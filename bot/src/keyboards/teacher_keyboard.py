from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def add_teacher_confirm():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Да"), callback_data="add_teacher")
    builder.button(text=_("Нет"), callback_data="cancel_add_teacher")
    builder.button(text=_("Изменить ФИО"), callback_data="change_teacher_fio")
    builder.button(text=_("Изменить номер телефона"), callback_data="change_teacher_phone")
    builder.button(text=_("Изменить почту"), callback_data="change_teacher_email")
    builder.button(text=_("Изменить социальную сеть"), callback_data="change_teacher_link")
    builder.button(text=_("Изменить аудиторию"), callback_data="change_teacher_classroom")
    builder.adjust(1)
    return builder.as_markup()

