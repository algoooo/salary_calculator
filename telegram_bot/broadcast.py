"""Send a one-off plain-text announcement to registered bot users."""

import argparse
import asyncio
import os
import sys

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select

from database.models import User
from database.session import get_session_factory
from telegram_bot.bot import bot_connection


async def broadcast(message: str, dry_run: bool) -> int:
    async with get_session_factory()() as session:
        recipients = (await session.scalars(select(User.telegram_id).order_by(User.telegram_id))).all()

    if dry_run:
        print(f"Dry run: {len(recipients)} registered users would receive the message.")
        return 0
    if not recipients:
        print("No registered users.")
        return 0

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not configured")
    proxies = [url.strip() for url in os.getenv("BOT_PROXY_URLS", "").split(",") if url.strip()]

    sent = 0
    async with bot_connection(token, proxies) as bot:
        try:
            for chat_id in recipients:
                try:
                    try:
                        await bot.send_message(chat_id, message, parse_mode=None)
                    except TelegramRetryAfter as error:
                        await asyncio.sleep(error.retry_after)
                        await bot.send_message(chat_id, message, parse_mode=None)
                except (TelegramForbiddenError, TelegramBadRequest) as error:
                    print(f"Delivery failed for {chat_id} ({type(error).__name__}).", file=sys.stderr)
                else:
                    sent += 1
                await asyncio.sleep(0.05)
        finally:
            print(f"Sent {sent} of {len(recipients)} messages.")

    return int(sent != len(recipients))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="Message text, or '-' to read from standard input")
    parser.add_argument("--dry-run", action="store_true", help="Count recipients without sending")
    args = parser.parse_args()
    message = sys.stdin.read() if args.message == "-" else args.message
    if not message.strip() or len(message) > 4096:
        parser.error("message must contain text and be at most 4096 characters")
    return asyncio.run(broadcast(message, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
