"""
Содержит модели объектов в БД
"""
import enum
from typing import Optional

from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel
from datetime import time, date

metadata = MetaData()


class Status(enum.Enum):
    not_started = 'Не начато'
    in_progress = 'В процессе'
    done = 'Готово к сдаче'
    submitted = 'Сдано'


class User(SQLModel, table=True):
    __tablename__ = "tblUser"
    user_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о пользователе")
    telegram_id: str = Field(max_length=20, description="Идентификатор Telegram аккаунта пользователя")
    is_petrsu_student: bool = Field(default=False, description="Флаг, является ли пользователь студентом ПетрГУ")
    group: Optional[str] = Field(default=None, max_length=100, description="Группа студента ПетрГУ")


class Teacher(SQLModel, table=True):
    __tablename__ = "tblTeacher"
    teacher_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о преподавателе")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    name: str = Field(max_length=100, description="ФИО преподавателя")
    phone_number: Optional[str] = Field(default=None, max_length=20, description="Номер телефона преподавателя")
    email: Optional[str] = Field(default=None, max_length=255, description="Электронный почтовый адрес преподавателя")
    social_page_link: Optional[str] = Field(default=None, max_length=255, description="Ссылка на социальную сеть преподавателя")
    classroom: Optional[str] = Field(default=None, max_length=100, description="Аудитория, в которой можно найти преподавателя")
    is_from_API: bool = Field(default=False, description="Флаг, получен ли преподаватель из API ПетрГУ")


class Dicipline(SQLModel, table=True):
    __tablename__ = "tblDicipline"
    dicipline_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о дисциплине")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    teacher_id: Optional[int] = Field(foreign_key="tblTeacher.teacher_id", description="Ссылка на идентификатор записи о преподавателе")
    name: str = Field(max_length=100, description="Название дисциплины")
    is_from_API: bool = Field(default=False, description="Флаг, получена ли дисциплина из API ПетрГУ")


class Lesson(SQLModel, table=True):
    __tablename__ = "tblLesson"
    lesson_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о паре")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    dicipline_id: int = Field(foreign_key="tblDicipline.dicipline_id", description="Ссылка на идентификатор записи о дисциплине")
    classroom: str = Field(max_length=100, description="Аудитория, в которой проходит пара")
    start_time: time = Field(description="Время начала пары")
    end_time: time = Field(description="Время окончания пары")
    date: date = Field(description="Дата проведения первой периодичной или единичной пары")
    periodicity_days: int = Field(default=0, description="Периодичность в днях, с которой повторяются пары")
    is_from_API: bool = Field(default=False, description="Флаг, получена ли пара из API")


class Task(SQLModel, table=True):
    __tablename__ = "tblTask"
    task_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о лабораторной работе")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    dicipline_id: int = Field(foreign_key="tblDicipline.dicipline_id", description="Ссылка на идентификатор записи о дисциплине")
    name: str = Field(max_length=100, description="Название лабораторной работы")
    task_text: Optional[str] = Field(default=None, description="Текст задания лабораторной работы")
    task_link: Optional[str] = Field(default=None, max_length=255, description="Ссылка на задание лабораторной работы")
    start_date: date = Field(description="Дата начала выполнения лабораторной работы")
    end_date: date = Field(description="Дата сдачи лабораторной работы")
    extra_info: Optional[str] = Field(default=None, description="Дополнительная информация о лабораторной работе")
    status: Status = Field(description="Статус выполнения лабораторной работы")


class File(SQLModel, table=True):
    __tablename__ = "tblFile"
    file_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о файле")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    task_id: int = Field(foreign_key="tblTask.task_id", description="Ссылка на идентификатор записи о лабораторной работе")
    file_name: str = Field(max_length=255, description="Имя файла")
    file_data: bytearray = Field(description="Содержимое файла любого формата в байтах")
