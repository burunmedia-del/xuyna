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

@router.callback_query(lambda x: x.data == 'BACK' or x.data == 'MENU')
async def naxuy(call: CallbackQuery, state: FSMContext, bot: Bot):
    bot_object = await bot.get_me()
    if call.message.from_user.id == bot.id:
        await call.message.delete()
    await state.set_state(None)

    await call.message.answer(f'Автоматизированный перелив и CRM-бот ⭐\n\n<b>Актуальный статус:</b> \n<b>RC:</b> {db.get_config_value("rc")} заявок\n<b>Автоуравнивание (ХУЙНЯ НЕ РАБОТАЕТ ):</b> каждые {db.get_config_value("organize_time")} минут', parse_mode="HTML", reply_markup=admin_key())

