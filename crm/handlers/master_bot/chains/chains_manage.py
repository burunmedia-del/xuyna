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
from random import choice
from utils.channels import create_link_in_channel
import uuid

db = Database()
db.create_tables()
router = Router()


@router.message(lambda x: x.text and 'Цепь' in x.text)
async def chain_remote_handler(message: Message, state: FSMContext, bot: Bot):
    bot_info = await bot.get_me()
    chain_id = int(message.text.split('\n')[1].split('id=')[1])
    chain = db.get_chain(chain_id)
    pull = f"<a href='t.me/{bot_info.username}?start=pull_{chain['pull_id']}'>{db.get_pull(chain['pull_id'])['name']}</a>" if \
    chain['pull_id'] is not None else 'не выбран'
    await message.answer(
        f'<b>Цепь "{chain["name"]}"</b>\n\n<b>Звеньев:</b> {len(db.get_elements(chain_id))}\n<b>Пулл приветок:</b> {pull}',
        reply_markup=chain_remote_key(chain_id), parse_mode="HTML")


@router.message(lambda x: x.text and 'установитьпулл' in x.text)
async def new_chain_pull(message: Message, state: FSMContext, bot: Bot):
    chain_id = int(message.text.split(' ')[1])
    new_pull_id = int(message.text.split(' ')[2])
    db.update_chain_pull_id(chain_id, new_pull_id)
    await message.answer('Пулл этой цепи обновлён ✅')
    chain = db.get_chain(chain_id)
    bot_info = await bot.get_me()
    pull = f"<a href='t.me/{bot_info.username}?start=pull_{chain['pull_id']}'>{db.get_pull(chain['pull_id'])['name']}</a>" if \
        chain['pull_id'] is not None else 'не выбран'
    await message.answer(
        f'<b>Цепь "{chain["name"]}"</b>\n\n<b>Звеньев:</b> {len(db.get_elements(chain_id))}\n<b>Пулл приветок:</b> {pull}',
        reply_markup=chain_remote_key(chain_id), parse_mode="HTML")


@router.callback_query(lambda x: 'startchain_' in x.data)
async def startchain_handler(call: CallbackQuery, state: FSMContext, bot: Bot):
    chain_id = call.data.split('_')[1]
    chain = db.get_chain(chain_id)
    if chain['pull_id'] is not None:
        privets = db.get_privets(chain['pull_id'])
        privets_ids = [p['id'] for p in privets]
        elements = db.get_elements(chain['id'])
        db.add_link('any', 'any', 0, elements[0]['id'], 0, 1, chain_id, 0, 0, 0, True)
        privets_for_elements = {}
        for x, element in enumerate(elements[1:]):
            last_element = elements[x]
            new_privet = choice(privets_ids)
            privets_ids.pop(privets_ids.index(new_privet))
            link_name = str(uuid.uuid4())[:8]
            link = await create_link_in_channel(bot, element['channel_id'],link_name[:8])
            db.add_link(link_name, link, last_element['id'], element['id'], last_element['queue'], element['queue'], chain_id, new_privet, 0, 0, True)
        await call.answer('Колымага ебаная запущена', show_alert=True)
    else:
        await call.answer('Вы не выбрали пулл приветок!', show_alert=True)