from fastapi import APIRouter

from api.src.schemas import AddTeacherSchema, GetTeachersSchema
from api.src.handlers.teacher_api_handler import add_teacher_handler, get_teachers_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_teacher", tags=["admin"])
async def add_teacher_router(schema: AddTeacherSchema, session: SessionDep):
    return add_teacher_handler(session, schema)


@router.get("/get_teachers", tags=["admin"])
async def get_teachers_router(schema: GetTeachersSchema, session: SessionDep):
    return get_teachers_handler(session, schema)
