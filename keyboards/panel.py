from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_key():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Управление каналами 📁 (🐷)', callback_data='CHANNELS'),
                 InlineKeyboardButton(text='Замена ссылок (🐷)', callback_data='LINKS'),
                 InlineKeyboardButton(text='Статистика 📊 (🐷)', switch_inline_query_current_chat='Статистика'), width=1)

    keyboard.row(InlineKeyboardButton(text='🔗 Добавить цепь', callback_data='add_chain'),
                 InlineKeyboardButton(text='🔗 Все цепи', switch_inline_query_current_chat='Цепи'), width=2)
    keyboard.row(InlineKeyboardButton(text='👋🏻 Добавить пулл приветок', callback_data='add_pull'),
    InlineKeyboardButton(text='👋🏻 Все пуллы приветок', switch_inline_query_current_chat='Пуллы'), width=2)
    keyboard.row(InlineKeyboardButton(text='Изменить RC (Replace Count)', callback_data='RC'), width=1)
    keyboard.row(InlineKeyboardButton(text='Изменить время уравнивания кол-ва заявок', callback_data='ORGTIME'), width=1)
    keyboard.row(InlineKeyboardButton(text='Обновление вебхука', callback_data='WEBHOOKS'), width=1)
    return keyboard.as_markup()


def download_statistic(channel_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Скачать статистику 📊', callback_data=f'download_{channel_id}'),
                 InlineKeyboardButton(text='⬅ Назад', callback_data='MAIN_MENU'), width=1)
    return keyboard.as_markup()
def channels_key():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Добавить канал ➕', callback_data='NEW_CHANNEL'),
                 InlineKeyboardButton(text='Список каналов 📄', switch_inline_query_current_chat='Список каналов'),
                 InlineKeyboardButton(text='⬅ Вернуться назад', callback_data='MAIN_MENU'), width=1)
    return keyboard.as_markup()


def back():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Назад ◀', callback_data='BACK'))
    return keyboard.as_markup()


def replace_links_choose_channel():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='Выбрать канал', switch_inline_query_current_chat='Замена ссылок'), width=1)
    keyboard.row(InlineKeyboardButton(text='⬅ Вернуться назад', callback_data='MAIN_MENU'), width=1)
    return keyboard.as_markup()