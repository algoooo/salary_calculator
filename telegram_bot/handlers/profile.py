from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.crud import users
from database.session import get_session_factory

from telegram_bot.classes.states import RegistrationStates, UpdateUserState
from telegram_bot.keyboards.keyboard_tools import construct_keyboard
from telegram_bot.keyboards.keyboards import start_mk
from telegram_bot.texts.answers import answer

router = Router()


def _parse_profile_number(text: str | None) -> int:
    value = int(text or "")
    if not -(2**31) <= value < 2**31:
        raise ValueError("Profile value is outside the database integer range")
    return value


@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    async with get_session_factory().begin() as session:
        user = await users.get_user(session, message.chat.id)

    if user is None:
        await state.set_state(RegistrationStates.Enter_hourly_rate)
        await message.answer(answer("questions.enter_rate"))
        return

    greeting = answer("profile.greeting", username=user.username)
    per_hour = answer("profile.rate", hourly_rate=user.salary_per_hour, sales_percent=user.sales_percent)
    choose_action = answer("profile.choose_action")
    await message.answer(f"{greeting}\n{per_hour}\n{choose_action}", reply_markup=start_mk)


@router.callback_query(F.data.in_({"profile_change_per_hour", "profile_change_sales_percent"}))
async def update_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not isinstance(callback.message, types.Message):
        return

    async with get_session_factory().begin() as session:
        user = await users.get_user(session, callback.from_user.id)
    if user is None:
        await callback.message.answer(answer("questions.not_registered"))
        return

    await state.clear()
    if callback.data == "profile_change_per_hour":
        await state.set_state(UpdateUserState.Enter_new_hourly_rate)
        await callback.message.answer(answer("update_user.update_salary"))
    else:
        await state.set_state(UpdateUserState.Enter_new_sales_percent)
        await callback.message.answer(answer("update_user.update_percent"))


@router.message(UpdateUserState.Enter_new_hourly_rate)
@router.message(UpdateUserState.Enter_new_sales_percent)
async def save_profile_change(message: types.Message, state: FSMContext):
    field = "salary_per_hour"
    if await state.get_state() == UpdateUserState.Enter_new_sales_percent.state:
        field = "sales_percent"

    try:
        value = _parse_profile_number(message.text)
    except ValueError:
        await message.answer(answer("update_user.error"))
        return

    async with get_session_factory().begin() as session:
        user = await users.update_user(session, message.from_user.id, **{field: value})

    if user is not None:
        await message.answer(answer("update_user.ok"))
    await start(message, state)


@router.callback_query(F.data == "profile_delete")
async def confirm_profile_deletion(callback: types.CallbackQuery):
    await callback.answer()
    if isinstance(callback.message, types.Message):
        await callback.message.answer(
            answer("profile.confirm_delete"),
            reply_markup=construct_keyboard({answer("profile.delete"): "profile_delete_confirm"}),
        )


@router.callback_query(F.data == "profile_delete_confirm")
async def delete_profile(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not isinstance(callback.message, types.Message):
        return

    async with get_session_factory().begin() as session:
        deleted = await users.delete_user(session, callback.from_user.id)

    await state.clear()
    text = "profile.deleted" if deleted else "questions.not_registered"
    await callback.message.edit_text(answer(text))


@router.message(RegistrationStates.Enter_hourly_rate)
async def _get_hourly_rate(message: types.Message, state: FSMContext):
    try:
        rate = _parse_profile_number(message.text)
    except ValueError:
        await message.answer(answer("questions.incorrect_input"))
        return

    await state.update_data(per_hour=rate)
    await state.set_state(RegistrationStates.Enter_sales_percent)
    await message.answer(answer("questions.moving_forward"))


@router.message(RegistrationStates.Enter_sales_percent)
async def _get_sales_percent(message: types.Message, state: FSMContext):
    try:
        percent = _parse_profile_number(message.text)
    except ValueError:
        await message.answer(answer("questions.incorrect_input"))
        return

    data = await state.get_data()
    sender = message.from_user
    async with get_session_factory().begin() as session:
        if await users.get_user(session, sender.id) is None:
            await users.create_user(
                session,
                telegram_id=sender.id,
                username=sender.username or sender.full_name,
                per_hour=data["per_hour"],
                percent=percent,
            )
    await start(message, state)
