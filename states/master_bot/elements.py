from aiogram.filters.state import State, StatesGroup

class add_chain_state(StatesGroup):
    name = State()
    first_channel = State()
    bot = State()