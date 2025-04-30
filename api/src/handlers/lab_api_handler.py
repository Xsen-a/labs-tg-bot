from sqlmodel import Session, select, delete, update
from api.src.schemas import AddLabSchema, AddFileSchema, GetLabsSchema, GetLabsResponseSchema, GetLabResponseSchema
from api.src.models import Task, User, Status, File, FileType


status_dict = {
    "not_started": Status.not_started,
    "in_progress": Status.in_progress,
    "done": Status.done,
    "submitted": Status.submitted
}

file_type_dict = {
    "document": FileType.document,
    "photo": FileType.photo,
    "audio": FileType.audio,
    "video": FileType.video
}


def add_lab_handler(session: Session, schema: AddLabSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()
    print(schema)
    new_item = Task(
        user_id=user.user_id,
        discipline_id=schema.discipline_id,
        name=schema.name,
        task_text=schema.task_text,
        task_link=schema.task_link,
        start_date=schema.start_date,
        end_date=schema.end_date,
        extra_info=schema.extra_info,
        status=status_dict[schema.status]
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {"task_id": new_item.task_id}


def add_file_handler(session: Session, schema: AddFileSchema):
    new_item = File(
        task_id=schema.task_id,
        file_name=schema.file_name,
        file_data=schema.file_data,
        file_type=file_type_dict[schema.file_type]
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Лабораторная работа {schema} добавлена."}


def get_labs_handler(session: Session, schema: GetLabsSchema) -> GetLabsResponseSchema:
    user_query = select(Task).where(Task.user_id == schema.user_id)
    labs = session.exec(user_query).all()
    labs_list = []
    for lab in labs:
        labs_list.append(GetLabResponseSchema(
            task_id=lab.task_id,
            user_id=lab.user_id,
            discipline_id=lab.discipline_id,
            name=lab.name,
            task_text=lab.task_text,
            task_link=lab.task_link,
            start_date=lab.start_date,
            end_date=lab.end_date,
            extra_info=lab.extra_info,
            status=lab.status.value
        ))

    return GetLabsResponseSchema(labs=labs_list)
