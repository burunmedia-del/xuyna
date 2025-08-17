from typing import Final

from aiogram import Router

from . import start_handler, chains, pulls, elements

router: Final[Router] = Router(name=__name__)
router.include_routers(start_handler.router, chains.router, pulls.router, elements.router)