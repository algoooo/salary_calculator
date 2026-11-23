from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import WorkDay
from database.crud import users
from database.crud import workdays
from database.session import get_session_factory
from database.models.user import User

from bot.keyboards.keyboards import start_mk
from bot.classes.states import RegistrationStates, UpdateUserState

from bot.texts.answers import answer

factory = get_session_factory()
router = Router()


@router.callback_query(F.data=="my_workdays")
async def my_workdays(message: types.Message):
    async with factory.begin() as session:
        user: User | None = await users.get_user(session, message.chat.id)
        if user is None:
            return await message.answer(answer("questions.not_registered"))
        user_workdays: list[WorkDay] | [] = await workdays.get_user_workdays(session, message.chat.id)
        if user_workdays == []:
            return await message.answer(answer("workdays.no_workdays_found"))
        sa
@router.message(F.text.contains("Дата"))
async def add_workday(message: types.Message):
    pass
