from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class add_element_state(StatesGroup):
    channel = State()
    bot = State()

class deltime_st(StatesGroup):
    timer = State()

class chain_last_privet_state(StatesGroup):
    message = State()