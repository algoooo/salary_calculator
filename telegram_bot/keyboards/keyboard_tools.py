from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def construct_keyboard(buttons: dict[str, str]) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for text, callback in buttons.items():
        inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def construct_button(button: list[str]):
    if len(button) != 2:
        raise Exception("Invalid button length")
    return InlineKeyboardButton(text=button[0], callback_data=button[1])

def construct_table_keyboard(buttons: list[list[list[str]]]):
    inline_keyboard = []

    for row in buttons:
        mid_list = []
        for entry in row:
            mid_list.append(construct_button(entry))
        inline_keyboard.append(mid_list)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

