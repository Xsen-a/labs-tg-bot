import asyncio
import logging
import sys
from .settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n, FSMI18nMiddleware
from typing import Any

from .handlers import main_bot_handler as main_handler, settings_bot_handler as settings_handler,\
    auth_bot_handler as auth_handler, teacher_bot_handler as teacher_handler, discipline_bot_handler as discipline_handler,\
    lab_bot_handler as lab_handler

from bot.src.bot_unit import bot as bot_unit

TOKEN = settings.BOT_TOKEN


class BotI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        return 'ru'


async def main() -> None:
    bot = bot_unit

    dp = Dispatcher()

    # Настройка i18n
    i18n = I18n(path="locales", default_locale="ru", domain="messages")
    i18n_middleware = FSMI18nMiddleware(i18n)


    # Добавление middleware в диспетчер
    dp.message.outer_middleware(i18n_middleware)
    FSMI18nMiddleware(i18n).setup(dp)

    # Добавление роутеров из всех handler
    dp.include_routers(main_handler.router)
    dp.include_routers(auth_handler.router)
    dp.include_routers(settings_handler.router)
    dp.include_routers(teacher_handler.router)
    dp.include_routers(discipline_handler.router)
    dp.include_routers(lab_handler.router)

    # logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())