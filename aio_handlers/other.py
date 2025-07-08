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

@router.callback_query(lambda x: x.data == 'BACK')
async def naxuy(call: CallbackQuery, state: FSMContext, bot: Bot):
    bot_object = await bot.get_me()
    if call.message.from_user.id == bot.id:
        await call.message.delete()
    await state.set_state(None)
    await call.message.answer_sticker("CAACAgIAAxkBAAEBTv1oODIGnfYN0ULJoukfT1XHkdkwgQACDjYAAqrzwEnqZj3GIe601zYE",
                                 reply_markup=admin_key())
