import asyncio
import logging
import sys
import gettext
from settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n
from sqlalchemy.dialects.postgresql import Any

from handlers import student_handler
from handlers.admin_handlers import admin_handler


TOKEN = settings.BOT_TOKEN


class BotI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        return 'ru'


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Добавление роутеров из всех handler
    dp.include_routers(student_handler.router)

    appname = 'bot'
    localedir = './locales'
    i18n = gettext.translation(appname, localedir, fallback=True, languages=['ru'])
    i18n.install()
    i18n = I18n(path="locales", default_locale="ru", domain="messages")
    BotI18nMiddleware(i18n).setup(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
