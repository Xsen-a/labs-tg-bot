import requests

from aiogram import Router, F
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


@router.callback_query(F.data == "change_group")
async def is_petrsu(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_petrsu_student=True)
    await callback_query.message.answer(
        _("Введите новый номер группы.")
    )
    await state.set_state(SettingsStates.waiting_for_group)


@router.message(SettingsStates.waiting_for_group)
async def get_group(message: Message, state: FSMContext):
    group = message.text
    url_req = "https://petrsu.egipti.com/api/v2/groups"
    response = requests.get(url_req)
    if response.status_code == 200:
        petrsu_groups = response.json()
        if group in petrsu_groups.keys():
            await state.update_data(group=group)
            user_data = await state.get_data()
            telegram_id = user_data.get("telegram_id")
            url_req = f"{settings.API_URL}/change_user_group"
            response = requests.post(url_req, json={"telegram_id": telegram_id,
                                                    "group": group})
            if response.status_code == 200:
                await message.answer(
                    _("Вы успешно изменили группу на {group}.").format(group=group)
                )
                await main_bot_handler.open_settings_menu(message, state, telegram_id)
                await state.clear()
            else:
                await message.answer(
                    _("Ошибка регистрации. Сервер недоступен. Ошибка {response_status}.").format(response_status=response.status_code)
                )
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