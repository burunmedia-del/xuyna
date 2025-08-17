from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class add_pull_state(StatesGroup):
    name = State()
