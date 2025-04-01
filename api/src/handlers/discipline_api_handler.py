from sqlmodel import Session, select, delete, update
from api.src.schemas import AddDisciplineSchema, GetDisciplinesSchema, GetDisciplinesResponseSchema, GetDisciplineSchema, \
    GetDisciplineResponseSchema, GetDisciplineApiStatusSchema, GetDisciplineApiStatusResponseSchema, EditDisciplineAttributeSchema,\
    DeleteDisciplineSchema
from api.src.models import Discipline, User


def add_discipline_handler(session: Session, schema: AddDisciplineSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()
    new_item = Discipline(
        user_id=user.user_id,
        teacher_id=schema.teacher_id,
        name=schema.name,
        is_from_API=schema.is_from_API
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {f"Дисциплина {schema} добавлена."}


def get_disciplines_handler(session: Session, schema: GetDisciplinesSchema) -> GetDisciplinesResponseSchema:
    user_query = select(Discipline).where(Discipline.user_id == schema.user_id)
    disciplines = session.exec(user_query).all()
    disciplines_list = []
    for discipline in disciplines:
        disciplines_list.append(GetDisciplineResponseSchema(
            user_id=discipline.user_id,
            teacher_id=discipline.teacher_id,
            name=discipline.name,
            is_from_API=discipline.is_from_API
        ))

    return GetDisciplinesResponseSchema(disciplines=disciplines_list)


def get_discipline_handler(session: Session, schema: GetDisciplineSchema) -> GetDisciplineResponseSchema:
    discipline_query = select(Discipline).where(Discipline.discipline_id == schema.discipline_id)
    discipline = session.exec(discipline_query).first()
    get_discipline = GetDisciplineResponseSchema(
        user_id=discipline.user_id,
        teacher_id=discipline.teacher_id,
        name=discipline.name,
        is_from_API=discipline.is_from_API
    )

    return get_discipline


def get_discipline_api_status_handler(session: Session, schema: GetDisciplineApiStatusSchema) -> GetDisciplineApiStatusResponseSchema:
    discipline_query = select(Discipline).where(Discipline.discipline_id == schema.discipline_id)
    discipline = session.exec(discipline_query).first()
    return GetDisciplineApiStatusResponseSchema(is_from_API=discipline.is_from_API)


def edit_discipline_attribute_handler(session: Session, schema: EditDisciplineAttributeSchema):
    # update_data = {schema.editing_attribute : schema.editing_value}
    # discipline_query = update(Discipline).where(Discipline.discipline_id == schema.discipline_id).values(**update_data)
    discipline_query = select(Discipline).where(Discipline.discipline_id == schema.discipline_id)
    discipline = session.exec(discipline_query).first()

    if discipline:
        setattr(discipline, schema.editing_attribute, schema.editing_value)
        # session.add(discipline)
        session.commit()
        # session.refresh(discipline)
        return discipline
    else:
        raise ValueError(f"Дисциплина с ID {schema.discipline_id} не найдена")


def delete_discipline_handler(session: Session, schema: DeleteDisciplineSchema):
    discipline_query = select(Discipline).where(Discipline.discipline_id == schema.discipline_id)
    discipline = session.exec(discipline_query).first()

    if discipline:
        session.exec(delete(Discipline).where(Discipline.discipline_id == schema.discipline_id))
        session.commit()
    else:
        raise ValueError(f"Дисциплина с ID {schema.discipline_id} не найдена")
