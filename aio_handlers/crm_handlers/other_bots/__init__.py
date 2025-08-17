from typing import Final

from aiogram import Router

from . import requests_handlers

router: Final[Router] = Router(name=__name__)
router.include_routers(requests_handlers.router)