from aiogram.fsm.state import StatesGroup, State


class RegistrationStates(StatesGroup):
    Enter_hourly_rate = State()
    Enter_sales_percent = State()

class UpdateUserState(StatesGroup):
    Enter_new_hourly_rate = State()
    Enter_new_sales_percent = State()