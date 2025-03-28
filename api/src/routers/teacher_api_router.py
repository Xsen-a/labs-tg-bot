from fastapi import APIRouter

from api.src.schemas import AddTeacherSchema, GetTeachersSchema, GetTeacherSchema, GetTeacherApiStatusSchema,\
    EditTeacherAttributeSchema, DeleteTeacherSchema
from api.src.handlers.teacher_api_handler import add_teacher_handler, get_teachers_handler, get_teacher_handler,\
    get_teacher_api_status_handler, edit_teacher_attribute_handler, delete_teacher_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_teacher", tags=["teachers"])
async def add_teacher_router(schema: AddTeacherSchema, session: SessionDep):
    return add_teacher_handler(session, schema)


@router.get("/get_teachers", tags=["teachers"])
async def get_teachers_router(schema: GetTeachersSchema, session: SessionDep):
    return get_teachers_handler(session, schema)


@router.get("/get_teacher", tags=["teachers"])
async def get_teacher_router(schema: GetTeacherSchema, session: SessionDep):
    return get_teacher_handler(session, schema)


@router.get("/get_teacher_api_status", tags=["teachers"])
async def get_teacher_api_status_router(schema: GetTeacherApiStatusSchema, session: SessionDep):
    return get_teacher_api_status_handler(session, schema)


@router.post("/edit_teacher", tags=["teachers"])
async def edit_teacher_attribute_router(schema: EditTeacherAttributeSchema, session: SessionDep):
    return edit_teacher_attribute_handler(session, schema)


@router.delete("/delete_teacher", tags=["teachers"])
async def delete_teacher_router(schema: DeleteTeacherSchema, session: SessionDep):
    return delete_teacher_handler(session, schema)

