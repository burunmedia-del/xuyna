from telethon import functions, types
from telethon_main import client
from data.config import YOUR_ACCOUNT_ID
from aiogram import Bot
from data.config import BOT_TOKEN
import asyncio
 

aiogram_bot = Bot(token=BOT_TOKEN)


async def create_link_aiogram_bot(chat_id: int | str) -> str:
    try:

        invite_link: str = await aiogram_bot.export_chat_invite_link(chat_id)
        return invite_link
    except Exception as e:
        print(f"Ошибка при создании ссылки приглашения: {e}")
        return ""


async def create_invite_link(channel_id: int, title: str):
    await client.connect()
    channel = await client.get_entity(channel_id)
    peer = types.InputPeerChannel(channel_id=channel.id, access_hash=channel.access_hash)
    result = await client(functions.messages.ExportChatInviteRequest(peer=peer, title=title, request_needed=True))
    return result.link


async def get_invite_link_stats(channel_id: int, link: str, requested: bool):
    await client.connect()
    channel = await client.get_entity(channel_id)

    result = await client(functions.messages.GetChatInviteImportersRequest(
        peer=channel,
        link=link,
        offset_date=None,
        offset_user=types.InputUserEmpty(),
        limit=100,
        requested=requested
    ))


    return result.count


async def get_requests_count(channel_id: int):
    await client.connect()
    channel = await client.get_input_entity(channel_id)

    result = await client(functions.messages.GetChatInviteImportersRequest(
        peer=channel,
        link='',
        offset_date=None,
        offset_user=types.InputUserEmpty(),
        limit=100,
        requested=True
    ))


    return result.count



