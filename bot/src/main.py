import asyncio
import logging
import sys
from .settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n
from typing import Any

# Логирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

TOKEN = settings.BOT_TOKEN

class BotI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        return 'ru'  # Устанавливаем локаль 'ru'

async def main() -> None:
    logger.info("Инициализация бота...")
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Настройка i18n
    logger.info("Инициализация i18n...")
    i18n = I18n(path="src/locales", default_locale="ru", domain="messages")
    i18n_middleware = BotI18nMiddleware(i18n)

    # Добавление middleware в диспетчер
    logger.info("Добавление middleware...")
    dp.message.middleware(i18n_middleware)

    # Импорт handlers после инициализации i18n
    logger.info("Импорт handlers...")
    from .handlers import main_handler

    # Добавление роутеров из всех handler
    logger.info("Добавление роутеров...")
    dp.include_routers(main_handler.router)

    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())