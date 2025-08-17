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

@router.callback_query(lambda x: 'add_pull' in x.data)
async def add_pull_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Укажите название нового пулла', reply_markup=back_key('MENU'))
    await state.set_state(add_pull_state.name)


@router.message(add_pull_state.name)
async def add_pull_name(message: Message, state: FSMContext):
    db.add_pull(message.text)
    await message.answer('Отлично! Пулл был добавлен!', reply_markup=back_key('MENU'), parse_mode="HTML")
    await state.set_state(None)