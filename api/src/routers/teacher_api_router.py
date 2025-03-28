from fastapi import APIRouter

from api.src.schemas import AddTeacherSchema, GetTeachersSchema, GetTeacherSchema, GetTeacherApiStatusSchema,\
    EditTeacherAttributeSchema
from api.src.handlers.teacher_api_handler import add_teacher_handler, get_teachers_handler, get_teacher_handler,\
    get_teacher_api_status_handler, edit_teacher_attribute_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_teacher", tags=["admin"])
async def add_teacher_router(schema: AddTeacherSchema, session: SessionDep):
    return add_teacher_handler(session, schema)


@router.get("/get_teachers", tags=["admin"])
async def get_teachers_router(schema: GetTeachersSchema, session: SessionDep):
    return get_teachers_handler(session, schema)


@router.get("/get_teacher", tags=["admin"])
async def get_teacher_router(schema: GetTeacherSchema, session: SessionDep):
    return get_teacher_handler(session, schema)


@router.get("/get_teacher_api_status", tags=["admin"])
async def get_teacher_api_status_router(schema: GetTeacherApiStatusSchema, session: SessionDep):
    return get_teacher_api_status_handler(session, schema)


@router.post("/edit_teacher", tags=["admin"])
async def edit_teacher_attribute_router(schema: EditTeacherAttributeSchema, session: SessionDep):
    return edit_teacher_attribute_handler(session, schema)
