import logging
import sys
from os import getenv
from os import mkdir
import os
from aiohttp import web
from aiogram.fsm.storage.base import (
    BaseEventIsolation,
    BaseStorage,
    StateType,
    StorageKey
)
from asyncio import Lock
from typing import Any, AsyncGenerator, DefaultDict, Dict, Hashable, Optional
from aiogram import Bot, Dispatcher, Router, types
from handlers import master_bot, other_bots
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from data.config import token_of_mainbot, BASE_WEBHOOK_URL, WEB_SERVER_PORT, WEB_SERVER_HOST, WEBHOOK_PATH, \
    OTHER_BOT_PATH
from middlewares.sched import *
from middlewares.album import *
from middlewares.albums import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

WEBHOOK_SECRET = "my-secret"

OTHER_WEBHOOK_URL = f'{BASE_WEBHOOK_URL}{WEBHOOK_PATH}'


async def on_startup(bot: Bot, scheduler: AsyncIOScheduler) -> None:
    scheduler.start()
    await bot.delete_webhook()
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


def main() -> None:
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    scheduler = AsyncIOScheduler(jobstores=jobstores)

    dp: Dispatcher = Dispatcher( scheduler=scheduler
    )

    dp.include_routers(master_bot.router)

    dp.startup.register(on_startup)
    dp.message.middleware(AlbumMiddleware())

    multibot_dispatcher: Dispatcher = Dispatcher (
        scheduler=scheduler
    )
    multibot_dispatcher.include_routers(other_bots.router)

    bot = Bot(token_of_mainbot)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )

    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
    ).register(app, path=OTHER_BOT_PATH)

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
