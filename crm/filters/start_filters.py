from aiogram.filters import Filter
from aiogram import types
from aiogram.filters import Command, CommandObject
from data.config import owners

class AdminFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        if message.chat.id in owners:
            return True

class PullInStartArgsFilter(Filter):
    async def __call__(self, message: types.Message, command: CommandObject):
        if command.args and 'pull_' in command.args:
            return {'pull_id': int(command.args.split('_')[1])}