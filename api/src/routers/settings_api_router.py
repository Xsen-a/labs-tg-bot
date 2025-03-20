from fastapi import APIRouter

from api.src.schemas import ChangeUserGroupSchema, ChangeUserStatusSchema
from api.src.handlers.settings_api_handler import change_user_group_handler, change_user_status_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/change_user_group", tags=["admin"])
async def change_user_group_router(schema: ChangeUserGroupSchema, session: SessionDep):
    return change_user_group_handler(session, schema)


@router.post("/change_user_status", tags=["admin"])
async def change_user_status_router(schema: ChangeUserStatusSchema, session: SessionDep):
    return change_user_status_handler(session, schema)