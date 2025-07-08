from typing import Final

from aiogram import Router

from . import add_chain, chains_manage

router: Final[Router] = Router(name=__name__)
router.include_routers(add_chain.router, chains_manage.router)