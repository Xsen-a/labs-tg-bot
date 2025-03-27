from sqlmodel import Session, select
from api.src.schemas import CheckUserExistSchema, CheckUserExistResponseSchema, AddUserSchema, CheckPetrsuStudentSchema, \
    CheckPetrsuStudentResponseSchema, GetUserIdSchema, GetUserIdResponseSchema, GetUserGroupSchema, GetUserGroupResponseSchema
from api.src.models import User


def get_user_id_by_tg_handler(session: Session, schema: GetUserIdSchema) -> GetUserIdResponseSchema:
    user_query = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user_query).first()
    if user:
        return GetUserIdResponseSchema(user_id=user.user_id)
    else:
        raise ValueError(f"Пользователь с Telegram ID {schema.telegram_id} не найден")


def get_user_group_by_tg_handler(session: Session, schema: GetUserGroupSchema) -> GetUserGroupResponseSchema:
    user_query = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user_query).first()
    if user:
        return GetUserGroupResponseSchema(group=user.group)
    else:
        raise ValueError(f"Пользователь с Telegram ID {schema.telegram_id} не найден")


def check_user_handler(session: Session, schema: CheckUserExistSchema) -> CheckUserExistResponseSchema:
    user_query = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user_query).first()
    if user:
        return CheckUserExistResponseSchema(exists=True)
    else:
        return CheckUserExistResponseSchema(exists=False)


def check_is_petrsu_student_handler(session: Session,
                                    schema: CheckPetrsuStudentSchema) -> CheckPetrsuStudentResponseSchema:
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
