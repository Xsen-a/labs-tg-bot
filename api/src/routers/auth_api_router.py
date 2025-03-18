from fastapi import APIRouter

from api.src.schemas import CheckUserSchema, AddUserSchema, CheckPetrsuStudentSchema
from api.src.handlers.auth_api_handler import check_user_handler, add_user_handler, check_is_petrsu_student_handler

from api.src.database import SessionDep

router = APIRouter()


@router.get("/check_user", tags=["admin"])
async def check_user_router(schema: CheckUserSchema, session: SessionDep):
    return check_user_handler(session, schema)


@router.get("/check_is_petrsu_student", tags=["admin"])
async def check_user_router(schema: CheckPetrsuStudentSchema, session: SessionDep):
    return check_is_petrsu_student_handler(session, schema)


@router.post("/add_user", tags=["admin"])
async def check_user_router(schema: AddUserSchema, session: SessionDep):
    return add_user_handler(session, schema)