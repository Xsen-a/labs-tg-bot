from fastapi import APIRouter

from api.src.schemas import AddLabSchema
from api.src.handlers.lab_api_handler import add_lab_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_discipline", tags=["disciplines"])
async def add_discipline_router(schema: AddLabSchema, session: SessionDep):
    return add_lab_handler(session, schema)
