from sqlmodel import Session, select
from api.src.schemas import CheckUserSchema, CheckUserResponseSchema, AddUserSchema, CheckPetrsuStudentSchema, CheckPetrsuStudentResponseSchema
from api.src.models import User


def check_user_handler(session: Session, schema: CheckUserSchema) -> CheckUserResponseSchema:
    user_query = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user_query).first()
    if user:
        return CheckUserResponseSchema(exists=True)
    else:
        return CheckUserResponseSchema(exists=False)


def check_is_petrsu_student_handler(session: Session, schema: CheckPetrsuStudentSchema) -> CheckPetrsuStudentResponseSchema:
    user_query = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user_query).first()
    if user.is_petrsu_student:
        return CheckPetrsuStudentResponseSchema(is_petrsu_student=True, group=user.group)
    else:
        return CheckPetrsuStudentResponseSchema(is_petrsu_student=False, group=user.group)


def add_user_handler(session: Session, schema: AddUserSchema):
    new_item = User(
        telegram_id=schema.telegram_id,
        is_petrsu_student=schema.is_petrsu_student,
        group=schema.group,
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Пользователь {schema} добавлен."}