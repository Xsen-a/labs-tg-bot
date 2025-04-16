from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .settings import settings
from aiogram import Bot

TOKEN = settings.BOT_TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))