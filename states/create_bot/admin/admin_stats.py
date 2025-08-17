# - *- coding: utf- 8 - *-
from aiogram.fsm.state import State, StatesGroup

class new_full_state(StatesGroup):
    post = State()
    keyboard = State()
    number = State()

class new_full_answer_state(StatesGroup):
    post = State()
    keyboard = State()
    delay = State()
class new_full_f_state(StatesGroup):
    post = State()

class replace_full_state(StatesGroup):
    post = State()

class new_full_keyboard_st(StatesGroup):
    keyboard = State()

