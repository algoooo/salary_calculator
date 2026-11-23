from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



start_mk = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Мои рабочие дни", callback_data="my_workdays"),
        InlineKeyboardButton(text="Изменить ставку", callback_data="profile_change_per_hour"),
        InlineKeyboardButton(text="Изменить процент", callback_data="profile_change_sales_percent"),
        InlineKeyboardButton(text="Удалить профиль", callback_data="profile_delete")
    ]
])