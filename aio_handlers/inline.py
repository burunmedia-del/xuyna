import uuid

from aiogram import Router, Bot, Dispatcher, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
import hashlib
import re
from data.database import Database
from data.config import *
from keyboards import *

db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)
router = Router()

@router.inline_query(lambda x: x.query == 'Замена ссылок')
async def inline_channels_handler(inline_query: types.InlineQuery, bot: Bot):
    channels = db.get_all_channels()
    results = []
    for i in channels:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            input_message_content=InputTextMessageContent(message_text=f"Замена ссылок {i['name']}\nid={i['channel_id']}"),
            description='Выбрать этот канал',
            thumbnail_url='https://thumb-p9.xhcdn.com/a/cf-WIRXJc_--RsMOvEKxHg/000/104/656/939_1000.jpg'
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )

@router.inline_query(lambda x: x.query == 'Список каналов')
async def inline_channels_handler(inline_query: types.InlineQuery, bot: Bot):
    channels = db.get_all_channels()
    results = []
    for i in channels:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            input_message_content=InputTextMessageContent(message_text=f"Это канал {i['name']}\nid={i['id']}"),
            description='',
            thumbnail_url='https://thumb-p9.xhcdn.com/a/cf-WIRXJc_--RsMOvEKxHg/000/104/656/939_1000.jpg'
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )


@router.inline_query(lambda x: x.query == 'Статистика')
async def inline_channels_handler(inline_query: types.InlineQuery, bot: Bot):
    channels = db.get_all_channels()
    results = []
    for i in channels:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            input_message_content=InputTextMessageContent(message_text=f"Статистика по каналу {i['name']}\nid={i['id']}"),
            description='Выберите этот канал для просмотра статистики',
            thumbnail_url='https://thumb-p9.xhcdn.com/a/cf-WIRXJc_--RsMOvEKxHg/000/104/656/939_1000.jpg'
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )