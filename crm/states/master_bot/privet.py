from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class add_privet_state(StatesGroup):
    text = State()
