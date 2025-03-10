"""
Этот файл содержит модели объектов в БД
"""
import enum
from typing import Union

from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, time

metadata = MetaData()

#
# class Roles(enum.Enum):
#     student = 'student'
#     teacher = 'teacher'
#     admin = 'admin'
#
#
# class HierarchyLevelName(enum.Enum):
#     faculty = 'Факультет'  # факультет
#     institute = 'Институт'  # институт
#     department = 'Кафедра'  # кафедра
#     direction = 'Направление'  # направление обучения
#     level = 'Уровень образования'  # уровень образования
#     course = 'Курс'  # курс
#     group = 'Группа'
#
#
# class Periodicity(enum.Enum):
#     once = 'once'
#     day = 'day'
#     week = 'week'
#     month = 'month'
#     year = 'year'
#
#
# class ExceptionType(enum.Enum):
#     cancel = 'cancel'
#     addition = 'addition'
#     moving = 'moving'
#
#
# class TeacherSubjectLink(SQLModel, table=True):
#     __tablename__ = "teachers_subjects"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     subject_id: int = Field(foreign_key="subjects.id")
#     teacher_id: int = Field(foreign_key="users.id")
#
#
# class Hierarchy(SQLModel, table=True):
#     __tablename__ = "hierarchy"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     name: str = Field()
#     path: str = Field()
#     hierarchy: HierarchyLevelName = Field()
#
#     users: list["User"] = Relationship(back_populates="group")
#
#
# class User(SQLModel, table=True):
#     __tablename__ = "users"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     tg_id: Union[int, None] = Field(default=None)
#     role: Roles = Field(default=Roles.student)
#     name: Union[str, None] = Field(default=None)
#     phone: Union[str, None] = Field(default=None)
#     email: Union[str, None] = Field(default=None)
#     group_id: Union[int, None] = Field(foreign_key="hierarchy.id")
#
#     subjects: list["Subject"] = Relationship(back_populates="teachers", link_model=TeacherSubjectLink)
#     group: Union[Hierarchy, None] = Relationship(back_populates="users")
#
#
# class Subject(SQLModel, table=True):
#     __tablename__ = "subjects"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     name: str = Field()
#     code: str = Field()
#
#     teachers: list["User"] = Relationship(back_populates="subjects", link_model=TeacherSubjectLink)
#
#
# class Corpus(SQLModel, table=True):
#     __tablename__ = "corpuses"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     address: str = Field()
#     name: str = Field()
#
#     classrooms: list["Classroom"] = Relationship(back_populates="corpus")
#
#
# class Classroom(SQLModel, table=True):
#     __tablename__ = "classrooms"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     name: str = Field()
#     corpus_id: int = Field(foreign_key="corpuses.id")
#
#     corpus: Corpus = Relationship(back_populates="classrooms")
#
#
# class TimePattern(SQLModel, table=True):
#     __tablename__ = "time_patterns"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     time_start: time = Field()
#     time_end: time = Field()
#
#
# class Schedule(SQLModel, table=True):
#     __tablename__ = "schedule"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     subject_id: int = Field(foreign_key="subjects.id")
#     teacher_id: int = Field(foreign_key="users.id")
#     group_id: int = Field(foreign_key="hierarchy.id")
#     classroom_id: int = Field(foreign_key="classrooms.id")
#
#
# class ScheduleTime(SQLModel, table=True):
#     __tablename__ = "schedule_time"
#     id: Union[int, None] = Field(default=None, primary_key=True)
#     moved_to: Union[int, None] = Field(foreign_key="schedule_time.id")
#     schedule_id: int = Field(foreign_key="schedule.id")
#     time_start: datetime = Field()
#     time_end: datetime = Field()
#     periodicity: Union[Periodicity, None] = Field()
#     number_of_periodicity: int = Field()
#     start_day: datetime = Field()
#     finish_day: datetime = Field()
#     exception_type: Union[ExceptionType, None] = Field()
