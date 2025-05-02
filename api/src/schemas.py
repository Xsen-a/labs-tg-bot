"""
Этот файл содержит схемы данных для приема запроса и отправки ответа от сервера
"""

from datetime import datetime, date, time

from pydantic import BaseModel, field_validator
from sqlalchemy.dialects.postgresql import Any
from sqlmodel import SQLModel
from api.src.models import Status


class GetUserIdSchema(SQLModel):
    telegram_id: str


class GetUserIdResponseSchema(SQLModel):
    user_id: int


class GetUserGroupSchema(SQLModel):
    telegram_id: str


class GetUserGroupResponseSchema(SQLModel):
    group: str | None = None


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


class AddTeacherSchema(SQLModel):
    user_id: int
    name: str
    phone_number: str | None = None
    email: str | None = None
    social_page_link: str | None = None
    classroom: str | None = None
    is_from_API: bool


class GetTeacherSchema(SQLModel):
    teacher_id: int


class GetTeacherResponseSchema(SQLModel):
    user_id: int
    teacher_id: int
    name: str
    phone_number: str | None = None
    email: str | None = None
    social_page_link: str | None = None
    classroom: str | None = None
    is_from_API: bool


class GetTeachersSchema(SQLModel):
    user_id: int


class GetTeachersResponseSchema(SQLModel):
    teachers: list[GetTeacherResponseSchema]


class GetTeacherApiStatusSchema(SQLModel):
    teacher_id: int


class GetTeacherApiStatusResponseSchema(SQLModel):
    is_from_API: bool


class GetTeacherNameSchema(SQLModel):
    teacher_id: int


class GetTeacherNameResponseSchema(SQLModel):
    name: str


class EditTeacherAttributeSchema(SQLModel):
    teacher_id: int
    editing_attribute: str
    editing_value: str


class DeleteTeacherSchema(SQLModel):
    teacher_id: int


class AddDisciplineSchema(SQLModel):
    user_id: int
    teacher_id: int | None = None
    name: str
    is_from_API: bool


class GetDisciplineSchema(SQLModel):
    discipline_id: int


class GetDisciplineResponseSchema(SQLModel):
    discipline_id: int
    user_id: int
    teacher_id: int | None = None
    name: str
    is_from_API: bool


class GetDisciplinesSchema(SQLModel):
    user_id: int


class GetDisciplinesResponseSchema(SQLModel):
    disciplines: list[GetDisciplineResponseSchema]


class GetDisciplineApiStatusSchema(SQLModel):
    discipline_id: int


class GetDisciplineApiStatusResponseSchema(SQLModel):
    is_from_API: bool


class EditDisciplineAttributeSchema(SQLModel):
    discipline_id: int
    editing_attribute: str
    editing_value: str


class DeleteDisciplineSchema(SQLModel):
    discipline_id: int


class AddLabSchema(SQLModel):
    user_id: int
    discipline_id: int
    name: str
    task_text: str | None = None
    task_link: str | None = None
    start_date: date
    end_date: date
    extra_info: str | None = None
    status: str


class AddFileSchema(SQLModel):
    task_id: int
    file_name: str
    file_data: bytes
    file_type: str


class GetLabsSchema(SQLModel):
    user_id: int


class GetLabResponseSchema(SQLModel):
    task_id: int
    user_id: int
    discipline_id: int
    name: str
    task_text: str | None = None
    task_link: str | None = None
    start_date: date
    end_date: date
    extra_info: str | None = None
    status: Status


class GetLabsResponseSchema(SQLModel):
    labs: list[GetLabResponseSchema]


class GetLabFilesSchema(SQLModel):
    task_id: int


class GetFileResponseSchema(SQLModel):
    file_id: int
    task_id: int
    file_name: str
    file_data: bytes
    file_type: str


class GetLabFilesResponseSchema(SQLModel):
    files: list[GetFileResponseSchema]


class EditLabAttributeSchema(SQLModel):
    task_id: int
    editing_attribute: str
    editing_value: str


class DeleteLabSchema(SQLModel):
    task_id: int
