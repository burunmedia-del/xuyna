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

@router.message(lambda x: x.text and 'звено ' in x.text)
async def element_han(message: Message, state: FSMContext):
    element_ = db.get_element(int(message.text.split()[1]))
    chain_id = element_['chain_id']
    chain_ = db.get_chain(chain_id)
    await message.answer(f'''<b>Звено из цепи "{chain_["name"]}"</b>

Актуальный канал: {element_['channel_name']} <i>({element_['channel_id']})</i>
Актуальный бот: @{element_['bot_username']}

{'<b>👑 Это оригинальный канал. Номер звена: 1</b>' if element_["main"] else f'🔹 Номер звена: {element_["queue"]}'}''', reply_markup=element_manage_keyboard(element_["id"]), parse_mode="HTML")