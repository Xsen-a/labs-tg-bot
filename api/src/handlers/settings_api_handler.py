from sqlmodel import Session, select
from api.src.schemas import ChangeUserGroupSchema
from api.src.models import User


def change_user_group_handler(session: Session, schema: ChangeUserGroupSchema):
    user = select(User).where(User.telegram_id == schema.telegram_id)
    user = session.exec(user).first()

    if user:
        user.group = schema.group
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    else:
        raise ValueError(f"Пользователь с Telegram ID {schema.telegram_id} не найден")

