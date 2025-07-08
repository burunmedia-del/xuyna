import uuid

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
from utils.channels import create_link_in_channel

db = Database()
db.create_tables()
router = Router()


@router.callback_query(lambda x: 'addelement' in x.data)
async def add_element_handler(call: CallbackQuery, state: FSMContext):
    chain_id = call.data.split('_')[1]
    await call.message.delete()
    await call.message.answer('Отправьте канал, где я являюсь администратором',
                                 reply_markup=add_chain_choose_channel())
    await state.set_state(add_element_state.channel)
    await state.update_data(chain_id=int(chain_id))

@router.message(add_element_state.channel, F.chat_shared)
async def add_element_channel(message: Message, state: FSMContext, bot: Bot):
    chat = message.chat_shared
    bot_info = await bot.get_me()
    try:
        chat_object = await bot.get_chat(chat.chat_id)

        rights = await bot.get_chat_member(chat.chat_id, bot_info.id)
        if rights.status == 'administrator':
            await message.answer(
                f'✅ Я добавил канал\n\nДалее нужно отправить токен бота для этого звена в формате <code>7566501035:AAHSqFbQTEMvStf-IofwhqA75FRdFRzbkN7</code>',
                parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            await state.update_data(channel=chat.chat_id, channel_name=chat_object.title)
            await state.set_state(add_element_state.bot)
        else:
            await message.answer('🙈 У меня нет прав администратора в этом канале!', reply_markup=back_key('MENU'))
    except TelegramBadRequest:
        await message.answer('🙈 У меня нет прав администратора в этом канале!', reply_markup=back_key('MENU'))


@router.message(add_element_state.bot)
async def add_element_bot(message: Message, state: FSMContext, bot: Bot):
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
        await message.answer(f'Бот <b>{x.full_name}</b> (@{x.username}) успешно добавлен ✅\n\n{warning}',
                             parse_mode='HTML')

        CHANNEL_ID = state_data['channel']
        CHANNEL_NAME = state_data['channel_name']
        BOT_ID = x.id
        BOT_USERNAME = x.username
        BOT_TOKEN = message.text
        last_and_new_elements = db.add_element(CHANNEL_ID, CHANNEL_NAME, BOT_TOKEN, BOT_USERNAME, BOT_ID, state_data['chain_id'])
        last_element = last_and_new_elements[0]
        new_element = last_and_new_elements[1]
        name = str(uuid.uuid4())[:8]
        privet_id = 0
        requests = 0
        last_privet = 0
        actual = 1
        # created_link = await create_link_in_channel(bot, int(CHANNEL_ID), name)
        # db.add_link(name, created_link, last_element['id'], new_element['id'], last_element['queue'], new_element['queue'], new_element['chain_id'], 0, 0, 0, True)
        print(last_element, new_element)
        await message.answer(
            f'Новое звено в цепь добавлено!',
            reply_markup=chain_successful_added_key())

    except TelegramUnauthorizedError:
        await message.answer('Неверный токен! ❌')
