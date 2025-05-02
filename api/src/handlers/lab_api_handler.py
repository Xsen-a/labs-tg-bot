from sqlmodel import Session, select, delete, update
from api.src.schemas import AddLabSchema, AddFileSchema, GetLabsSchema, GetLabsResponseSchema, GetLabResponseSchema, \
    GetLabFilesSchema, GetFileResponseSchema, GetLabFilesResponseSchema, EditLabAttributeSchema, DeleteFilesSchema
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
    return {f"Файл {schema} добавлен."}


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


def get_lab_files_handler(session: Session, schema: GetLabFilesSchema) -> GetLabFilesResponseSchema:
    files_query = select(File).where(File.task_id == schema.task_id)
    files = session.exec(files_query).all()
    files_list = []
    for file in files:
        files_list.append(GetFileResponseSchema(
            file_id=file.file_id,
            task_id=file.task_id,
            file_name=file.file_name,
            file_data=file.file_data,
            file_type=file.file_type
        ))

    return GetLabFilesResponseSchema(files=files_list)


def edit_lab_attribute_handler(session: Session, schema: EditLabAttributeSchema):
    # update_data = {schema.editing_attribute : schema.editing_value}
    # discipline_query = update(Discipline).where(Discipline.discipline_id == schema.discipline_id).values(**update_data)
    lab_query = select(Task).where(Task.task_id == schema.task_id)
    lab = session.exec(lab_query).first()

    print(schema.editing_attribute)

    if schema.editing_attribute == "discipline_id":
        editing_value = int(schema.editing_value)
    else:
        editing_value = str(schema.editing_value)

    if schema.editing_attribute == "status":
        editing_value = Status[schema.editing_value]
        print(editing_value)

    if lab:
        setattr(lab, schema.editing_attribute, editing_value)
        # session.add(discipline)
        session.commit()
        # session.refresh(discipline)
        return lab
    else:
        raise ValueError(f"Лабораторная работа с ID {schema.task_id} не найдена")


def delete_lab_handler(session: Session, schema: DeleteFilesSchema):
    lab_query = select(Task).where(Task.task_id == schema.task_id)
    lab = session.exec(lab_query).first()

    if lab:
        try:
            session.exec(delete(File).where(File.task_id == schema.task_id))
            session.exec(delete(Task).where(Task.task_id == schema.task_id))
            session.commit()
            return {"message": f"Лабораторная работа удалена."}

        except Exception as e:
            session.rollback()
            raise ValueError(f"Ошибка при удалении файлов: {str(e)}")


def delete_files_handler(session: Session, schema: DeleteFilesSchema):
    files_query = select(File).where(File.task_id == schema.task_id)
    files = session.exec(files_query).all()

    if files:
        try:
            session.exec(delete(File).where(File.task_id == schema.task_id))
            session.commit()
            return {"message": f"Удалено {len(files)} файлов для задачи {schema.task_id}"}

        except Exception as e:
            session.rollback()
            raise ValueError(f"Ошибка при удалении файлов: {str(e)}")


