from fastapi import APIRouter

from api.src.schemas import AddDisciplineSchema, GetDisciplinesSchema, GetDisciplineSchema, GetDisciplineApiStatusSchema,\
    EditDisciplineAttributeSchema, DeleteDisciplineSchema
from api.src.handlers.discipline_api_handler import add_discipline_handler, get_disciplines_handler, get_discipline_handler,\
    get_discipline_api_status_handler, edit_discipline_attribute_handler, delete_discipline_handler

from api.src.database import SessionDep

router = APIRouter()


@router.post("/add_discipline", tags=["disciplines"])
async def add_discipline_router(schema: AddDisciplineSchema, session: SessionDep):
    return add_discipline_handler(session, schema)


@router.get("/get_disciplines", tags=["disciplines"])
async def get_disciplines_router(schema: GetDisciplinesSchema, session: SessionDep):
    return get_disciplines_handler(session, schema)


@router.get("/get_discipline", tags=["disciplines"])
async def get_discipline_router(schema: GetDisciplineSchema, session: SessionDep):
    return get_discipline_handler(session, schema)


@router.get("/get_discipline_api_status", tags=["disciplines"])
async def get_discipline_api_status_router(schema: GetDisciplineApiStatusSchema, session: SessionDep):
    return get_discipline_api_status_handler(session, schema)


@router.post("/edit_discipline", tags=["disciplines"])
async def edit_discipline_attribute_router(schema: EditDisciplineAttributeSchema, session: SessionDep):
    return edit_discipline_attribute_handler(session, schema)


@router.delete("/delete_discipline", tags=["disciplines"])
async def delete_discipline_router(schema: DeleteDisciplineSchema, session: SessionDep):
    return delete_discipline_handler(session, schema)
