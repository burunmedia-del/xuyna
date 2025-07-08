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
from utils.keyboards import *

db = Database()
router = Router()


@router.callback_query(lambda x: 'addprivet' in x.data)
async def addprivet_handler(call: CallbackQuery, state: FSMContext):
    pull_id = int(call.data.split('_')[1])
    await call.message.edit_text(
        'Пожалуйста, отправьте новую приветку. Текст + клавиатура(при надобности) в формате:\n\nТекст\n-\nКнопка 1 | Кнопка2\nКнопка 3',
        reply_markup=back_key('MENU'), parse_mode='HTML')
    await state.set_state(add_privet_state.text)
    await state.update_data(pull_id=pull_id)

@router.message(add_privet_state.text)
async def add_privet_text(message: Message, state: FSMContext):
    splitted_text = parse_message(message.html_text)
    message_text = splitted_text[0]
    keyboard = splitted_text[1]
    if not keyboard:
        keyboard = None
    state_data = await state.get_data()
    await state.set_state(None)
    db.add_privet(message_text, str(keyboard), state_data['pull_id'])
    await message.answer('✅ Добавили новую приветку в этот пулл!', reply_markup=back_key('MENU'))
