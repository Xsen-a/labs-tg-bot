from sqlmodel import Session, select
from api.src.schemas import AddTeacherSchema
from api.src.models import Teacher, User


def add_teacher_handler(session: Session, schema: AddTeacherSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()
    new_item = Teacher(
        user_id=user.user_id,
        name=schema.name,
        phone_number=schema.phone_number,
        email=schema.email,
        social_page_link=schema.social_page_link,
        classroom=schema.classroom,
        is_from_API=schema.is_from_API
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Преподаватель {schema} добавлен."}


def get_teachers_handler(session: Session, schema: AddTeacherSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()
    new_item = Teacher(
        user_id=user.user_id,
        name=schema.name,
        phone_number=schema.phone_number,
        email=schema.email,
        social_page_link=schema.social_page_link,
        classroom=schema.classroom,
        is_from_API=schema.is_from_API
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Преподаватель {schema} добавлен."}