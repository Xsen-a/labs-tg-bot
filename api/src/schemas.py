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


class GetUserGroupSchema(SQLModel):
    telegram_id: str


class GetUserGroupResponseSchema(SQLModel):
    group: str | None = None


class AddTeacherSchema(SQLModel):
    user_id: int
    name: str
    phone_number: str | None = None
    email: str | None = None
    social_page_link: str | None = None
    classroom: str | None = None
    is_from_API: bool


class GetTeachersSchema(SQLModel):
    user_id: int


class GetTeachersResponseSchema(SQLModel):
    teachers: list


class CheckUserExistSchema(SQLModel):
    telegram_id: str


class CheckUserExistResponseSchema(BaseModel):
    exists: bool


class AddUserSchema(SQLModel):
    telegram_id: str
    is_petrsu_student: bool
    group: str | None = None


class CheckPetrsuStudentSchema(SQLModel):
    telegram_id: str


class CheckPetrsuStudentResponseSchema(BaseModel):
    is_petrsu_student: bool
    group: str | None = None


class ChangeUserGroupSchema(SQLModel):
    telegram_id: str
    group: str | None = None


class ChangeUserStatusSchema(SQLModel):
    telegram_id: str
    group: str | None = None
    is_petrsu_student: bool
