from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.crud import users
from database.session import get_session_factory
from database.models.user import User

from bot.keyboards.keyboards import start_mk
from bot.classes.states import RegistrationStates, UpdateUserState

from bot.texts.answers import answer

factory = get_session_factory()
router = Router()



@router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):

    async with factory.begin() as session:
        user: User | None = await users.get_user(session, telegram_id=message.from_user.id)

    if user is None:
        await _start_registration(message, state)
        return

    greeting = answer("profile.greeting", username=user.username)
    per_hour = answer("profile.rate", hourly_rate=user.salary_per_hour, sales_percent=user.sales_percent)
    choose_action = answer("profile.choose_action")

    await message.answer(
        f"{greeting} \n{per_hour}, \n{choose_action}",
        reply_markup=start_mk
    )

@router.callback_query("profile_change" in F.data)
async def update_user(callback: types.CallbackQuery, state: FSMContext):
    if "per_hour" in callback.data:
        await state.set_state(UpdateUserState.Enter_new_hourly_rate)
    elif "percent" in callback.data:
        await state.set_state(UpdateUserState.Enter_new_sales_percent)
    else:
        await callback.message.answer(answer("update_user.wrong_callback"))

@router.message(UpdateUserState.Enter_new_hourly_rate)
async def update_salary(message: types.Message, state: FSMContext):
    try:
        new_rate = int(message.text) # type: ignore
    except ValueError:
        await message.answer(answer("update_user.error"))
        return
    async with factory.begin() as session:
        try:
            user = users.update_user(session, message.from_user.id, salary_per_hour=new_rate)
        except:
            await message.answer(answer("update_user.wrong_callback"))
            return
    await state.clear()
    await message.answer(answer("update_user.ok"))
    return await start(message, state)

@router.message(UpdateUserState.Enter_new_sales_percent)
async def update_percent(message: types.Message, state: FSMContext):
    try:
        new_percent = int(message.text) # type: ignore
    except ValueError:
        await message.answer(answer("update_user.error"))
        return
    async with factory.begin() as session:
        try:
            user = users.update_user(session, message.from_user.id, sales_percent=new_percent)
        except:
            await message.answer(answer("update_user.wrong_callback"))
    await state.clear()
    await message.answer(answer("update_user.ok"))
    return await start(message, state)

# ==================== REGISTRATION =====================
async def _start_registration(message: types.Message, state: FSMContext):

    await message.answer(answer("questions.enter_rate"))
    await state.set_state(RegistrationStates.Enter_hourly_rate)

@router.message(RegistrationStates.Enter_hourly_rate)
async def _get_hourly_rate(message: types.Message, state: FSMContext):

    try:
        rate = int(message.text) # type: ignore
    except ValueError:
        await message.answer(answer("questions.incorrect_input"))
        return

    await state.update_data(per_hour=rate)
    await state.set_state(RegistrationStates.Enter_sales_percent)
    await message.answer(answer("questions.moving_forward"))

@router.message(RegistrationStates.Enter_sales_percent)
async def _get_sales_percent(message: types.Message, state: FSMContext):
    try:
        percent = int(message.text)  # type: ignore
    except ValueError:
        await message.answer(answer("questions.incorrect_input"))
        return

    await state.update_data(sales_percent=percent)


    await end_registration(message, state)


async def end_registration(message: types.Message, state: FSMContext):

    async with factory.begin() as session:
        data = await state.get_data()

        user = users.create_user(
            session,
            telegram_id=message.from_user.id,
            username=str(message.from_user.username),
            per_hour=data["per_hour"],
            percent=data["sales_percent"]
        )
    await state.clear()
    return await start(message, state)
# ==================== END OF REGISTRATION ====================


