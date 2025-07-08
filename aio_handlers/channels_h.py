import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import types
from data.config import *
import re
from middlewares.album import *
from middlewares.albums import *
from data.database import Database
from keyboards.panel import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)
db.create_tables()


@router.callback_query(lambda x: x.data == 'CHANNELS')
async def CHANNELS_han(call: CallbackQuery, state: FSMContext):
    print('x')
    await call.message.edit_reply_markup(reply_markup=channels_key())