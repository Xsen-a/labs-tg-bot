from sqlmodel import Session, select
from api.src.schemas import AddTeacherSchema, GetTeachersSchema, GetTeachersResponseSchema, GetTeacherSchema, GetTeacherResponseSchema
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


def get_teachers_handler(session: Session, schema: GetTeachersSchema) -> GetTeachersResponseSchema:
    user_query = select(Teacher).where(Teacher.user_id == schema.user_id)
    teachers = session.exec(user_query).all()
    teachers_list = []
    for teacher in teachers:
        teachers_list.append(GetTeacherResponseSchema(
            user_id=teacher.user_id,
            teacher_id=teacher.teacher_id,
            name=teacher.name,
            phone_number=teacher.phone_number,
            email=teacher.email,
            social_page_link=teacher.social_page_link,
            classroom=teacher.classroom,
            is_from_API=teacher.is_from_API
        ))

    return GetTeachersResponseSchema(teachers=teachers_list)


def get_teacher_handler(session: Session, schema: GetTeacherSchema) -> GetTeacherResponseSchema:
    teacher_query = select(Teacher).where((Teacher.user_id == schema.user_id) & (Teacher.teacher_id == schema.teacher_id))
    print(teacher_query)
    teacher = session.exec(teacher_query).first()
    get_teacher = GetTeacherResponseSchema(
        user_id=teacher.user_id,
        teacher_id=teacher.teacher_id,
        name=teacher.name,
        phone_number=teacher.phone_number,
        email=teacher.email,
        social_page_link=teacher.social_page_link,
        classroom=teacher.classroom,
        is_from_API=teacher.is_from_API
    )

    return get_teacher
