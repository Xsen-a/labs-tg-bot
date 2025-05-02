from fastapi import APIRouter

from api.src.schemas import AddLabSchema, AddFileSchema, GetLabsSchema, GetLabFilesSchema, EditLabAttributeSchema
from api.src.handlers.lab_api_handler import add_lab_handler, add_file_handler, get_labs_handler, get_lab_files_handler,\
    edit_lab_attribute_handler

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


@router.get("/get_lab_files", tags=["tasks"])
async def get_lab_files_router(schema: GetLabFilesSchema, session: SessionDep):
    return get_lab_files_handler(session, schema)


@router.post("/edit_lab", tags=["tasks"])
async def edit_lab_attribute_router(schema: EditLabAttributeSchema, session: SessionDep):
    return edit_lab_attribute_handler(session, schema)
