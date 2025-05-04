from fastapi import APIRouter

from api.src.schemas import AddLessonSchema, GetLessonsSchema, EditLessonAttributeSchema, \
    DeleteLessonSchema
from api.src.handlers.lesson_api_handler import add_lesson_handler, get_lessons_handler,\
    edit_lesson_attribute_handler, delete_lesson_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_lesson", tags=["lessons"])
async def add_discipline_router(schema: AddLessonSchema, session: SessionDep):
    return add_lesson_handler(session, schema)


@router.get("/get_lessons", tags=["lessons"])
async def get_lessons_router(schema: GetLessonsSchema, session: SessionDep):
    return get_lessons_handler(session, schema)


@router.post("/edit_lesson", tags=["lessons"])
async def edit_lesson_attribute_router(schema: EditLessonAttributeSchema, session: SessionDep):
    return edit_lesson_attribute_handler(session, schema)


@router.delete("/delete_lesson", tags=["lessons"])
async def delete_lesson_router(schema: DeleteLessonSchema, session: SessionDep):
    return delete_lesson_handler(session, schema)