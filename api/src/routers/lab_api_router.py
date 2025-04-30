from fastapi import APIRouter

from api.src.schemas import AddLabSchema, AddFileSchema, GetLabsSchema
from api.src.handlers.lab_api_handler import add_lab_handler, add_file_handler, get_labs_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_lab", tags=["labs"])
async def add_discipline_router(schema: AddLabSchema, session: SessionDep):
    return add_lab_handler(session, schema)


@router.post("/add_file", tags=["labs"])
async def add_file_router(schema: AddFileSchema, session: SessionDep):
    return add_file_handler(session, schema)


@router.get("/get_labs", tags=["tasks"])
async def get_labs_router(schema: GetLabsSchema, session: SessionDep):
    return get_labs_handler(session, schema)