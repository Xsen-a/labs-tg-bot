from fastapi import APIRouter

from api.src.schemas import CheckUserExistSchema, AddUserSchema, CheckPetrsuStudentSchema, GetUserIdSchema, GetUserGroupSchema
from api.src.handlers.auth_api_handler import check_user_handler, add_user_handler, check_is_petrsu_student_handler,\
    get_user_id_by_tg_handler, get_user_group_by_tg_handler

from api.src.database import SessionDep

router = APIRouter()


@router.get("/get_user_id", tags=["user"])
async def get_user_id_by_tg_router(schema: GetUserIdSchema, session: SessionDep):
    return get_user_id_by_tg_handler(session, schema)


@router.get("/get_user_group", tags=["user"])
async def get_user_group_by_tg_router(schema: GetUserGroupSchema, session: SessionDep):
    return get_user_group_by_tg_handler(session, schema)

@router.get("/check_user", tags=["user"])
async def check_user_router(schema: CheckUserExistSchema, session: SessionDep):
    return check_user_handler(session, schema)


@router.get("/check_is_petrsu_student", tags=["user"])
async def check_user_router(schema: CheckPetrsuStudentSchema, session: SessionDep):
    return check_is_petrsu_student_handler(session, schema)


@router.post("/add_user", tags=["user"])
async def check_user_router(schema: AddUserSchema, session: SessionDep):
    return add_user_handler(session, schema)