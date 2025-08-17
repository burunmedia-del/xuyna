from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_key(where_to_call_data):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=where_to_call_data), width=1)
    return keyboard.as_markup()