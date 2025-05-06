import io

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile
from aiogram.utils import i18n

from ..settings import settings
import requests
import json

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

import bot.src.keyboards.menu_keyboard as kb
import bot.src.keyboards.auth_keyboard as kb_auth
import bot.src.keyboards.diagrams_keyboard as kb_diag
import bot.src.keyboards.settings_keyboard as kb_settings
from bot.src.handlers.diagrams_bot_handler import create_kanban, create_kanban_2

from bot.src.bot_unit import bot as bot_unit

router = Router()


@router.message(CommandStart())
async def start_dialog(message: Message, state: FSMContext, telegram_id: int = None):

    if telegram_id is not None:
        current_user_tg_id = telegram_id
    else:
        current_user_tg_id = message.from_user.id

    url_req = f"{settings.API_URL}/check_user"
    response = requests.get(url_req, json={"telegram_id": str(current_user_tg_id)})
    response_data = response.json()
    if response_data.get("exists", True):
        url_req = f"{settings.API_URL}/check_is_petrsu_student"
        response = requests.get(url_req, json={"telegram_id": str(current_user_tg_id)})
        response_data = response.json()
        if response_data.get("is_petrsu_student", True):
            if telegram_id is None:
                await message.answer(
                    _("Добро пожаловать! Ваша группа {group}.").format(group=response_data.get("group"))
                )
            await message.answer(
                _("Вы находитесь в главном меню."),
                reply_markup=kb.main_menu_keyboard(),
            )
        else:
            if telegram_id is None:
                await message.answer(
                    _("Добро пожаловать!")
                )
            await message.answer(
                _("Вы находитесь в главном меню."),
                reply_markup=kb.main_menu_keyboard(),
            )
    else:
        await state.update_data(tg_id=str(current_user_tg_id))
        await message.answer(
            _("Подтвердите, пожалуйста, отправку Telegram ID для регистрации."),
            reply_markup=kb_auth.send_tg_id(),
        )


@router.message(F.text == __("⬅ Назад"))
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    try:
        await message.edit_reply_markup(
            reply_markup=None
        )
        await message.answer(
            _("Вы находитесь в главном меню."),
            reply_markup=kb.main_menu_keyboard(),
        )
    except:
        await message.answer(
            _("Вы находитесь в главном меню."),
            reply_markup=kb.main_menu_keyboard(),
        )


@router.message(F.text == __("Лабораторные работы"))
async def open_labs_menu(message: Message, state: FSMContext, telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    await message.answer(
        _("Вы находитесь в меню лабораторных работ."),
        reply_markup=kb.labs_menu_keyboard(),
    )


@router.message(F.text == __("Диаграмма Ганта"))
async def open_gant_menu(message: Message, state: FSMContext, telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    url_req = f"{settings.API_URL}/check_is_petrsu_student"
    response = requests.get(url_req, json={"telegram_id": str(telegram_id)})
    response_data = response.json()
    if response.status_code == 200:
        if response_data.get("is_petrsu_student", True):
            url_req = f"{settings.API_URL}/get_user_group"
            response = requests.get(url_req, json={"telegram_id": telegram_id})
            if response.status_code == 200:
                group = response.json().get("group")
                url_req = "https://petrsu.egipti.com/api/v2/schedule/{group}".format(group=group)
                response = requests.get(url_req)
                if response.status_code == 200:
                    response_data = response.json()
                    await state.update_data(schedule_data=response_data)
                    await message.answer(
                        _("Выберите период для диаграммы Ганта."),
                        reply_markup=kb_diag.choose_gant_diagram(),
                    )
                else:
                    await message.answer(json.loads(response.text).get('detail'))
            else:
                await message.answer(json.loads(response.text).get('detail'))
        else:
            await message.answer(
                _("Выберите период для диаграммы Ганта."),
                reply_markup=kb_diag.choose_gant_diagram(),
            )
    else:
        await message.answer(json.loads(response.text).get('detail'))



@router.message(F.text == __("Канбан-доска"))
async def open_gant_menu(message: Message, state: FSMContext, telegram_id: int = None, bot: Bot = bot_unit):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": telegram_id})
    if response.status_code == 200:
        user_id = response.json().get("user_id")
        await state.update_data(user_id=user_id)
        url_req = f"{settings.API_URL}/get_labs"
        response = requests.get(url_req, json={"user_id": user_id})
        if response.status_code == 200:
            response_data = response.json()
            await state.update_data(labs_response=response_data)

            url_req = f"{settings.API_URL}/get_disciplines"
            response = requests.get(url_req, json={"user_id": user_id})

            if response.status_code == 200:
                disciplines = response.json().get("disciplines", [])
                sorted_disciplines = sorted(disciplines, key=lambda x: x["name"])
                disciplines_dict = {d["discipline_id"]: d["name"] for d in sorted_disciplines}
                await state.update_data(disciplines_dict=disciplines_dict)
                await state.update_data(disciplines=list(disciplines_dict.values()))
                await state.update_data(disciplines_id=list(disciplines_dict.keys()))
                state_data = await state.get_data()
                # await create_kanban(state_data)
                try:
                    plt, fig = await create_kanban_2(state_data)

                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.5)
                    plt.close(fig)

                    photo = BufferedInputFile(
                        file=buf.getvalue(),
                        filename="kanban_desk.png"
                    )
                    await bot.send_photo(chat_id=message.chat.id, photo=photo)
                    await bot.send_document(chat_id=message.chat.id, document=photo)
                    buf.close()
                except Exception as e:
                    print(e)
                    await message.answer(
                        _("У Вас не добавлено ни одного задания.")
                    )


@router.message(F.text == __("Дисциплины"))
async def open_discipline_menu(message: Message, state: FSMContext, telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    url_req = f"{settings.API_URL}/check_is_petrsu_student"
    response = requests.get(url_req, json={"telegram_id": str(telegram_id)})
    response_data = response.json()
    if response.status_code == 200:
        if response_data.get("is_petrsu_student", True):
            url_req = f"{settings.API_URL}/get_user_group"
            response = requests.get(url_req, json={"telegram_id": telegram_id})
            if response.status_code == 200:
                group = response.json().get("group")
                url_req = "https://petrsu.egipti.com/api/v2/schedule/{group}".format(group=group)
                response = requests.get(url_req)
                if response.status_code == 200:
                    response_data = response.json()
                    await state.update_data(schedule_data=response_data)
                    await message.answer(
                        _("Вы находитесь в меню дисциплин."),
                        reply_markup=kb.discipline_menu_keyboard(),
                    )
                else:
                    await message.answer(json.loads(response.text).get('detail'))
            else:
                await message.answer(json.loads(response.text).get('detail'))
        else:
            await message.answer(
                _("Вы находитесь в меню дисциплин."),
                reply_markup=kb.discipline_menu_keyboard(),
            )
    else:
        await message.answer(json.loads(response.text).get('detail'))


@router.message(F.text == __("Преподаватели"))
async def open_teacher_menu(message: Message, state: FSMContext, telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    await message.answer(
        _("Вы находитесь в меню преподавателей."),
        reply_markup=kb.teacher_menu_keyboard(),
    )


@router.message(F.text == __("Пары"))
async def open_lesson_menu(message: Message, state: FSMContext, telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    await message.answer(
        _("Вы находитесь в меню занятий."),
        reply_markup=kb.lesson_menu_keyboard(),
    )


@router.message(F.text == __("Настройки"))
async def open_settings_menu(message: Message, state: FSMContext,  telegram_id: int = None):
    await state.clear()
    if telegram_id is None:
        telegram_id = str(message.from_user.id)
    await state.update_data(telegram_id=telegram_id)
    url_req = f"{settings.API_URL}/check_is_petrsu_student"
    response = requests.get(url_req, json={"telegram_id": telegram_id})
    response_data = response.json()
    if response_data.get("is_petrsu_student", True):
        await message.answer(
            _("Вы находитесь в разделе пользовательских настроек.\n\nВы являетесь студентом ПетрГУ.\n"
              "Группа: {group}").format(group=response_data.get("group")),
            reply_markup=kb_settings.settings_menu_keyboard(response_data.get("is_petrsu_student")),
        )
    else:
        await message.answer(
            _("Вы находитесь в разделе пользовательских настроек.\n\nВы не являетесь студентом ПетрГУ."),
            reply_markup=kb_settings.settings_menu_keyboard(response_data.get("is_petrsu_student")),
        )