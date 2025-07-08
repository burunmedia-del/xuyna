from typing import Final

from aiogram import Router

from . import add_pull, pulls_manage, privets

router: Final[Router] = Router(name=__name__)
router.include_routers(add_pull.router, pulls_manage.router, privets.router)