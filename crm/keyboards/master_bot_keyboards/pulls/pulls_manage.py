from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def pull_manage_key(pull_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Все приветки', switch_inline_query_current_chat=f'Приветки {pull_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Добавить приветку', callback_data=f'addprivet_{pull_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='В главное меню', callback_data=f'MENU'), width=1)
    return keyboard.as_markup()