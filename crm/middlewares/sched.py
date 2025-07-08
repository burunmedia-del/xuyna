from aiogram import Dispatcher, types
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Awaitable, Any, Dict, Union


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler):
        self.scheduler = scheduler

    async def on_process_message(self, data: dict):
        data['scheduler'] = self.scheduler

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, any]], Awaitable[Any]],
                       event: Union[Message, Any],
                       data: Dict[str, Any]
                       ) -> Any:
        await self.on_process_message(data)
        await handler(event,data)