from aiogram.filters import Filter
from aiogram import types
from aiogram.filters import Command, CommandObject
from data.database import dbworker

db = dbworker('data/db.db')


class BlackListExists(Filter):
    async def __call__(self, message: types.Message) -> bool:
        if db.black_list_exists(message.chat.username):
            return True