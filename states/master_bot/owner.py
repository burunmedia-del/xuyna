# - *- coding: utf- 8 - *-
from aiogram.fsm.state import State, StatesGroup


class new_channel_st(StatesGroup):
    post = State()
    custom_link = State()
    custom_uses = State()
class count_members_chat_state(StatesGroup):
    count = State()

class new_ans(StatesGroup):
    message = State()
    seconds = State()

class mailing_state(StatesGroup):
    message = State()

class mass_mailing_state(StatesGroup):
    message = State()

class buttons_state(StatesGroup):
    buttons = State()

class buttons_state_ans(StatesGroup):
    buttons = State()

class black_list_state(StatesGroup):
    users = State()

class black_list_state2(StatesGroup):
    users = State()

class timer_state(StatesGroup):
    timer = State()

class delay_ANS(StatesGroup):
    delay = State()

class delay_ANS_del(StatesGroup):
    delay = State()


class deltime_st(StatesGroup):
    timer = State()