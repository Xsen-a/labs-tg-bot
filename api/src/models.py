"""
Содержит модели объектов в БД
"""
import enum
from typing import Optional

from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, Relationship
from datetime import time, date

from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

metadata = MetaData()


class Status(enum.Enum):
    not_started = 'Не начато'
    in_progress = 'В процессе'
    done = 'Готово к сдаче'
    submitted = 'Сдано'


class FileType(enum.Enum):
    document = 'document'
    photo = 'photo'
    video = 'video'
    audio = 'audio'


class User(SQLModel, table=True):
    __tablename__ = "tblUser"
    user_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о пользователе")
    telegram_id: str = Field(max_length=20, description="Идентификатор Telegram аккаунта пользователя")
    is_petrsu_student: bool = Field(default=False, description="Флаг, является ли пользователь студентом ПетрГУ")
    group: Optional[str] = Field(default=None, max_length=100, description="Группа студента ПетрГУ")

    disciplines: list["Discipline"] = Relationship(back_populates="user")
    teachers: list["Teacher"] = Relationship(back_populates="user")
    tasks: list["Task"] = Relationship(back_populates="user")
    lessons: list["Lesson"] = Relationship(back_populates="user")


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

    user: User = Relationship(back_populates="teachers")
    disciplines: list["Discipline"] = Relationship(back_populates="teacher")


class Discipline (SQLModel, table=True):
    __tablename__ = "tblDiscipline"
    discipline_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о дисциплине")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    teacher_id: Optional[int] = Field(foreign_key="tblTeacher.teacher_id", description="Ссылка на идентификатор записи о преподавателе")
    name: str = Field(max_length=100, description="Название дисциплины")
    is_from_API: bool = Field(default=False, description="Флаг, получена ли дисциплина из API ПетрГУ")

    user: User = Relationship(back_populates="disciplines")
    teacher: Optional["Teacher"] = Relationship(back_populates="disciplines")
    lessons: list["Lesson"] = Relationship(back_populates="discipline")
    tasks: list["Task"] = Relationship(back_populates="discipline")


class Lesson(SQLModel, table=True):
    __tablename__ = "tblLesson"
    lesson_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о паре")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    discipline_id: int = Field(foreign_key="tblDiscipline.discipline_id", description="Ссылка на идентификатор записи о дисциплине")
    classroom: str = Field(max_length=100, description="Аудитория, в которой проходит пара")
    start_time: time = Field(description="Время начала пары")
    end_time: time = Field(description="Время окончания пары")
    start_date: date = Field(description="Дата проведения первой периодичной или единичной пары")
    periodicity_days: int = Field(default=0, description="Периодичность в днях, с которой повторяются пары")

    user: User = Relationship(back_populates="lessons")
    discipline: Discipline = Relationship(back_populates="lessons")


class Task(SQLModel, table=True):
    __tablename__ = "tblTask"
    task_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о лабораторной работе")
    user_id: int = Field(foreign_key="tblUser.user_id", description="Ссылка на идентификатор записи о пользователе")
    discipline_id: int = Field(foreign_key="tblDiscipline.discipline_id", description="Ссылка на идентификатор записи о дисциплине")
    name: str = Field(max_length=100, description="Название лабораторной работы")
    task_text: Optional[str] = Field(default=None, description="Текст задания лабораторной работы")
    task_link: Optional[str] = Field(default=None, max_length=255, description="Ссылка на задание лабораторной работы")
    start_date: date = Field(description="Дата начала выполнения лабораторной работы")
    end_date: date = Field(description="Дата сдачи лабораторной работы")
    extra_info: Optional[str] = Field(default=None, description="Дополнительная информация о лабораторной работе")
    status: Status = Field(default=Status.not_started, description="Статус выполнения лабораторной работы")

    user: User = Relationship(back_populates="tasks")
    discipline: Discipline = Relationship(back_populates="tasks")
    files: list["File"] = Relationship(back_populates="task")


class File(SQLModel, table=True):
    __tablename__ = "tblFile"
    file_id: int = Field(default=None, primary_key=True, description="Уникальный идентификатор записи о файле")
    task_id: int = Field(foreign_key="tblTask.task_id", description="Ссылка на идентификатор записи о лабораторной работе")
    file_name: str = Field(max_length=255, description="Имя файла")
    file_data: bytes = Field(description="Содержимое файла любого формата в байтах")
    file_type: FileType = Field(default=FileType.document, description="Тип файла Telegram")

    task: Task = Relationship(back_populates="files")
