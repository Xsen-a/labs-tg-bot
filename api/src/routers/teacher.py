from fastapi import APIRouter

from api.src.schemas import AddTeacherSchema
from api.src.handlers.teacher import add_teacher_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_teacher", tags=["admin"])
async def add_teacher_router(schema: AddTeacherSchema, session: SessionDep):
    return add_teacher_handler(session, schema)