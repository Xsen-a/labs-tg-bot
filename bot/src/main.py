import asyncio
import logging
import sys
from settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n
from typing import Any

from handlers import main_handler

TOKEN = settings.BOT_TOKEN

class BotI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        return 'ru'

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Настройка i18n
    i18n = I18n(path="locales", default_locale="ru", domain="messages")
    BotI18nMiddleware(i18n).setup(dp)
    i18n_middleware = BotI18nMiddleware(i18n)

    # Добавление middleware в диспетчер
    dp.message.middleware(i18n_middleware)
    dp.update.outer_middleware(BotI18nMiddleware(i18n))

    # Добавление роутеров из всех handler
    dp.include_routers(main_handler.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
