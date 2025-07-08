from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestChat,\
    ChatAdministratorRights
from aiogram.utils.keyboard import InlineKeyboardBuilder
from random import randint as R

def add_chain_choose_channel():
    request_id = R(100000, 999999)
    button_request_chat = [
        [KeyboardButton(text='Выбрать канал',
                        request_chat=KeyboardButtonRequestChat(request_id=request_id,
                                                               chat_is_channel=True))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=button_request_chat, resize_keyboard=True)
    return keyboard

def chain_successful_added_key():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Спасибо. К управлению цепью ➡', callback_data='пустышка'), width=1)
    keyboard.row(InlineKeyboardButton(text='Вернуться в главное меню', callback_data='MENU'), width=1)
    return keyboard.as_markup()

def chain_remote_key(chain_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Выбрать пулл приветок', switch_inline_query_current_chat=f'выбратьпулл {chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Добавить звено', callback_data=f'addelement_{chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Все звенья', switch_inline_query_current_chat=f'звенья {chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Статистика', callback_data=f'chainstate_{chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Удалить цепь', callback_data=f'delchain_{chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='▶ Запустить эту цепь', callback_data=f'startchain_{chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='🔢 Отключить автоподбор', callback_data=f'autochain_1{chain_id}'), width=1)
    keyboard.row(InlineKeyboardButton(text='Вернуться в меню', callback_data='MENU'), width=1)
    return keyboard.as_markup()