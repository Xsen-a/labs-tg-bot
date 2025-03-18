from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Session
from ..config.project_config import settings


SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
