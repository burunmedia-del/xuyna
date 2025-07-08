from aiogram import Bot
from data.config import BASE_WEBHOOK_URL, OTHER_BOT_PATH

WEBHOOK_SECRET = "my-secret"


async def bot_set_webhook(bot: Bot, token: str):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{OTHER_BOT_PATH.format(bot_token=token)}", secret_token=WEBHOOK_SECRET)
    return True
