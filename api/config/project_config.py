from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    class Config:
        env_file = ".env"  # Путь к .env файлу относительно этого сервиса
        env_file_encoding = 'utf-8'
        extra = "allow"


settings = Settings()
