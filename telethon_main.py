import asyncio
from telethon import TelegramClient, errors
from xtelethon import CustomParseMode
from data.config import API_ID, API_HASH
from tele_handlers.load_messages import register_handlers
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest


client = TelegramClient(
    'SESS.session',
    API_ID,
    API_HASH,
    system_version="4.16.30-vxMAX"
)
client.parse_mode = CustomParseMode('markdown')

register_handlers(client)


async def join_private_channel_by_invite(invite_link: str) -> bool:
    """
    Вступить в приватный канал по ссылке-приглашению t.me/+...
    """
    try:
        # Извлекаем хеш приглашения из ссылки
        invite_hash = invite_link.split('+')[-1]
        await client(ImportChatInviteRequest(invite_hash))
        return True
    except Exception as e:
        print(f"Ошибка при вступлении в канал по ссылке {invite_link}: {e}")
        return False


async def is_client_admin(chat_id):
    me = await client.get_me()  # Получаем информацию о текущем аккаунте
    try:
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            user_id=me.id
        ))
        # Проверяем, является ли участник админом или создателем
        return isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator))
    except Exception:
        # Если не админ или нет доступа, вернём False
        return False


async def start_telethon_client():
    await client.connect()
    if not await client.is_user_authorized():
        phone = input("Введите номер телефона (с кодом страны, например +79161234567): ")
        await client.send_code_request(phone)
        code = input("Введите код из Telegram: ")
        try:
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            password = input("Введите пароль двухфакторной аутентификации: ")
            await client.sign_in(password=password)
    print("Telethon клиент авторизован!")


async def main():
    await start_telethon_client()
    print("Клиент запущен, ожидаем события...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
