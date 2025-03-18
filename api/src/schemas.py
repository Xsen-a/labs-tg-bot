"""
Этот файл содержит схемы данных для приема запроса и отправки ответа от сервера
"""

from datetime import datetime, date, time

from pydantic import BaseModel
from sqlmodel import SQLModel


class AddTeacherSchema(SQLModel):
    user_id: int
    name: str
    phone_number: str
    email: str
    social_page_link: str
    classroom: str
    is_from_API: bool


class CheckUserSchema(SQLModel):
    telegram_id: str


class CheckUserResponseSchema(BaseModel):
    exists: bool


class AddUserSchema(SQLModel):
    telegram_id: str
    is_petrsu_student: bool
    group: str


class CheckPetrsuStudentSchema(SQLModel):
    telegram_id: str


class CheckPetrsuStudentResponseSchema(BaseModel):
    is_petrsu_student: bool
    group: str