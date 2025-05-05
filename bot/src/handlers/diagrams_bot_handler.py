import base64
import calendar
import io
import re
import json

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import datetime
import numpy as np
from textwrap import wrap
from matplotlib.backends.backend_pdf import PdfPages

import requests
from datetime import datetime, timedelta

from aiogram import Router, F, Bot, types
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from matplotlib.gridspec import GridSpec

from bot.src.handlers import main_bot_handler
import bot.src.keyboards.diagrams_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit

router = Router()


def round_to_2weeks(dt):
    # Преобразуем в datetime если это строка
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%d')

    # Вычисляем сколько дней нужно добавить для округления
    days_since_epoch = (dt - datetime(1970, 1, 1)).days
    remainder = days_since_epoch % 14
    if remainder == 0:
        return dt
    else:
        return dt + timedelta(days=(14 - remainder))


def filter_labs_by_month(labs_data, year, month):
    filtered_labs = []
    year = int(year)
    month = int(month)
    # Определяем границы месяца
    first_day = datetime(year=year, month=month, day=1)
    if month == 12:
        last_day = datetime(year=year + 1, month=1, day=1)
    else:
        last_day = datetime(year=year, month=month + 1, day=1)

    for lab in labs_data['labs_response']['labs']:
        start_date = datetime.strptime(lab['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(lab['end_date'], '%Y-%m-%d')

        # Проверяем пересечение с выбранным месяцем
        if (start_date < last_day) and (end_date >= first_day):
            filtered_labs.append(lab)
        # if lab["status"] != 'Сдано':
        #     filtered_labs.append(lab)

    return filtered_labs


async def create_diagram_full(data):
    # Преобразуем данные лабораторных работ
    labs = data['labs_response']['labs']
    disciplines_dict = data['disciplines_dict']

    # Группируем лабораторные по дисциплинам
    disciplines_labs = {}
    for lab in labs:
        discipline_id = lab['discipline_id']
        if discipline_id not in disciplines_labs:
            disciplines_labs[discipline_id] = []
        disciplines_labs[discipline_id].append(lab)

    # Сортируем дисциплины от новых к старым
    sorted_disciplines = sorted(disciplines_labs.items(),
                                key=lambda x: min(lab['start_date'] for lab in x[1]))

    # Цвета для статусов
    status_colors = {
        'Не начато': '#dedede',
        'В процессе': '#66e3ff',
        'Готово к сдаче': '#ddb3fc',
        'Сдано': '#66ff87'
    }

    plt.rcParams.update({
        'font.family': 'DejaVu Sans',  # Хороший шрифт с поддержкой кириллицы
        'axes.titlesize': 12,
        'font.weight': 'bold'
    })

    # Создаем фигуру с адаптивной высотой
    total_labs = sum(len(labs) for labs in disciplines_labs.values())
    fig_height = max(6, total_labs * 0.4)  # Увеличили множитель для лучшего отображения
    fig, ax = plt.subplots(figsize=(15, fig_height))

    # Собираем все задачи в правильном порядке (сверху - старые, снизу - новые)
    all_items = []  # Может быть либо дисциплиной, либо лабораторной
    y_labels = []

    for discipline_id, lab_list in sorted_disciplines:
        discipline_name = disciplines_dict.get(discipline_id, f"Дисциплина {discipline_id}")

        # Сортируем лабораторные внутри дисциплины от старых к новым
        lab_list.sort(key=lambda x: x['start_date'])

        # Добавляем название дисциплины ПЕРЕД лабораторными
        y_labels.append(discipline_name)
        all_items.append({'type': 'discipline'})

        # Затем добавляем лабораторные
        for lab in lab_list:
            y_labels.append(lab['name'])
            all_items.append({'type': 'lab', 'data': lab})

        # Добавляем пустую строку после дисциплины
        all_items.append({'type': 'empty'})
        y_labels.append("")

    print(all_items)
    if len(all_items) == 0:
        return

    # Фильтруем только лабораторные для построения графиков
    lab_tasks = [item['data'] for item in all_items if item['type'] == 'lab']

    # Преобразуем даты только для лабораторных
    start_dates_num = [mdates.datestr2num(lab['start_date']) for lab in lab_tasks]
    end_dates_num = [mdates.datestr2num(lab['end_date']) for lab in lab_tasks]
    durations = [end - start for start, end in zip(start_dates_num, end_dates_num)]
    statuses = [lab['status'] for lab in lab_tasks]

    # Позиции по оси Y (сверху вниз)
    y_pos = np.arange(len(all_items)) * 1

    # Рисуем полосы только для лабораторных
    bar_height = 0.7
    lab_index = 0
    deadline_num = 0
    for i, item in enumerate(all_items):
        if item['type'] == 'lab':
            start = start_dates_num[lab_index]
            duration = durations[lab_index]
            status = statuses[lab_index]
            ax.barh(y_pos[i], duration, left=start, height=bar_height,
                    color=status_colors.get(status),
                    edgecolor='black', linewidth=0.5)
            if item['data']['status'] != 'Сдано':
                deadline = datetime.strptime(item['data']['end_date'], '%Y-%m-%d')
                if deadline < datetime.now():
                    ax.barh(y_pos[i], datetime.now() - deadline, left=deadline, height=bar_height,
                            color='#FFCCCC', linestyle="--", alpha=0.7,
                            edgecolor='red', linewidth=0.5)
                deadline_num += 1
            lab_index += 1

    # Настраиваем подписи
    ax.set_yticks(y_pos)
    labels = ax.set_yticklabels(y_labels, ha='right', position=(-0.1, 0), fontsize=10)

    discipline_names = set(disciplines_dict.values())
    for i, label in enumerate(labels):
        text = label.get_text()
        if text in discipline_names:
            label.set_fontweight('bold')
            label.set_fontsize(12)
        else:
            label.set_fontweight('normal')  # Явно убираем жирный для остальных
            label.set_fontsize(10)

    # Настраиваем оси и даты
    ax.set_ylim(len(all_items) - 0.5, -0.5)

    # Для минимальной даты (точно 03.02)
    min_date = min(lab['start_date'] for lab in lab_tasks)
    min_date_dt = datetime.strptime(min_date, '%Y-%m-%d')
    min_date_num = mdates.date2num(min_date_dt)

    max_date_dt = max(datetime.strptime(lab['end_date'], '%Y-%m-%d') for lab in lab_tasks)
    today_dt = datetime.now()
    max_date = max(max_date_dt, today_dt).strftime('%Y-%m-%d')  # Получаем строку
    rounded_max_date = round_to_2weeks(max_date)
    print(rounded_max_date)
    max_date_num = mdates.date2num(rounded_max_date)

    # Устанавливаем границы с минимальным смещением
    ax.set_xlim(min_date_num - 0.001, max_date_num + 0.001)

    # Настраиваем локатор дат (главное исправление)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))  # Каждые 2 недели
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))  # Формат без года

    ax.set_xticks(list(ax.get_xticks()) + [min_date_num])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.xaxis.tick_top()  # Даты сверху
    for label in ax.get_xticklabels():
        label.set_fontweight('normal')  # Обычный шрифт

    # Красная линия текущей даты
    ax.axvline(x=mdates.date2num(datetime.now()), color='red', linestyle='--', linewidth=1.5)

    # Сетка
    ax.grid(True, axis='x', linestyle=':', alpha=0.5)

    # Убираем лишние рамки
    for spine in ['left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

    # Легенда
    legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=color, label=status)
                       for status, color in status_colors.items()]
    legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc='#FFCCCC', label=f"Просроченные задания: {deadline_num}",
                                         linestyle="--", edgecolor='red', linewidth=0.5))
    legend = ax.legend(handles=legend_elements,
                       loc='upper left',
                       bbox_to_anchor=(1, 1),
                       fontsize=9)
    legend.set_title('Статусы', prop={'weight': 'normal'})  # Заголовок легенды
    for text in legend.get_texts():
        text.set_fontweight('normal')  # Текст в легенде

    plt.tight_layout()
    plt.subplots_adjust(left=0.3, right=0.85, top=0.95, bottom=0.05)
    # Увеличиваем размер фигуры перед сохранением
    fig.set_size_inches(15, total_labs * 0.5)  # Подбирайте высоту под ваш случай

    # # Сохраняем в файл с высоким DPI
    # plt.savefig('график_лабораторных.png',
    #             dpi=300,
    #             bbox_inches='tight',
    #             pad_inches=0.5)
    #
    # # Показываем сообщение о сохранении
    # print("График сохранен в файл 'график_лабораторных.png'")
    #
    # with PdfPages('all_labs.pdf') as pdf:
    #     pdf.savefig(fig, bbox_inches='tight')
    #
    # plt.show()
    return plt, fig


async def create_diagram_month(labs, disciplines_dict, month, year):
    month = int(month)
    year = int(year)

    # Группируем лабораторные по дисциплинам
    disciplines_labs = {}
    for lab in labs:
        discipline_id = lab['discipline_id']
        if discipline_id not in disciplines_labs:
            disciplines_labs[discipline_id] = []
        disciplines_labs[discipline_id].append(lab)

    # Сортируем дисциплины от новых к старым
    sorted_disciplines = sorted(disciplines_labs.items(),
                                key=lambda x: min(lab['start_date'] for lab in x[1]))

    # Цвета для статусов
    status_colors = {
        'Не начато': '#dedede',
        'В процессе': '#66e3ff',
        'Готово к сдаче': '#ddb3fc',
        'Сдано': '#66ff87'
    }

    plt.rcParams.update({
        'font.family': 'DejaVu Sans',  # Хороший шрифт с поддержкой кириллицы
        'axes.titlesize': 12,
        'font.weight': 'bold'
    })

    # Создаем фигуру с адаптивной высотой
    total_labs = sum(len(labs) for labs in disciplines_labs.values())
    fig_height = max(6, total_labs * 0.4)  # Увеличили множитель для лучшего отображения
    fig, ax = plt.subplots(figsize=(15, fig_height))

    # Собираем все задачи в правильном порядке (сверху - старые, снизу - новые)
    all_items = []  # Может быть либо дисциплиной, либо лабораторной
    y_labels = []

    for discipline_id, lab_list in sorted_disciplines:
        discipline_name = disciplines_dict.get(discipline_id, f"Дисциплина {discipline_id}")

        # Сортируем лабораторные внутри дисциплины от старых к новым
        lab_list.sort(key=lambda x: x['start_date'])

        # Добавляем название дисциплины ПЕРЕД лабораторными
        y_labels.append(discipline_name)
        all_items.append({'type': 'discipline'})

        # Затем добавляем лабораторные
        for lab in lab_list:
            y_labels.append(lab['name'])
            all_items.append({'type': 'lab', 'data': lab})

        # Добавляем пустую строку после дисциплины
        all_items.append({'type': 'empty'})
        y_labels.append("")

    print(all_items)
    if len(all_items) == 0:
        return

    # Фильтруем только лабораторные для построения графиков
    lab_tasks = [item['data'] for item in all_items if item['type'] == 'lab']

    # Преобразуем даты только для лабораторных
    start_dates_num = [mdates.datestr2num(lab['start_date']) for lab in lab_tasks]
    end_dates_num = [mdates.datestr2num(lab['end_date']) for lab in lab_tasks]
    durations = [end - start for start, end in zip(start_dates_num, end_dates_num)]
    statuses = [lab['status'] for lab in lab_tasks]

    # Позиции по оси Y (сверху вниз)
    y_pos = np.arange(len(all_items)) * 1

    # Рисуем полосы только для лабораторных
    bar_height = 0.7
    lab_index = 0
    deadline_num = 0
    for i, item in enumerate(all_items):
        if item['type'] == 'lab':
            start = start_dates_num[lab_index]
            duration = durations[lab_index]
            status = statuses[lab_index]
            ax.barh(y_pos[i], duration, left=start, height=bar_height,
                    color=status_colors.get(status),
                    edgecolor='black', linewidth=0.5)
            if item['data']['status'] != 'Сдано':
                deadline = datetime.strptime(item['data']['end_date'], '%Y-%m-%d')
                if deadline < datetime.now():
                    ax.barh(y_pos[i], datetime(day=calendar.monthrange(year, month)[1], month=month, year=year) - deadline, left=deadline, height=bar_height,
                            color='#FFCCCC', linestyle="--", alpha=0.7,
                            edgecolor='red', linewidth=0.5)
                deadline_num += 1
            lab_index += 1

    # Настраиваем подписи
    ax.set_yticks(y_pos)
    labels = ax.set_yticklabels(y_labels, ha='right', position=(-0.1, 0), fontsize=10)

    discipline_names = set(disciplines_dict.values())
    for i, label in enumerate(labels):
        text = label.get_text()
        if text in discipline_names:
            label.set_fontweight('bold')
            label.set_fontsize(12)
        else:
            label.set_fontweight('normal')  # Явно убираем жирный для остальных
            label.set_fontsize(10)

    # Настраиваем оси и даты
    ax.set_ylim(len(all_items) - 0.5, -0.5)

    # Для минимальной даты
    min_date_dt = datetime(day=1, month=month, year=year)
    min_date_num = mdates.date2num(min_date_dt)

    max_date_dt = datetime(day=calendar.monthrange(year, month)[1], month=month, year=year)
    max_date_num = mdates.date2num(max_date_dt)

    # Устанавливаем границы с минимальным смещением
    ax.set_xlim(min_date_num - 0.001, max_date_num + 0.001)

    # Настраиваем локатор дат (главное исправление)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.set_xticks(list(ax.get_xticks()) + [min_date_num, max_date_num])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.xaxis.tick_top()  # Даты сверху
    for label in ax.get_xticklabels():
        label.set_fontweight('normal')  # Обычный шрифт

    # Красная линия текущей даты
    ax.axvline(x=mdates.date2num(datetime.now()), color='red', linestyle='--', linewidth=1.5)

    # Сетка
    ax.grid(True, axis='x', linestyle=':', alpha=0.5)

    # Убираем лишние рамки
    for spine in ['left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

    # Легенда
    legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=color, label=status)
                       for status, color in status_colors.items()]
    if deadline_num != 0:
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc='#FFCCCC', label=f"Просроченные задания: {deadline_num}",
                                         linestyle="--", edgecolor='red', linewidth=0.5))
    legend = ax.legend(handles=legend_elements,
                       loc='upper left',
                       bbox_to_anchor=(1, 1),
                       fontsize=9)
    legend.set_title('Статусы', prop={'weight': 'normal'})  # Заголовок легенды
    for text in legend.get_texts():
        text.set_fontweight('normal')  # Текст в легенде

    plt.tight_layout()
    plt.subplots_adjust(left=0.3, right=0.85, top=0.95, bottom=0.05)
    # Увеличиваем размер фигуры перед сохранением
    fig.set_size_inches(15, total_labs * 0.5)  # Подбирайте высоту под ваш случай

    # # Сохраняем в файл с высоким DPI
    # plt.savefig('график_лабораторных.png',
    #             dpi=300,
    #             bbox_inches='tight',
    #             pad_inches=0.5)
    #
    # # Показываем сообщение о сохранении
    # print("График сохранен в файл 'график_лабораторных.png'")
    #
    # with PdfPages('all_labs.pdf') as pdf:
    #     pdf.savefig(fig, bbox_inches='tight')
    #
    # plt.show()
    return plt, fig


@router.callback_query(F.data == "gant_full")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

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
                try:
                    plt, fig = await create_diagram_full(state_data)

                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.5)
                    plt.close(fig)

                    photo = BufferedInputFile(
                        file=buf.getvalue(),  # Используем getvalue() вместо read()
                        filename="gantt_chart.png"
                    )
                    await bot.send_photo(chat_id=callback_query.message.chat.id, photo=photo)
                    await bot.send_document(chat_id=callback_query.message.chat.id, document=photo)
                    buf.close()
                except Exception as e:
                    print(e)
                    await callback_query.message.answer(
                        _("У Вас не добавлено ни одного задания.")
                    )

        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data == "gant_month")
async def back_to_list(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
    await callback_query.answer()
    state_data = await state.get_data()
    url_req = f"{settings.API_URL}/get_user_id"
    response = requests.get(url_req, json={"telegram_id": state_data.get("telegram_id")})

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
                print(state_data)
                months_used = set()
                for lab in state_data["labs_response"]["labs"]:
                    date_obj = datetime.strptime(lab["start_date"], '%Y-%m-%d')
                    month_year = (date_obj.month, date_obj.year)  # Кортеж (месяц, год)
                    months_used.add(month_year)
                    date_obj = datetime.strptime(lab["end_date"], '%Y-%m-%d')
                    month_year = (date_obj.month, date_obj.year)  # Кортеж (месяц, год)
                    months_used.add(month_year)

                    # Сортируем месяцы в хронологическом порядке
                sorted_months = sorted(months_used, key=lambda x: (x[1], x[0]))

                # Преобразуем в удобный формат
                month_names = []
                for month, year in sorted_months:
                    month_name = datetime(year=year, month=month, day=1).strftime('%B %Y')
                    month_names.append(month_name)

                await callback_query.message.answer(
                    _("Выберите месяц для отображения диаграммы Ганта."),
                    reply_markup=kb.months(month_names)
                )
        else:
            await callback_query.message.answer(json.loads(response.text).get('detail'))
    else:
        await callback_query.message.answer(json.loads(response.text).get('detail'))


@router.callback_query(F.data.startswith("gant_month_"))
async def back_to_list(callback_query: CallbackQuery, state: FSMContext, bot: Bot = bot_unit):
    await callback_query.answer()
    gant_month = callback_query.data.split("_")[-2]
    gant_year = callback_query.data.split("_")[-1]
    state_data = await state.get_data()

    chosen_month_labs = filter_labs_by_month(state_data, gant_year, gant_month)
    print(chosen_month_labs)
    try:
        plt, fig = await create_diagram_month(chosen_month_labs, state_data["disciplines_dict"], gant_month, gant_year)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close(fig)

        photo = BufferedInputFile(
            file=buf.getvalue(),  # Используем getvalue() вместо read()
            filename="gantt_chart.png"
        )
        await bot.send_photo(chat_id=callback_query.message.chat.id, photo=photo)
        await bot.send_document(chat_id=callback_query.message.chat.id, document=photo)
        buf.close()
    except Exception as e:
        print(e)
        await callback_query.message.answer(
            _("У Вас не добавлено ни одного задания.")
        )
