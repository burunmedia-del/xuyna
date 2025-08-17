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
from states import *
from telethon_main import is_client_admin, join_private_channel_by_invite
from utils.channels_u import create_link_aiogram_bot, get_requests_count


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)


@router.message(Command("start"))
async def admin_start(message: Message, state: FSMContext):
    await state.set_state(None)
    await message.answer_sticker("CAACAgIAAxkBAAEBaLVobVAXkJI4alnr97qRfJCiKiIUTAACz4QAAjwAAWhLUoVMPntP96g2BA",
                                )
    await message.answer(f'Автоматизированный перелив и CRM-бот ⭐\n\n<b>Актуальный статус:</b> \n<b>RC:</b> {db.get_config_value("rc")} заявок\n<b>Автоуравнивание (ХУЙНЯ НЕ РАБОТАЕТ ):</b> каждые {db.get_config_value("organize_time")} минут', parse_mode="HTML", reply_markup=admin_key())


@router.callback_query(lambda x: x.data == 'MAIN_MENU')
async def menu_han(call: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await call.message.edit_reply_markup(reply_markup=admin_key())


@router.callback_query(lambda x: x.data == 'CHANNELS')
async def CHANNELS_han(call: CallbackQuery, state: FSMContext):
    print('x')
    await call.message.edit_reply_markup(reply_markup=channels_key())


@router.callback_query(lambda x: x.data == 'NEW_CHANNEL')
async def NEW_CHANNEL(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Отправь мне любой пост из канала. Главное, чтобы я был админом в нём и мог добавлять других админов.', reply_markup=back())
    await state.set_state(new_ch.post)


@router.message(new_ch.post, lambda x: x.forward_from_chat is not None)
async def forward_from_chat(message: Message, state: FSMContext):
    channel_id = message.forward_from_chat.id
    link_ = await create_link_aiogram_bot(channel_id)
    await join_private_channel_by_invite(link_)
    await bot.promote_chat_member(chat_id=channel_id, user_id=YOUR_ACCOUNT_ID, can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True,
            can_manage_video_chats=True,
            can_manage_chat=True,
            can_manage_topics=True,
            can_post_stories=True,
            can_edit_stories=True)
    add_database = db.add_channel(channel_id, message.forward_from_chat.full_name)
    if add_database:
        await message.answer('Канал добавлен!', reply_markup=back())
    else:
        await message.answer('Такой канал уже существует!', reply_markup=back())

@router.message(lambda x: 'Это канал' in x.html_text)
async def it_is_channel_handler(message: Message, state: FSMContext):
    match = re.search(r"id=([-]?\d+)", message.text)
    number_str = int(match.group(1))
    chat = db.get_channel_by_id(number_str)
    await message.delete()
    await message.answer(f'Это канал {chat["name"]}!', reply_markup=back())
