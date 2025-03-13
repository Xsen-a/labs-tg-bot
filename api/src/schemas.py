"""
Этот файл содержит схемы данных для приема запроса и отправки ответа от сервера
"""

from datetime import datetime, date, time

from sqlmodel import SQLModel


class AddTeacherSchema(SQLModel):
    user_id: int
    name: str
    phone_number: str
    email: str
    social_page_link: str
    classroom: str
    is_from_API: bool
