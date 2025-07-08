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
from datetime import datetime, timedelta
from keyboards import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.channels_u import create_invite_link, get_invite_link_stats
from telethon_main import client, join_private_channel_by_invite
from utils.time_u import get_current_time_formatted
from utils.channels_u import get_invite_link_stats
from utils.xlsx import create_report_excel

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)


def parse_message_links(text: str):
    pattern = re.compile(r"^(?P<tag>@\w+)\s+(?P<date>\d{2}\.\d{2})\s+(?P<price>\d+)р$", re.MULTILINE)
    results = []
    for line in text.strip().splitlines():
        match = pattern.match(line.strip())
        if not match:
            return None
        data = match.groupdict()
        data['tag'] = data['tag']
        data['price'] = int(data['price'])
        results.append(data)
    return results

class Form(StatesGroup):
    waiting_for_post = State()
    waiting_for_ids = State()
    send_posts = State()

# Главное меню с эмодзи
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Каналы", callback_data="channels")],
        [InlineKeyboardButton(text="🔗 Замена ссылок", callback_data="replace_links")]
    ])

# Кнопка назад
def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_menu")]
    ])




@router.message(Form.waiting_for_post, F.media_group_id, F.photo)
async def process_post_album(message: Message, album: Album, state: FSMContext):
    photos = []
    for i in album.photo:
        photos.append(i.file_id)
    media = []
    for i in photos:
        media.append(types.InputMediaPhoto(media=i))
    await message.answer_media_group(media=media)


@router.message(Form.waiting_for_post)
async def process_post(message: Message, state: FSMContext):
    if message.text == '/s':
        state_data = await state.get_data()
        print(state_data['messages'])
        await message.answer(
            "✍️ Теперь отправьте идентификаторы в формате:\n"
            "@usertag 27.05 700р\n"
            "@usertag 27.05 700р\n"
            "(несколько строк)",
            reply_markup=back()
        )
        await state.set_state(Form.waiting_for_ids)
        return
    state_data = await state.get_data()
    messages: list = state_data['messages']
    messages.append(message)
    await state.update_data(messages=messages)

@router.message(lambda message: message.text and message.text.lower().startswith('вход '))
async def join_private_channel_handler(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Пожалуйста, укажите ссылку после слова 'вход'.")
        return

    invite_link = parts[1].strip()
    if 't.me' not in invite_link:
        await message.reply("Ссылка должна содержать 't.me'.")
        return

    success = await join_private_channel_by_invite(invite_link)
    if success:
        await message.reply(f"Успешно вошёл в канал по ссылке: {invite_link}")
    else:
        await message.reply(f"Не удалось войти в канал по ссылке: {invite_link}")



@router.message(lambda x: 'Замена ссылок' in x.html_text)
async def replace_links_channel_handler(message: Message, state: FSMContext):
    match = re.search(r"id=([-]?\d+)", message.text)
    if match:
        number_str = match.group(1)
        number_int = int(number_str)
        await message.answer('✅ Отлично! Канал выбран! Пожалуйста, отправьте посты для замены\n\nПосле - напишите /s', reply_markup=back())
        await state.set_state(Form.waiting_for_post)
        await state.update_data(channel_id=number_int)
        await state.update_data(messages=[])


@router.message(lambda x: 'Отправка постов' in x.html_text)
async def replace_links_channel_handler(message: Message, state: FSMContext):
    match = re.search(r"id=(\d+)", message.text)
    if match:
        number_str = match.group(1)
        user_id = int(number_str)
        await state.set_state(Form.send_posts)
        await state.update_data(user_id=user_id)


@router.message(Form.send_posts)
async def send_posts_handler(message: Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    user_id = state_data['user_id']
    if 'стоп' in message.html_text:
        ids = message.text.split()
        first_id = int(ids[1].split('-')[0])
        last_id = int(ids[1].split('-')[1])
        await state.set_state(None)
        await bot.send_message(user_id, 'Спасибо!', reply_markup=back())
        for i in range(first_id, last_id+1):
            await bot.delete_message(replace_links_chat, i)
        return
    await message.forward(user_id)



@router.callback_query(lambda x: x.data == "LINKS")
async def LINKS_handler(call: CallbackQuery, state: FSMContext):
    x = 'd'
    if len(db.get_all_channels()):
        await call.message.delete()
        await call.message.answer('Выберите канал', reply_markup=replace_links_choose_channel())
    else:
        await call.answer('У Вас не добавлено ни одного канала!', show_alert=True)

@router.message(Form.waiting_for_ids)
async def ids_links_replace_handler(message: Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    parse = parse_message_links(message.text)
    new_post_entities = []
    channel_id = state_data['channel_id']
    for i in parse:
        link = await create_invite_link(channel_id, title=f"{i['tag']} {i['date']} {i['price']}")
        db.add_link(channel_id, f"{i['tag']} {i['date']} {i['price']}", link, int(i['price']))
        new_post_entities.append(f"{i['tag']} {i['date']} {i['price']} — {link}")
    if parse is not None:
        state_data = await state.get_data()
        messages: list = state_data['messages']
        for m in messages:
            m: Message
            if m.text != '/s':
                await m.forward(replace_links_chat)
        x = f'{message.chat.id}\n'+'\n'.join(new_post_entities)
        await bot.send_message(replace_links_chat, x)
        await message.answer('✅ Ссылки созданы. Подготавливаю посты!')
        await bot.send_message(YOUR_ACCOUNT_ID, "ZAMENA")
    else:
        await message.answer('❌ Не соответствует формату!', reply_markup=back())


@router.message(lambda x: 'Статистика по каналу' in x.html_text)
async def state_of_channel_handler(message: Message, state: FSMContext):
    match = re.search(r"id=([-]?\d+)", message.text)
    channel_id = int(match.group(1))
    channel = db.get_channel_by_id(channel_id)
    await message.answer(f'Статистика по каналу {channel["name"]}', reply_markup=download_statistic(channel_id))

async def everytime_stats(channel_id, link_id, _requests, _joins):
    link = db.get_link_by_id(link_id)
    requests = await get_invite_link_stats(channel_id, link['link'], True)
    joins = await get_invite_link_stats(channel_id, link['link'], False)
    print(_requests, _joins)
    db.update_link_value(link_id, _requests, requests)
    db.update_link_value(link_id, _joins, joins)

@router.callback_query(lambda x: 'download' in x.data)
async def download_statistic_handler(call: CallbackQuery, state: FSMContext):
    channel = db.get_channel_by_id(int(call.data.split('_')[1]))
    channel_id = channel['channel_id']
    links = db.get_links_by_channel(channel_id)
    links_for_report = []
    if len(links):
        await call.message.edit_text('🕟 Идёт подготовка отчёта...')
        for link in links:
            links_for_report.append(
                [
                    link['title'],
                    link['price'],
                    link['start'].strftime('%d.%m.%Y %H:%M') if link['start'] is not None else 'ещё не начиналось',
                    await get_invite_link_stats(channel_id, link['link'], True),
                    await get_invite_link_stats(channel_id, link['link'], False),
                    link['10m_requests'],
                    link['28m_requests'],
                    link['60m_requests'],
                    link['24h_requests'],
                    link['48h_requests'],
                    link['72h_requests'],
                    link['10m_joins'],
                    link['28m_joins'],
                    link['60m_joins'],
                    link['24h_joins'],
                    link['48h_joins'],
                    link['72h_joins'],
                ]
            )
        await create_report_excel(channel['name'], links_for_report)
        await call.message.answer_document(document=types.FSInputFile(f'files/{channel["name"]}.xlsx'))
        await call.message.answer('Спасибо! Приходите ещё', reply_markup=back())
    else:
        await call.answer('Нет созданных ссылок', show_alert=True)

@router.chat_join_request()
async def handle_join_request(join_request: types.ChatJoinRequest, scheduler: AsyncIOScheduler):
    chat = join_request.chat.id
    if db.channel_exists(chat):
        invite_link = db.get_link_by_partial_link(join_request.invite_link.invite_link[:-3], chat)
        if invite_link:
            if invite_link['start'] is None:
                if invite_link['requests_before_start'] != 2:
                    db.update_link_value(invite_link['id'], 'requests_before_start', invite_link['requests_before_start']+1)
                else:
                    db.set_start_time(invite_link['id'])
                    now = datetime.now()
                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '10m_requests', '10m_joins'],
                                      run_date=now + timedelta(minutes=10))

                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '28m_requests', '28m_joins'],
                                      run_date=now + timedelta(minutes=28))

                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '60m_requests', '60m_joins'],
                                      run_date=now + timedelta(minutes=60))

                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '24h_requests', '24h_joins'],
                                      run_date=now + timedelta(hours=24))

                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '48h_requests', '48h_joins'],
                                      run_date=now + timedelta(hours=48))

                    scheduler.add_job(everytime_stats, 'date',
                                      args=[chat, invite_link['id'], '72h_requests', '72h_joins'],
                                      run_date=now + timedelta(hours=72))