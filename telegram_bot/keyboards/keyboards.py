from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



start_mk = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мои рабочие дни", callback_data="my_workdays")],
        [InlineKeyboardButton(text="🔄 Ставка", callback_data="profile_change_per_hour")],
        [InlineKeyboardButton(text="📈 Процент", callback_data="profile_change_sales_percent")],
        [InlineKeyboardButton(text="🗑️ Удалить профиль", callback_data="profile_delete")]
])