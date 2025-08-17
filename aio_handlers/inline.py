import uuid

from aiogram import Router, Bot, Dispatcher, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
import hashlib
import re
from data.database import Database
from data.config import *
from keyboards import *
from random import choice


db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)
router = Router()
thumbs = ['https://sun1-89.userapi.com/impg/MDT5V9KtqyLuvY51E50_O2dZ2mqW0L7wojLtnQ/prYdUZETb6o.jpg?size=453x604&quality=96&sign=3fa14909aa6f6c3f244d8a6d991e9e88&type=album', 'https://static-eu-cdn.eporner.com/gallery/S3/o7/RM8Z93xo7S3/6812218-fxztqh-uuaadmnu-jpg-large.jpg', 'https://i.pinimg.com/originals/de/ec/1d/deec1dc6abf62a556316ae82599cb5b7.png', 'https://steamuserimages-a.akamaihd.net/ugc/2036238827533067379/5E5231DB1E5CBFB48A6A9724744D9A5F2E94C971/?imw=512&amp;imh=585&amp;ima=fit&amp;impolicy=Letterbox&amp;imcolor=%23000000&amp;letterbox=true', 'https://i.ytimg.com/vi/bjMBchhe8z8/maxresdefault.jpg', 'https://sun9-45.userapi.com/s/v1/ig2/OnjoRvwImTUKydEMJ98nCmMs19fpKGWvUBjP6BOp63DDjxZXTAzKx1-gwwUZxAU7cNF4hH_Pbm5dy76QMrLPPYl0.jpg?quality=95&as=32x57,48x85,72x128,108x192,160x284,240x427,360x640,480x853,540x960,640x1138,720x1280&from=bu&u=KiB-88n86PLpMPu9xueLFzIfyfFKjd4ju_rU6E-EUZ8&cs=454x807', 'https://sun9-37.userapi.com/s/v1/ig2/tmNOGYw7zyx_Ye2UFpiR-6qhyyHQefRdgvB3LRy3UJ6s0qsSx43uNFI9xD5dau32Kbg_6yKddg01dMx553psaSNp.jpg?quality=96&as=32x48,48x71,72x107,108x161,160x238,240x357,360x536,480x714,540x804,640x953,688x1024&from=bu&u=31IFdKUX6YOPxetHKxnLo-Gd13Wa0yx7vy-ygD0lnrg&cs=688x1024', 'https://sun9-12.userapi.com/impg/Ph8JEAfzvsuBd2OkYaexpiPLDyAjjSO3PrBQBQ/LVfTZUr0Q0o.jpg', 'https://i0.wp.com/webmg.ru/wp-content/uploads/2022/10/look.com_.ua-223276.jpg?ssl=1', 'https://www.meme-arsenal.com/memes/373df60309b4a18502bd0c0c1775a8ce.jpg']


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



@router.inline_query(lambda x: x.query == 'Цепи')
async def inline_channels_handler(inline_query: types.InlineQuery, bot: Bot):
    chains = db.get_all_chains()
    results = []
    for i in chains:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            thumbnail_url=choice(thumbs),
            input_message_content=InputTextMessageContent(message_text=f"Цепь {i['name']}\nid={i['id']}"),
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )

@router.inline_query(lambda x: x.query == 'Пуллы')
async def inline_channels_handler_pulls(inline_query: types.InlineQuery, bot: Bot):
    pulls = db.get_pulls()

    results = []
    for i in pulls:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            thumbnail_url=choice(thumbs),
            input_message_content=InputTextMessageContent(message_text=f"Пулл {i['name']}\nid={i['id']}"),
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )


@router.inline_query(lambda x: 'Приветки' in x.query)
async def inline_channels_handler_privets(inline_query: types.InlineQuery, bot: Bot):
    pull_id = int(inline_query.query.split(' ')[1])
    privets = db.get_privets(pull_id)
    results = []
    for i in privets:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['text'][:15]+'...',
            description=f'Клавиатура: есть ✅' if i["keyboard"] is not None else f'Клавиатура: нет ❌',
            thumbnail_url=choice(thumbs),
            input_message_content=InputTextMessageContent(message_text=f"Приветка {pull_id} {i['id']}"),
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )


@router.inline_query(lambda x: 'выбратьпулл' in x.query)
async def choosepull_chain_handler(inline_query: types.InlineQuery, bot: Bot):
    chain_id = int(inline_query.query.split(' ')[1])
    chain = db.get_chain(chain_id)
    privets = db.get_pulls()
    results = []
    for i in privets:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=i['name'],
            thumbnail_url=choice(thumbs),
            description=f'Выбрать этот пулл для цепи "{chain["name"]}. Всего приветок: {len(db.get_privets(i["id"]))}',
            input_message_content=InputTextMessageContent(message_text=f"установитьпулл {chain_id} {i['id']}"),
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )


@router.inline_query(lambda x: 'звенья' in x.query)
async def all_elements_chain_handler(inline_query: types.InlineQuery, bot: Bot):
    chain_id = int(inline_query.query.split(' ')[1])
    chain = db.get_chain(chain_id)
    elements = db.get_elements(chain_id)
    results = []
    for i in elements:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f'Звено №{i["queue"]}'+f'{" (оригинальный канал, главное звено) 🔻" if i["main"] else ""}',
            thumbnail_url=choice(thumbs),
            description=f'📁 {i["channel_name"]} | 🤖 @{i["bot_username"]}',
            input_message_content=InputTextMessageContent(message_text=f"звено {i['id']}"),
        )
        results.append(result)

    await bot.answer_inline_query(
        inline_query.id,
        results=results,
        cache_time=0,

        is_personal=True
    )