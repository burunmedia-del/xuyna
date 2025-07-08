from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
import re
from aiogram.utils.token import validate_token
from aiogram.utils.token import TokenValidationError
from data.config import BASE_WEBHOOK_URL, FOR_OTHER_BOTS
from keyboards import *
from states import *
from aiogram.fsm.context import FSMContext
from filters.start_filters import AdminFilter
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError
from data.database import Database
from utils.webhook_utils import bot_set_webhook

db = Database()
db.create_tables()
router = Router()


@router.callback_query(lambda x: 'add_chain' in x.data)
async def add_chain_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите название цепи для добавления', reply_markup=back_key('MENU'))
    await state.set_state(add_chain_state.name)

@router.message(add_chain_state.name)
async def add_chain_name(message: Message, state: FSMContext):
    await message.answer('Отлично, готово! ✅\nТеперь добавим первое звено в эту ценю: отправьте канал, где я являюсь администратором', reply_markup=add_chain_choose_channel())
    await state.update_data(name=message.text)
    await state.set_state(add_chain_state.first_channel)

@router.message(add_chain_state.first_channel, F.chat_shared)
async def add_chain_channel(message: Message, state: FSMContext, bot: Bot):
    chat = message.chat_shared
    bot_info = await bot.get_me()
    try:
        chat_object = await bot.get_chat(chat.chat_id)
        rights = await bot.get_chat_member(chat.chat_id, bot_info.id)
        if rights.status == 'administrator':
            await message.answer(f'✅ Я добавил канал\n\nДалее нужно отправить токен бота для этого звена в формате <code>7566501035:AAHSqFbQTEMvStf-IofwhqA75FRdFRzbkN7</code>', parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            await state.update_data(channel=chat.chat_id, channel_name=chat_object.title)
            await state.set_state(add_chain_state.bot)
        else:
            await message.answer('🙈 У меня нет прав администратора в этом канале!', reply_markup=back_key('MENU'))
    except TelegramBadRequest:
        await message.answer('🙈 У меня нет прав администратора в этом канале!', reply_markup=back_key('MENU'))

@router.message(add_chain_state.bot)
async def add_chain_bot(message: Message, state: FSMContext, bot: Bot):
    try:
        state_data = await state.get_data()
        chain_new_bot = Bot(message.text)
        x = await chain_new_bot.get_me()
        warning = ''
        try:
            bot_in_channel = await bot.get_chat_member(state_data['channel'], x.id)
            if bot_in_channel.status == 'administrator':
                warning = '⚙ Бот является администратором в канале, который был привязан ранее. Всё хорошо.'
            else:
                warning = '<b>‼ Внимание! Данный Бот НЕ является администратором в канале, который был привязан ранее!</b>'
        except:
            warning = '<b>‼ Внимание! Данный Бот НЕ является администратором в канале, который был привязан ранее!</b>'
        await bot_set_webhook(chain_new_bot, message.text)
        await message.answer(f'Бот <b>{x.full_name}</b> (@{x.username}) успешно добавлен ✅\n\n{warning}', parse_mode='HTML')

        CHAIN_NAME = state_data['name']
        CHANNEL_ID = state_data['channel']
        CHANNEL_NAME = state_data['channel_name']
        BOT_ID = x.id
        BOT_USERNAME = x.username
        BOT_TOKEN = message.text
        add_chain = db.add_chain(CHAIN_NAME)
        db.add_element(CHANNEL_ID, CHANNEL_NAME, BOT_TOKEN, BOT_USERNAME, BOT_ID, add_chain, True)
        await message.answer(f'🔗 Новая цепь с названием «{CHAIN_NAME}» успешно создана!\n\nДобавили первый канал и бота. Осталось выбрать пулл приветок и запустить работу данной цепи', reply_markup=chain_successful_added_key())

    except TelegramUnauthorizedError:
        await message.answer('Неверный токен! ❌')