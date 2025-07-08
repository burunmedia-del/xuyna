import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data.config import *
from telethon_main import *
from middlewares.albums import *
from aio_handlers import start_handlers, replace_links_handlers, channels_h, other, inline
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

async def main():
    await start_telethon_client()
    dp.include_routers(start_handlers.router, replace_links_handlers.router, channels_h.router, other.router, inline.router)
    # scheduler.add_job(CHECK_LINKS, 'interval', seconds=3)
    scheduler.start()
    dp['scheduler'] = scheduler
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
