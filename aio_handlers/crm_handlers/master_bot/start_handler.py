from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
import re
from aiogram.utils.token import validate_token
from aiogram.utils.token import TokenValidationError
from data.config import BASE_WEBHOOK_URL, OTHER_BOT_PATH
from keyboards import *
from aiogram.fsm.context import FSMContext
from filters.start_filters import *
from data.database import Database
from states import *
from utils.webhook_utils import bot_set_webhook

router = Router()
db = Database()


@router.message(CommandStart(), PullInStartArgsFilter())
async def start_handler(message: Message, command: Command, pull_id: int):
    pull = db.get_pull(pull_id)
    print(pull)
    await message.answer(f'<b>Пулл {pull["name"]}</b>\n\nВсего приветок добавлено: {len(db.get_privets(pull_id))}', reply_markup=pull_manage_key(pull_id), parse_mode='HTML')


# @router.message(CommandStart(), AdminFilter())
# async def start_handler(message: Message, state: FSMContext):
#     await message.answer(f'Автоматизированный перелив и CRM-бот ⭐\n\n<b>Актуальный статус:</b> \n<b>RC:</b> {db.get_config_value("rc")} заявок\nА<b>втоуравнивание:</b> каждые {db.get_config_value("organize_time")} минут', reply_markup=main_menu_keyboard(), parse_mode="HTML")


# @router.callback_query(lambda x: 'MENU' in x.data)
# async def menu_handler(call: CallbackQuery, state: FSMContext):
#     await state.set_state(None)
#     await call.message.edit_text(f'Автоматизированный перелив и CRM-бот ⭐\n\n<b>Актуальный статус:</b>\n<b>RC:</b> {db.get_config_value("rc")} заявок\n<b>Автоуравнивание:</b> каждые {db.get_config_value("organize_time")} минут', reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.callback_query(lambda x: 'RC' in x.data)
async def rc_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите новое значение:', reply_markup=back_key('MENU'))
    await state.set_state(edit_rc.new_rc)

@router.message(edit_rc.new_rc)
async def new_rc_handler(message: Message, state: FSMContext):
    if message.text.isdigit():
        db.set_config_value('rc', int(message.text))
        await message.answer('Отлично! Задали новый RC', reply_markup=back_key('MENU'))
    else:
        await message.answer('Указали не число!')


@router.callback_query(lambda x: 'ORGTIME' in x.data)
async def orgtime_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите новое значение в минутах:', reply_markup=back_key('MENU'))
    await state.set_state(edit_orgtime.new_orgtime)

@router.message(edit_orgtime.new_orgtime)
async def new_orgtime_handler(message: Message, state: FSMContext):
    if message.text.isdigit():
        db.set_config_value('organize_time', int(message.text))
        await message.answer('Отлично! Задали новое значение для автоуравнивания заявок', reply_markup=back_key('MENU'))
    else:
        await message.answer('Указали не число!')


@router.callback_query(lambda x: x.data == 'WEBHOOKS')
async def WEBHOOKS_handler(call: CallbackQuery, state: FSMContext):
    elements = db.get_elements_all()
    await call.answer('Начинаю обновление ботов', show_alert=True)
    for i in elements:
        await bot_set_webhook(Bot(token=i['bot_token']), i['bot_token'])
    await call.message.answer('Все боты на вебхуке обновлены!')