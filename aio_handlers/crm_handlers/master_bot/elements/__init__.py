from typing import Final

from aiogram import Router

from . import element_add, elements_manag

router: Final[Router] = Router(name=__name__)
router.include_routers(element_add.router, elements_manag.router)