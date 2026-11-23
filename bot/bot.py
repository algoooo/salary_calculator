from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
load_dotenv()

token: str | None = os.getenv("BOT_TOKEN")
if token is None:
    raise Exception("Bot Token not found")

BOT = Bot(token=token)
dp = Dispatcher()

dp.start_polling(BOT)