import calendar
import io
import json

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

import requests
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from matplotlib.patches import FancyBboxPatch

import bot.src.keyboards.diagrams_keyboard as kb
from ..settings import settings

from bot.src.bot_unit import bot as bot_unit

router = Router()

status_colors = {
    'Не начато': '#dedede',
    'В процессе': '#66e3ff',
    'Готово к сдаче': '#ddb3fc',
    'Сдано': '#94ffab'
}

lesson_colors = {
    'schedule': '#f59527',
    'database': '#675ce5',
    'schedule_end': '#fac07d',
    'database_end': '#a69ef7'
}

FIXED_SPACING = 1
BAR_HEIGHT = 0.7


def round_to_2weeks(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%d')

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
    current_date = datetime.now()

    first_day = datetime(year=year, month=month, day=1)
    if month == 12:
        last_day = datetime(year=year + 1, month=1, day=1)
    else:
        last_day = datetime(year=year, month=month + 1, day=1)

    for lab in labs_data['labs_response']['labs']:
        start_date = datetime.strptime(lab['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(lab['end_date'], '%Y-%m-%d')

        if ((start_date < last_day and end_date >= first_day) or
                (end_date < current_date and lab['status'] != 'Сдано'
                 and start_date < datetime(day=calendar.monthrange(year, month)[1], month=month, year=year))):
            filtered_labs.append(lab)

    return filtered_labs


def get_schedule_pairs(schedule_data):
    pairs = []

    for day_lessons in schedule_data['denominator']:
        for lesson in day_lessons:
            if "Лекция" not in lesson['type']:
                pairs.append({
                    'discipline': lesson['title'],
                    'date': lesson['date']
                })

    for day_lessons in schedule_data['numerator']:
        for lesson in day_lessons:
            if "Лекция" not in lesson['type']:
                pairs.append({
                    'discipline': lesson['title'],
                    'date': lesson['date']
                })

    return pairs


def get_lessons_pairs(lessons_response, disciplines_dict):
    pairs = []

    for lesson in lessons_response['lessons']:
        discipline_id = lesson['discipline_id']
        pairs.append({
            'discipline': disciplines_dict.get(discipline_id, f"Unknown ({discipline_id})"),
            'discipline_id': discipline_id,
            'start_date': lesson['start_date'],
            'periodicity_days': lesson['periodicity_days']
        })

    return pairs


def generate_dates(start_date_str, periodicity_days, weeks=3):
    today = datetime.now().date() - timedelta(days=7)
    start_monday = today - timedelta(days=today.weekday())
    end_date = start_monday + timedelta(weeks=weeks)

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    dates = []

    if periodicity_days == 0:
        if start_monday <= start_date <= end_date:
            dates.append(start_date)
    else:
        current_date = start_date
        while current_date < start_monday:
            current_date += timedelta(days=periodicity_days)

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=periodicity_days)

    return dates


async def create_diagram_full(data):
    labs = data['labs_response']['labs']
    disciplines_dict = data['disciplines_dict']

    disciplines_labs = {}
    for lab in labs:
        discipline_id = lab['discipline_id']
        if discipline_id not in disciplines_labs:
            disciplines_labs[discipline_id] = []
        disciplines_labs[discipline_id].append(lab)

    sorted_disciplines = sorted(disciplines_labs.items(),
                                key=lambda x: min(lab['start_date'] for lab in x[1]))

    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 12,
        'font.weight': 'bold'
    })

    all_items = []
    y_labels = []

    for discipline_id, lab_list in sorted_disciplines:
        discipline_name = disciplines_dict.get(discipline_id, f"Дисциплина {discipline_id}")

        lab_list.sort(key=lambda x: x['start_date'])

        y_labels.append(discipline_name)
        all_items.append({'type': 'discipline'})

        for lab in lab_list:
            y_labels.append(lab['name'])
            all_items.append({'type': 'lab', 'data': lab})

        all_items.append({'type': 'empty'})
        y_labels.append("")

    if len(all_items) == 0:
        return

    total_labs = sum(len(labs) for labs in disciplines_labs.values())
    fig_height = len(all_items) * 0.4
    fig, ax = plt.subplots(figsize=(15, fig_height))

    lab_tasks = [item['data'] for item in all_items if item['type'] == 'lab']

    start_dates_num = [mdates.datestr2num(lab['start_date']) for lab in lab_tasks]
    end_dates_num = [mdates.datestr2num(lab['end_date']) for lab in lab_tasks]
    durations = [end - start for start, end in zip(start_dates_num, end_dates_num)]
    statuses = [lab['status'] for lab in lab_tasks]

    y_pos = np.arange(len(all_items)) * FIXED_SPACING

    lab_index = 0
    deadline_num = 0
    for i, item in enumerate(all_items):
        if item['type'] == 'lab':
            start = start_dates_num[lab_index]
            duration = durations[lab_index]
            status = statuses[lab_index]
            ax.barh(y_pos[i], duration, left=start, height=BAR_HEIGHT,
                    color=status_colors.get(status),
                    edgecolor='black', linewidth=0.5)
            if item['data']['status'] != 'Сдано':
                deadline = datetime.strptime(item['data']['end_date'], '%Y-%m-%d')
                if deadline < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                    ax.barh(y_pos[i], mdates.date2num(datetime.now()) - mdates.date2num(deadline) - 0.5, left=deadline, height=BAR_HEIGHT,
                            color='#FFCCCC', linestyle="--", alpha=0.7,
                            edgecolor='red', linewidth=0.5)
                    deadline_num += 1
            lab_index += 1

    ax.set_yticks(y_pos)
    labels = ax.set_yticklabels(y_labels, ha='right', position=(-0.1, 0), fontsize=10)

    discipline_names = set(disciplines_dict.values())
    for i, label in enumerate(labels):
        text = label.get_text()
        if text in discipline_names:
            label.set_fontweight('bold')
            label.set_fontsize(12)
        else:
            label.set_fontweight('normal')
            label.set_fontsize(10)

    ax.set_ylim(len(all_items) - 0.5, -0.5)

    min_date = min(lab['start_date'] for lab in lab_tasks)
    min_date_dt = datetime.strptime(min_date, '%Y-%m-%d')
    min_date_num = mdates.date2num(min_date_dt)

    max_date_dt = max(datetime.strptime(lab['end_date'], '%Y-%m-%d') for lab in lab_tasks)
    today_dt = datetime.now()
    max_date = max(max_date_dt, today_dt).strftime('%Y-%m-%d')
    rounded_max_date = round_to_2weeks(max_date)
    max_date_num = mdates.date2num(rounded_max_date)

    ax.set_xlim(min_date_num - 0.001, max_date_num + 0.001)

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))

    ax.set_xticks(list(ax.get_xticks()) + [min_date_num])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.xaxis.tick_top()
    for label in ax.get_xticklabels():
        label.set_fontweight('normal')

    ax.axvline(x=mdates.date2num(datetime.now()) - 0.5, color='red', linestyle='--', linewidth=1.5)

    ax.grid(True, axis='x', linestyle=':', alpha=0.5)

    for spine in ['left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

    legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=color, label=status)
                       for status, color in status_colors.items()]
    legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc='#FFCCCC', label=f"Просроченные задания: {deadline_num}",
                                         linestyle="--", edgecolor='red', linewidth=0.5))
    legend = ax.legend(handles=legend_elements,
                       loc='upper left',
                       bbox_to_anchor=(1.02, 1),
                       fontsize=9)
    legend.set_title('Статусы', prop={'weight': 'normal'})
    for text in legend.get_texts():
        text.set_fontweight('normal')

    plt.tight_layout()
    plt.subplots_adjust(left=0.3, right=0.85, top=0.95, bottom=0.05)

    # plt.savefig('график_лабораторных.png',
    #             dpi=300,
    #             bbox_inches='tight',
    #             pad_inches=0.5)
    #
    # with PdfPages('all_labs.pdf') as pdf:
    #     pdf.savefig(fig, bbox_inches='tight')
    #
    # plt.show()

    return plt, fig


async def create_diagram_month(labs, disciplines_dict, month, year):
    month = int(month)
    year = int(year)

    disciplines_labs = {}
    for lab in labs:
        discipline_id = lab['discipline_id']
        if discipline_id not in disciplines_labs:
            disciplines_labs[discipline_id] = []
        disciplines_labs[discipline_id].append(lab)

    sorted_disciplines = sorted(disciplines_labs.items(),
                                key=lambda x: min(lab['start_date'] for lab in x[1]))

    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 12,
        'font.weight': 'bold'
    })

    all_items = []
    y_labels = []

    for discipline_id, lab_list in sorted_disciplines:
        discipline_name = disciplines_dict.get(discipline_id, f"Дисциплина {discipline_id}")

        lab_list.sort(key=lambda x: x['start_date'])

        y_labels.append(discipline_name)
        all_items.append({'type': 'discipline'})

        for lab in lab_list:
            y_labels.append(lab['name'])
            all_items.append({'type': 'lab', 'data': lab})

        all_items.append({'type': 'empty'})
        y_labels.append("")

    if len(all_items) == 0:
        return

    total_labs = sum(len(labs) for labs in disciplines_labs.values())
    fig_height = len(all_items) * 0.4
    fig, ax = plt.subplots(figsize=(15, fig_height))

    lab_tasks = [item['data'] for item in all_items if item['type'] == 'lab']

    start_dates_num = [mdates.datestr2num(lab['start_date']) for lab in lab_tasks]
    end_dates_num = [mdates.datestr2num(lab['end_date']) for lab in lab_tasks]
    durations = [end - start for start, end in zip(start_dates_num, end_dates_num)]
    statuses = [lab['status'] for lab in lab_tasks]

    y_pos = np.arange(len(all_items)) * 1

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
                if deadline < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                    if datetime.now().month != month:
                        ax.barh(y_pos[i], datetime(day=calendar.monthrange(year, month)[1], month=month, year=year) - deadline, left=deadline, height=bar_height,
                                color='#FFCCCC', linestyle="--", alpha=0.7,
                                edgecolor='red', linewidth=0.5)
                    else:
                        ax.barh(y_pos[i],
                                datetime(day=datetime.now().day, month=month, year=year) - deadline,
                                left=deadline, height=bar_height,
                                color='#FFCCCC', linestyle="--", alpha=0.7,
                                edgecolor='red', linewidth=0.5)
                    deadline_num += 1
            lab_index += 1

    ax.set_yticks(y_pos)
    labels = ax.set_yticklabels(y_labels, ha='right', position=(-0.1, 0), fontsize=10)

    discipline_names = set(disciplines_dict.values())
    for i, label in enumerate(labels):
        text = label.get_text()
        if text in discipline_names:
            label.set_fontweight('bold')
            label.set_fontsize(12)
        else:
            label.set_fontweight('normal')
            label.set_fontsize(10)

    ax.set_ylim(len(all_items) - 0.5, -0.5)

    min_date_dt = datetime(day=1, month=month, year=year)
    min_date_num = mdates.date2num(min_date_dt)

    max_date_dt = datetime(day=calendar.monthrange(year, month)[1], month=month, year=year)
    max_date_num = mdates.date2num(max_date_dt)

    ax.set_xlim(min_date_num - 0.001, max_date_num + 0.001)

    days_in_month = calendar.monthrange(year, month)[1]
    ax.set_xticks(np.arange(min_date_num, max_date_num + 1, 1))
    ax.xaxis.set_major_formatter(plt.FixedFormatter(range(1, days_in_month + 1)))
    ax.xaxis.tick_top()
    for label in ax.get_xticklabels():
        label.set_fontweight('normal')

    ax.axvline(x=mdates.date2num(datetime.now().replace(hour=0)), color='red', linestyle='--', linewidth=1.5)

    ax.grid(True, axis='x', which='major', linestyle='-', alpha=0.3)
    ax.grid(True, axis='x', which='minor', linestyle=':', alpha=0.1)

    for spine in ['left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

    legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=color, label=status)
                       for status, color in status_colors.items()]
    if deadline_num != 0:
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc='#FFCCCC', label=f"Просроченные задания: {deadline_num}",
                                         linestyle="--", edgecolor='red', linewidth=0.5))
    legend = ax.legend(handles=legend_elements,
                       loc='upper left',
                       bbox_to_anchor=(1.02, 1),
                       fontsize=9)
    legend.set_title('Статусы', prop={'weight': 'normal'})
    for text in legend.get_texts():
        text.set_fontweight('normal')

    month_name = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }.get(month, '')

    plt.title(f"{month_name}, {year} год",
              pad=40, fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.subplots_adjust(left=0.3, right=0.85, top=0.95, bottom=0.05)

    # plt.savefig('график_лабораторных.png',
    #             dpi=300,
    #             bbox_inches='tight',
    #             pad_inches=0.5)
    #
    # with PdfPages('all_labs.pdf') as pdf:
    #     pdf.savefig(fig, bbox_inches='tight')
    #
    # plt.show()
    return plt, fig


async def create_diagram_week(data):

    labs = data['labs_response']['labs']
    disciplines_dict = data['disciplines_dict']

    if 'schedule_data' in data.keys():
        schedule_pairs = get_schedule_pairs(data['schedule_data'])
    else:
        schedule_pairs = []

    lessons_data = {
        'schedule_pairs': schedule_pairs,
        'lessons_pairs': get_lessons_pairs(data['lessons_response'], data['disciplines_dict'])
    }
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_monday = today - timedelta(days=today.weekday()) - timedelta(days=7)
    end_date = start_monday + timedelta(weeks=3) - timedelta(days=7)

    disciplines_labs = {}
    for lab in labs:
        discipline_id = lab['discipline_id']
        if discipline_id not in disciplines_labs:
            disciplines_labs[discipline_id] = []
        disciplines_labs[discipline_id].append(lab)

    sorted_disciplines = sorted(disciplines_labs.items(),
                                key=lambda x: min(lab['start_date'] for lab in x[1]))

    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 12,
        'font.weight': 'bold'
    })

    all_items = []
    y_labels = []

    for discipline_id, lab_list in sorted_disciplines:
        discipline_name = disciplines_dict.get(discipline_id, f"Дисциплина {discipline_id}")

        lab_list.sort(key=lambda x: x['start_date'])

        y_labels.append(discipline_name)
        all_items.append({'type': 'discipline'})

        for lab in lab_list:
            end_lab_date = datetime.strptime(lab['end_date'], '%Y-%m-%d').date()
            if lab['status'] != 'Сдано' or (start_monday.date() <= end_lab_date <= end_date.date()):
                y_labels.append(lab['name'])
                all_items.append({'type': 'lab', 'data': lab})

        all_items.append({'type': 'empty'})
        y_labels.append("")

    if len(all_items) == 0:
        return

    total_labs = sum(len(labs) for labs in disciplines_labs.values())
    fig_height = len(all_items) * 0.4
    fig, ax = plt.subplots(figsize=(15, fig_height))

    lab_tasks = [item['data'] for item in all_items if item['type'] == 'lab']

    start_dates_num = [mdates.datestr2num(lab['start_date']) for lab in lab_tasks]
    end_dates_num = [mdates.datestr2num(lab['end_date']) for lab in lab_tasks]
    durations = [end - start for start, end in zip(start_dates_num, end_dates_num)]
    statuses = [lab['status'] for lab in lab_tasks]

    y_pos = np.arange(len(all_items)) * 1

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
                if deadline < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                    ax.barh(y_pos[i], mdates.date2num(datetime.now().replace(hour=0)) - mdates.date2num(deadline.replace(hour=0)), left=deadline, height=bar_height,
                            color='#FFCCCC', linestyle="--", alpha=0.7,
                            edgecolor='red', linewidth=0.5)
                    deadline_num += 1
            lab_index += 1

    ax.set_yticks(y_pos)
    labels = ax.set_yticklabels(y_labels, ha='right', position=(-0.1, 0), fontsize=12)

    discipline_names = set(disciplines_dict.values())
    for i, label in enumerate(labels):
        text = label.get_text()
        if text in discipline_names:
            label.set_fontweight('bold')
            label.set_fontsize(13)
        else:
            label.set_fontweight('normal')
            label.set_fontsize(12)

    ax.set_ylim(len(all_items) - 0.5, -0.5)

    ax.set_xlim([
        mdates.date2num(start_monday - timedelta(days=0.5)),
        mdates.date2num(end_date + timedelta(days=0.5))
    ])

    days_ru = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

    all_dates = [start_monday + timedelta(days=i) for i in range(21)]  # 3 недели
    date_numbers = [mdates.date2num(date) for date in all_dates]

    ax.set_xticks(date_numbers)
    ax.set_xticklabels([days_ru[d.weekday()] for d in all_dates])

    current_day = datetime.now().replace(hour=0, minute=0, second=0)
    ax.axvline(x=mdates.date2num(current_day),
               color='red', linestyle='--', linewidth=1.5, zorder=10)

    point_size = 150

    for pair in lessons_data['lessons_pairs']:
        dates = generate_dates(pair['start_date'], pair['periodicity_days'])
        for date in dates:
            pair_date = datetime.strptime(date.strftime('%d.%m.%Y'), '%d.%m.%Y').replace(hour=0, minute=0, second=0)
            pair_num = mdates.date2num(pair_date)
            for i, item in enumerate(all_items):
                if item['type'] == 'lab' and disciplines_dict.get(item['data']['discipline_id']) == pair['discipline']:
                    if item['data']['status'] != 'Сдано':
                        if datetime.strptime(item['data']['start_date'], '%Y-%m-%d') <= pair_date <= datetime.strptime(item['data']['end_date'], '%Y-%m-%d') or \
                                datetime.strptime(item['data']['start_date'],'%Y-%m-%d') <= pair_date <= datetime.now().replace(hour=0, minute=0,second=0, microsecond=0):
                            if pair_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                                color = lesson_colors['database_end']
                            else:
                                color = lesson_colors['database']
                            ax.scatter(pair_num, y_pos[i],
                                      s=point_size, marker='o',
                                      color=color, zorder=5)

    for pair in lessons_data['schedule_pairs']:
        pair_date = datetime.strptime(pair['date'], '%d.%m.%Y').replace(hour=0, minute=0, second=0, microsecond=0)
        pair_num = mdates.date2num(pair_date)

        for i, item in enumerate(all_items):
            if item['type'] == 'lab' and disciplines_dict.get(item['data']['discipline_id']) == pair['discipline']:
                if item['data']['status'] != 'Сдано':
                    if datetime.strptime(item['data']['start_date'], '%Y-%m-%d') <= pair_date <= datetime.strptime(item['data']['end_date'], '%Y-%m-%d') or \
                            datetime.strptime(item['data']['start_date'], '%Y-%m-%d') <= pair_date <= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                        if pair_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                            color = lesson_colors['schedule_end']
                        else:
                            color = lesson_colors['schedule']
                        ax.scatter(pair_num, y_pos[i],
                                  s=point_size, marker='o',
                                  color=color, zorder=5)

    ax.xaxis.tick_top()
    # plt.xticks(rotation=45)
    ax.grid(True, axis='x', linestyle=':', alpha=0.5)

    for date in all_dates:
        if date.weekday() == 0:
            ax.axvline(x=mdates.date2num(date), color='gray', linestyle='-', alpha=0.3)

    ax.grid(True, axis='x', which='major', linestyle='-', alpha=0.3)
    ax.grid(True, axis='x', which='minor', linestyle=':', alpha=0.1)

    for spine in ['left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

    legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=color, label=status)
                       for status, color in status_colors.items()]
    if deadline_num != 0:
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc='#FFCCCC', label=f"Просроченные задания: {deadline_num}",
                                         linestyle="--", edgecolor='red', linewidth=0.5))
    legend_elements.append(
        plt.Line2D([0], [0], marker='o', color='w', label='Занятия из расписания ПетрГУ',
                   markerfacecolor=lesson_colors['schedule'], markersize=10))
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', label='Ваши добавленные занятия',
                   markerfacecolor=lesson_colors['database'], markersize=10))

    legend = ax.legend(handles=legend_elements,
                       loc='upper left',
                       bbox_to_anchor=(1.02, 1),
                       fontsize=11)

    legend.set_title('Статусы', prop={'weight': 'normal'})
    for text in legend.get_texts():
        text.set_fontweight('normal')

    plt.tight_layout()
    plt.subplots_adjust(left=0.3, right=0.85, top=0.95, bottom=0.05)

    # plt.savefig('график_лабораторных.png',
    #             dpi=300,
    #             bbox_inches='tight',
    #             pad_inches=0.5)
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
                    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.5)
                    plt.close(fig)

                    photo = BufferedInputFile(
                        file=buf.getvalue(),
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
                months_used = set()
                for lab in state_data["labs_response"]["labs"]:
                    date_obj = datetime.strptime(lab["start_date"], '%Y-%m-%d')
                    month_year = (date_obj.month, date_obj.year)
                    months_used.add(month_year)
                    date_obj = datetime.strptime(lab["end_date"], '%Y-%m-%d')
                    month_year = (date_obj.month, date_obj.year)
                    months_used.add(month_year)

                sorted_months = sorted(months_used, key=lambda x: (x[1], x[0]))

                month_names = []
                for month, year in sorted_months:
                    month_name = datetime(year=year, month=month, day=1).strftime('%B %Y')
                    month_names.append(month_name)

                await callback_query.message.edit_text(
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
    try:
        plt, fig = await create_diagram_month(chosen_month_labs, state_data["disciplines_dict"], gant_month, gant_year)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.5)
        plt.close(fig)

        photo = BufferedInputFile(
            file=buf.getvalue(),
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


@router.callback_query(F.data == "gant_three_weeks")
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
                url_req = f"{settings.API_URL}/get_lessons"
                response = requests.get(url_req, json={"user_id": user_id})
                if response.status_code == 200:
                    response_data = response.json()
                    await state.update_data(lessons_response=response_data)
                    state_data = await state.get_data()
                    # await create_diagram_week(state_data)
                    try:
                        plt, fig = await create_diagram_week(state_data)

                        buf = io.BytesIO()
                        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.5)
                        plt.close(fig)

                        photo = BufferedInputFile(
                            file=buf.getvalue(),
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


def wrap_text(text, max_length=30):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


async def create_kanban(data):
    # Получаем и группируем данные
    labs = data['labs_response']['labs']
    disciplines = data['disciplines_dict']

    status_groups = {
        "Не начато": [],
        "В процессе": [],
        "Готово к сдаче": [],
        "Сдано": []
    }

    for lab in labs:
        status = lab['status']
        if status in status_groups:
            lab['discipline_name'] = disciplines.get(lab['discipline_id'], 'Неизвестно')
            status_groups[status].append(lab)

    # Настройки визуализации
    column_width = 5.0
    margin = 0.4
    spacing = 0.5
    colors = [status_colors['Не начато'], status_colors['В процессе'],
              status_colors['Готово к сдаче'], status_colors['Сдано']]

    # Определяем максимальное количество карточек в колонке
    max_cards = max(len(tasks) for tasks in status_groups.values())
    column_heights = []
    for status, tasks in status_groups.items():
        col_height = margin * 2
        for task in tasks:
            name_lines = wrap_text(task['name'])
            disc_lines = wrap_text(f"Дисц.: {task['discipline_name']}")
            col_height += (len(name_lines) + len(disc_lines) + 1) * 0.3 + spacing
        col_height += margin / 2 - 0.2
        column_heights.append(col_height)

    total_height = max(column_heights)

    # Создаем фигуру
    fig, ax = plt.subplots(figsize=(15, total_height))
    ax.axis('off')

    # Функция для переноса текста


    for col_idx, (status, color) in enumerate(zip(status_groups.keys(), colors)):
        x = col_idx * (column_width + margin) + margin

        # Фон колонки
        ax.add_patch(
            FancyBboxPatch(
                (x, margin),
                column_width,
                total_height - margin,
                facecolor=color,
                alpha=0.7,
                edgecolor="black",
                linewidth=2,
                boxstyle="round,pad=0.1",
                zorder=0
            )
        )

        # Заголовок колонки
        ax.text(
            x + column_width / 2,
            total_height,
            status + " - " + str(len(status_groups[status])),
            ha='center',
            va='center',
            fontsize=14,
            weight='bold',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),
            zorder=2
        )

    # Рисуем карточки задач
    for col_idx, (status, tasks) in enumerate(status_groups.items()):
        x = col_idx * (column_width + margin) + margin + 0.2
        y_offset = total_height - margin - 0.3  # Начинаем от верхнего края

        for task in tasks:
            # Форматируем текст
            name_lines = wrap_text(task['name'])
            disc_lines = wrap_text(f"Дисц.: {task['discipline_name']}")
            date_line = f"Срок: {datetime.strptime(task['end_date'], '%Y-%m-%d').strftime('%d.%m.%Y')}"

            # Рассчитываем высоту карточки
            line_count = len(name_lines) + len(disc_lines) + 1
            current_card_height = line_count * 0.3

            # Рисуем карточку
            ax.add_patch(
                FancyBboxPatch(
                    (x, y_offset - current_card_height),
                    column_width - 0.4,
                    current_card_height,
                    facecolor="white",
                    edgecolor="gray",
                    linewidth=1,
                    boxstyle="round,pad=0.2,rounding_size=0.15",
                    zorder=1
                )
            )

            # Добавляем текст
            all_lines = name_lines + disc_lines + [date_line]
            for i, line in enumerate(all_lines):
                weight = 'bold' if i < len(name_lines) else 'normal'
                ax.text(
                    x + 0.3,
                    y_offset - current_card_height + 0.23 + (len(all_lines) - i - 1) * 0.3,
                    line,
                    ha='left',
                    va='top',
                    fontsize=11,
                    fontfamily='sans-serif',
                    weight=weight,
                    zorder=3
                )

            y_offset -= current_card_height + spacing

    # Настраиваем границы
    total_width = (column_width + margin) * len(status_groups) + margin
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height + margin)
    plt.tight_layout()
    return plt, fig