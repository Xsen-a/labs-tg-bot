import uvicorn

from fastapi import FastAPI
from .database import SessionDep
from .routers import authorization, teacher, utils, authentication, student, admin

def create_app() -> FastAPI:
    """
    Создает и настраивает экземпляр FastAPI приложения.
    """
    app = FastAPI()

    # Подключение маршрутов
    app.include_router(authorization.router)
    app.include_router(teacher.router)
    app.include_router(utils.router)
    app.include_router(authentication.router)
    app.include_router(student.router)
    app.include_router(admin.router)

    # Пример базового маршрута
    @app.get("/")
    async def read_root(session: SessionDep):
        return {"Ответ сервера": "Привет от FastAPI!"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)