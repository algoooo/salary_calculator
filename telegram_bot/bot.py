import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import GetMe
from dotenv import load_dotenv

from telegram_bot.handlers import management, profile

load_dotenv()
logger = logging.getLogger(__name__)
PROXY_CHECK_TIMEOUT = 10


@asynccontextmanager
async def bot_connection(token: str, proxies: list[str]):
    defaults = DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    if not proxies:
        async with Bot(token=token, default=defaults) as bot:
            yield bot
        return

    for index, proxy in enumerate(proxies, start=1):
        try:
            session = AiohttpSession(proxy=proxy)
        except ValueError:
            logger.warning("Telegram proxy %d has an invalid URL", index)
            continue

        async with Bot(token=token, session=session, default=defaults) as bot:
            try:
                await bot(GetMe(), request_timeout=PROXY_CHECK_TIMEOUT)
            except (TelegramNetworkError, TimeoutError, OSError):
                logger.warning("Telegram proxy %d could not reach Telegram", index)
                continue

            yield bot
            return

    raise RuntimeError(f"None of the {len(proxies)} configured Telegram proxies could connect")


async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Bot Token not found")

    dp = Dispatcher()
    dp.include_routers(profile.router, management.router)
    proxies = [url.strip() for url in os.getenv("BOT_PROXY_URLS", "").split(",") if url.strip()]
    if not proxies:
        proxy_url = os.getenv("BOT_PROXY_URLS", "").strip()
        if proxy_url:
            proxies.append(proxy_url)

    async with bot_connection(token, proxies) as bot:
        await dp.start_polling(bot, close_bot_session=False)


if __name__ == "__main__":
    asyncio.run(main())
