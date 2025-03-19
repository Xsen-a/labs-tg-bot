from fastapi import APIRouter

from api.src.schemas import ChangeUserGroupSchema
from api.src.handlers.settings_api_handler import change_user_group_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/change_user_group", tags=["admin"])
async def change_user_group_router(schema: ChangeUserGroupSchema, session: SessionDep):
    return change_user_group_handler(session, schema)