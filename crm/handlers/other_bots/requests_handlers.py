from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.filters import CommandStart, Command
import re
from aiogram.utils.token import validate_token
from aiogram.utils.token import TokenValidationError
from data.config import BASE_WEBHOOK_URL, FOR_OTHER_BOTS
from keyboards import *
from aiogram.fsm.context import FSMContext
from filters.start_filters import *
from data.database import Database
from utils.keyboards import build_privet_keyboard

router = Router()
db = Database()


@router.chat_join_request()
async def cjr(update: ChatJoinRequest, bot: Bot):
    invite_link_name = update.invite_link.name
    requests = update.invite_link.pending_join_request_count
    link = db.get_link_by_name(invite_link_name)
    if link is not None:
        print(link)
        if requests >= int(link['requests']):
            db.update_link_requests(link['id'], requests)
        next_link = db.get_next_link(link['element2_id'])
        privet_id = next_link['privet_id']
        privet = db.get_privet_by_id(privet_id)
        keyboard_ = build_privet_keyboard(privet['keyboard'], next_link['link'])
        await bot.send_message(update.from_user.id, privet['text'], reply_markup=keyboard_)
    else:
        channel_id = update.chat.id
        print(channel_id)
        element = db.get_element_by_channel_id(channel_id)
        print(element)
        next_link = db.get_next_link(element['id'])
        privet_id = next_link['privet_id']
        privet = db.get_privet_by_id(privet_id)
        keyboard_ = build_privet_keyboard(privet['keyboard'], next_link['link'])
        await bot.send_message(update.from_user.id, privet['text'], reply_markup=keyboard_)