from typing import Final

from aiogram import Router

from . import start_handler, chains, inline_handler, pulls, elements

router: Final[Router] = Router(name=__name__)
router.include_routers(start_handler.router, chains.router, inline_handler.router, pulls.router, elements.router)