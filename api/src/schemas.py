"""
Этот файл содержит схемы данных для приема запроса и отправки ответа от сервера
"""

from datetime import datetime, date, time

from pydantic import BaseModel, field_validator
from sqlmodel import SQLModel


class GetUserIdSchema(SQLModel):
    telegram_id: str


class GetUserIdResponseSchema(SQLModel):
    user_id: int


class AddTeacherSchema(SQLModel):
    user_id: int
    name: str
    phone_number: str | None = None
    email: str | None = None
    social_page_link: str | None = None
    classroom: str | None = None
    is_from_API: bool


class CheckUserExistSchema(SQLModel):
    telegram_id: str


class CheckUserExistResponseSchema(BaseModel):
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


class ChangeUserGroupSchema(SQLModel):
    telegram_id: str
    group: str


class ChangeUserStatusSchema(SQLModel):
    telegram_id: str
    group: str
    is_petrsu_student: bool
