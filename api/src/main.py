import uvicorn

from fastapi import FastAPI
from .database import SessionDep
from .routers import teacher, auth

def create_app() -> FastAPI:
    """
    Создает и настраивает экземпляр FastAPI приложения.
    """
    app = FastAPI()

    # Подключение маршрутов
    app.include_router(teacher.router)
    app.include_router(auth.router)

    # Пример базового маршрута
    @app.get("/")
    async def read_root(session: SessionDep):
        return {"Ответ сервера": "Привет от FastAPI!"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("api.src.main:app", host="0.0.0.0", port=8000, reload=True)