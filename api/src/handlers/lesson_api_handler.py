from datetime import datetime

from sqlmodel import Session, select, delete, update
from api.src.schemas import AddLessonSchema, GetLessonsSchema, GetLessonsResponseSchema, GetLessonResponseSchema, \
    EditLessonAttributeSchema, DeleteLessonSchema
from api.src.models import Lesson, User


def add_lesson_handler(session: Session, schema: AddLessonSchema):
    user_query = select(User).where(User.user_id == schema.user_id)
    user = session.exec(user_query).first()

    new_item = Lesson(
        user_id=user.user_id,
        discipline_id=schema.discipline_id,
        classroom=schema.classroom,
        start_date=schema.start_date,
        start_time=schema.start_time,
        end_time=schema.end_time,
        periodicity_days=schema.periodicity_days
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {"Занятие добавлено."}


def get_lessons_handler(session: Session, schema: GetLessonsSchema) -> GetLessonsResponseSchema:
    user_query = select(Lesson).where(Lesson.user_id == schema.user_id)
    lessons = session.exec(user_query).all()
    lessons_list = []
    for lesson in lessons:
        lessons_list.append(GetLessonResponseSchema(
            lesson_id=lesson.lesson_id,
            user_id=lesson.user_id,
            discipline_id=lesson.discipline_id,
            classroom=lesson.classroom,
            start_date=lesson.start_date.date(),
            start_time=lesson.start_time,
            end_time=lesson.end_time,
            pretiodicity_days=lesson.periodicity_days
        ))

    return GetLessonsResponseSchema(lessons=lessons_list)


def edit_lesson_attribute_handler(session: Session, schema: EditLessonAttributeSchema):
    # update_data = {schema.editing_attribute : schema.editing_value}
    # discipline_query = update(Discipline).where(Discipline.discipline_id == schema.discipline_id).values(**update_data)
    lesson_query = select(Lesson).where(Lesson.lesson_id == schema.lesson_id)
    lesson = session.exec(lesson_query).first()

    print(schema.editing_attribute)

    if schema.editing_attribute == "discipline_id":
        editing_value = int(schema.editing_value)
    else:
        editing_value = str(schema.editing_value)


    if lesson:
        setattr(lesson, schema.editing_attribute, editing_value)
        # session.add(discipline)
        session.commit()
        # session.refresh(discipline)
        return lesson
    else:
        raise ValueError(f"Лабораторная работа с ID {schema.task_id} не найдена")


def delete_lesson_handler(session: Session, schema: DeleteLessonSchema):
    lesson_query = select(Lesson).where(Lesson.lesson_id == schema.lesson_id)
    lesson = session.exec(lesson_query).first()

    if lesson:
        try:
            session.exec(delete(Lesson).where(Lesson.lesson_id == schema.lesson_id))
            session.commit()
            return {"message": f"Лабораторная работа удалена."}

        except Exception as e:
            session.rollback()
            raise ValueError(f"Ошибка при удалении файлов: {str(e)}")



