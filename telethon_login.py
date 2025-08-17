import asyncio
from telethon import TelegramClient, errors
from data.config import API_ID, API_HASH

SESSION_NAME = 'SESS'

async def login():
    client = TelegramClient(f"{SESSION_NAME}.session", API_ID, API_HASH)
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
    print("Авторизация прошла успешно!")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(login())
