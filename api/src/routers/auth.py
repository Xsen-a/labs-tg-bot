from fastapi import APIRouter

from api.src.schemas import CheckUserSchema, AddUserSchema
from api.src.handlers.auth import check_user_handler, add_user_handler

from api.src.database import SessionDep

router = APIRouter()


@router.get("/check_user", tags=["admin"])
async def check_user_router(schema: CheckUserSchema, session: SessionDep):
    return check_user_handler(session, schema)


@router.post("/add_user", tags=["admin"])
async def check_user_router(schema: AddUserSchema, session: SessionDep):
    return add_user_handler(session, schema)