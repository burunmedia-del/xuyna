from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='🔗 Добавить цепь', callback_data='add_chain'),
                 InlineKeyboardButton(text='🔗 Все цепи', switch_inline_query_current_chat='Цепи'), width=2)
    keyboard.row(InlineKeyboardButton(text='👋🏻 Добавить пулл приветок', callback_data='add_pull'),
    InlineKeyboardButton(text='👋🏻 Все пуллы приветок', switch_inline_query_current_chat='Пуллы'), width=2)
    keyboard.row(InlineKeyboardButton(text='Изменить RC (Replace Count)', callback_data='RC'), width=1)
    keyboard.row(InlineKeyboardButton(text='Изменить время уравнивания кол-ва заявок', callback_data='ORGTIME'), width=1)
    keyboard.row(InlineKeyboardButton(text='Обновление вебхука', callback_data='WEBHOOKS'), width=1)
    return keyboard.as_markup()