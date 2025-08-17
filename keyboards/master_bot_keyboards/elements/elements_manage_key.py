from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def element_manage_keyboard(element_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Сменить канал', callback_data=f'replacechannel_{element_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Сменить бота', callback_data=f'replacebot_{element_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Удалить звено', callback_data=f'delelement_{element_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Вернуться в главное меню', callback_data=f'MENU'), width=1)
    return keyboard.as_markup()