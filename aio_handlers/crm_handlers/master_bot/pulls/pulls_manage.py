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

db = Database()
router = Router()

@router.message(lambda x: x.text and 'Пулл' in x.text)
async def oull_manage(message: Message, state: FSMContext):
    pull_id = int(message.text.split('\n')[1].split('id=')[1])
    pull = db.get_pull(pull_id)
    print(pull)
    await message.answer(f'<b>Пулл {pull["name"]}</b>\n\nВсего приветок добавлено: {len(db.get_privets(pull_id))}', reply_markup=pull_manage_key(pull_id), parse_mode='HTML')