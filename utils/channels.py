from aiogram import Bot
from data.config import *

bot = Bot(token=BOT_TOKEN)


async def create_link_in_channel(channel_id: int, link_name: str):
    link = await bot.create_chat_invite_link(channel_id, link_name, creates_join_request=True)
    return link.invite_link