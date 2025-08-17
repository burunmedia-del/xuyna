from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class edit_rc(StatesGroup):
    new_rc = State()

class edit_orgtime(StatesGroup):
    new_orgtime = State()
