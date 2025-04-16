from sqlmodel import Session, select, delete, update
from api.src.schemas import AddLabSchema
from api.src.models import Task, User, Status


def add_discipline_handler(session: Session, schema: AddLabSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()
    new_item = Task(
        user_id=user.user_id,
        discipline_id=schema.discipline_id,
        name=schema.name,
        task_text=schema.task_text,
        task_link=schema.task_link,
        start_date=schema.start_date,
        end_date=schema.end_date,
        extra_info=schema.extra_info,
        status=Status.not_started
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Лабораторная работа {schema} добавлена."}