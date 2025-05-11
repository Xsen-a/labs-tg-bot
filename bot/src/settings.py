from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_URL: str
    openAI_API_KEY: str

    class Config:
        env_file = ".env"  # Путь к .env файлу относительно этого сервиса
        env_file_encoding = 'utf-8'
        extra = "allow"

settings = Settings()
