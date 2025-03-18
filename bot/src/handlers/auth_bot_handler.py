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


class AuthStates(StatesGroup):
    waiting_for_group = State()


async def add_user_to_db(state):
    user_data = await state.get_data()
    tg_id = user_data.get("tg_id")
    is_petrsu_student = user_data.get("is_petrsu_student")
    group = user_data.get("group")
    url_req = f"{settings.API_URL}/add_user"
    response = requests.post(url_req, json={"telegram_id": tg_id,
                                            "is_petrsu_student": is_petrsu_student,
                                            "group": group})
    return response.status_code


@router.callback_query(F.data == "send_tg_id")
async def get_is_petrsu(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        _("Вы являетесь студентом ПетрГУ?"),
        reply_markup=kb.is_petrsu_student(),
    )


@router.callback_query(F.data == "petrsu_true")
async def is_petrsu(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_petrsu_student=True)
    await callback_query.message.answer(
        _("Введите номер группы.")
    )
    await state.set_state(AuthStates.waiting_for_group)


@router.message(AuthStates.waiting_for_group)
async def get_group(message: Message, state: FSMContext):
    group = message.text
    url_req = "https://petrsu.egipti.com/api/v2/groups"
    response = requests.get(url_req)
    if response.status_code == 200:
        petrsu_groups = response.json()
        if group in petrsu_groups.keys():
            await state.update_data(group=group)
            response_status = await add_user_to_db(state)
            if response_status == 200:
                await message.answer(
                    _("Добро пожаловать! Ваша группа {group}.").format(group=group)
                )
                await main_bot_handler.start_dialog(message, state, message.from_user.id)
                await state.clear()
            else:
                await message.answer(
                    _("Ошибка регистрации. Сервер недоступен. Ошибка {response_status}.").format(response_status=response_status)
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


@router.callback_query(F.data == "petrsu_false")
async def is_not_petrsu(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(is_petrsu_student=False)
    await state.update_data(group="")
    response_status = await add_user_to_db(state)
    if response_status == 200:
        await callback_query.message.answer(
            _("Добро пожаловать!")
        )
        await main_bot_handler.start_dialog(callback_query.message, state, callback_query.from_user.id)
        await state.clear()
    else:
        await callback_query.message.answer(
            _("Ошибка регистрации. Сервер недоступен. Ошибка {response_status}.").format(response_status=response_status)
        )