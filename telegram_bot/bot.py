import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from telegram_bot.handlers import management, profile


async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Bot Token not found")

    dp = Dispatcher()
    dp.include_routers(profile.router, management.router)
    async with Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)) as bot:
        await dp.start_polling(bot, close_bot_session=False)


if __name__ == "__main__":
    asyncio.run(main())
