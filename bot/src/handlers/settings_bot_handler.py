import requests

from aiogram import Router, F
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.auth_keyboard as kb
from ..settings import settings

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_new_group = State()


@router.callback_query(F.data == "change_group")
async def is_petrsu(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_petrsu_student=True)
    await callback_query.message.answer(
        _("Введите новый номер группы.")
    )
    await state.set_state(SettingsStates.waiting_for_group)


@router.message(or_f(StateFilter(SettingsStates.waiting_for_group), StateFilter(SettingsStates.waiting_for_new_group)))
async def change_group(message: Message, state: FSMContext):
    user_data = await state.get_data()
    telegram_id = user_data.get("telegram_id")
    group = message.text
    url_req = "https://petrsu.egipti.com/api/v2/groups"
    response = requests.get(url_req)
    if response.status_code == 200:
        petrsu_groups = response.json()
        if group in petrsu_groups.keys():
            await state.update_data(group=group)
            if await state.get_state() == SettingsStates.waiting_for_group:
                url_req = f"{settings.API_URL}/change_user_group"
                response = requests.post(url_req, json={"telegram_id": telegram_id,
                                                        "group": group})
                if response.status_code == 200:
                    await message.answer(
                        _("Вы успешно изменили группу на {group}.").format(group=group)
                    )
                    await main_bot_handler.open_settings_menu(message, state, telegram_id)
                else:
                    await message.answer(
                        _("Ошибка изменения группы. Сервер недоступен. Ошибка {response_status}.").format(
                            response_status=response.status_code)
                    )
            elif await state.get_state() == SettingsStates.waiting_for_new_group:
                url_req = f"{settings.API_URL}/change_user_status"
                response = requests.post(url_req,
                                         json={"is_petrsu_student": True, "telegram_id": telegram_id, "group": group})
                if response.status_code == 200:
                    await message.answer(
                        _("Ваша группа: {group}").format(group=group)
                    )
                    await main_bot_handler.open_settings_menu(message, state, telegram_id)
        else:
            await message.answer(
                _("Данная группа не найдена в ПетрГУ, повторите ввод.")
            )
            return
    else:
        await message.answer(
            _("Сервер ПетрГУ в данный момент недоступен. Зарегистрируйтесь без статуса студента ПетрГУ."
              "Вы можете сменить статус студента в настройках. Ошибка {status}.").format(status=response.status_code)
        )


@router.callback_query(F.data == "change_petrsu_status")
async def is_petrsu(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    telegram_id = user_data.get("telegram_id")
    url_req = f"{settings.API_URL}/check_is_petrsu_student"
    response = requests.get(url_req, json={"telegram_id": telegram_id})
    response_data = response.json()
    if response_data.get("is_petrsu_student", True):
        url_req = f"{settings.API_URL}/change_user_status"
        response = requests.post(url_req, json={"is_petrsu_student": False, "telegram_id": telegram_id, "group": ""})
        if response.status_code == 200:
            await callback_query.message.answer(
                _("Вы больше не являетесь студентом ПетрГУ.")
            )
            await main_bot_handler.open_settings_menu(callback_query.message, state, telegram_id)
        else:
            await callback_query.message.answer(
                _("Ошибка изменения статуса. Сервер недоступен. Ошибка {response_status}.").format(
                    response_status=response.status_code)
            )
    else:
        await callback_query.message.answer(
            _("Теперь Вы являетесь студентом ПетрГУ. Укажите номер группы.")
        )
        await state.set_state(SettingsStates.waiting_for_new_group)
