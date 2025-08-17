from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
import re
from aiogram.utils.token import validate_token
from aiogram.utils.token import TokenValidationError
from data.config import BASE_WEBHOOK_URL, FOR_OTHER_BOTS
from keyboards import *
from states import *
from aiogram.fsm.context import FSMContext
from filters.start_filters import AdminFilter
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError
from data.database import Database
from random import choice
from utils.channels import create_link_in_channel
import uuid
from utils.keyboards import *
from utils.xlsx import export_conversion_to_excel

db = Database()
db.create_tables()
router = Router()


@router.message(lambda x: x.text and 'Цепь' in x.text)
async def chain_remote_handler(message: Message, state: FSMContext, bot: Bot):
    bot_info = await bot.get_me()
    chain_id = int(message.text.split('\n')[1].split('id=')[1])
    chain = db.get_chain(chain_id)
    pull = f"<a href='t.me/{bot_info.username}?start=pull_{chain['pull_id']}'>{db.get_pull(chain['pull_id'])['name']}</a>" if \
    chain['pull_id'] is not None else 'не выбран'
    is_started = bool(len(db.get_all_actual_crm_links_by_chain_id(chain_id)))
    await message.answer(
        f'<b>Цепь "{chain["name"]}"</b>\n\n<b>Звеньев:</b> {len(db.get_elements(chain_id))}\n<b>Пулл приветок:</b> {pull}',
        reply_markup=chain_remote_key(chain_id, is_started), parse_mode="HTML")


@router.message(lambda x: x.text and 'установитьпулл' in x.text)
async def new_chain_pull(message: Message, state: FSMContext, bot: Bot):
    chain_id = int(message.text.split(' ')[1])
    new_pull_id = int(message.text.split(' ')[2])
    is_started = bool(len(db.get_all_actual_crm_links_by_chain_id(chain_id)))
    db.update_chain_pull_id(chain_id, new_pull_id)
    await message.answer('Пулл этой цепи обновлён ✅')
    chain = db.get_chain(chain_id)
    bot_info = await bot.get_me()
    pull = f"<a href='t.me/{bot_info.username}?start=pull_{chain['pull_id']}'>{db.get_pull(chain['pull_id'])['name']}</a>" if \
        chain['pull_id'] is not None else 'не выбран'

    await message.answer(
        f'<b>Цепь "{chain["name"]}"</b>\n\n<b>Звеньев:</b> {len(db.get_elements(chain_id))}\n<b>Пулл приветок:</b> {pull}',
        reply_markup=chain_remote_key(chain_id, is_started), parse_mode="HTML")


@router.callback_query(lambda x: 'startchain_' in x.data)
async def startchain_handler(call: CallbackQuery, state: FSMContext, bot: Bot):
    chain_id = call.data.split('_')[1]
    chain = db.get_chain(chain_id)
    if chain['pull_id'] is not None:
        privets = db.get_privets(chain['pull_id'])
        privets_ids = [p['id'] for p in privets]
        elements = db.get_elements(chain['id'])
        # db.add_crm_link('any', 'any', 0, elements[0]['id'], 0, 1, chain_id, 0, 0, 0, True)
        privets_for_elements = {}
        for x, element in enumerate(elements[1:]):
            last_element = elements[x]
            new_privet = choice(privets_ids)
            privets_ids.pop(privets_ids.index(new_privet))
            link_name = str(uuid.uuid4())[:8]
            link = await create_link_in_channel(element['channel_id'],link_name[:8])
            previuos = 0
            previuos_pair = db.get_links_by_chain_and_positions_actual(chain['id'], element['queue']-2, element['queue']-1)
            if previuos_pair is not None:
                previuos = previuos_pair['id']
            db.add_crm_link(link_name, link, last_element['id'], element['id'], last_element['queue'], element['queue'], chain_id, new_privet, 0, 0, True, previuos)
        await call.answer('Цепь была запущена. Ссылки созданы ✅', show_alert=True)
        await call.message.edit_reply_markup(reply_markup=chain_remote_key(chain_id, True))
    else:
        await call.answer('Вы не выбрали пулл приветок!', show_alert=True)


@router.callback_query(lambda x: 'privetoflastelement_' in x.data)
async def privetoflastelement_handler(call: CallbackQuery, state: FSMContext):
    chain_id = call.data.split('_')[1]
    chain = db.get_chain(chain_id)
    privet = chain['last_element_privet'] if chain['last_element_privet'] is not None else chain['last_element_privet']
    await call.message.edit_text('Укажите новую приветку в формате:\n\nТекст\n-\nКнопка 1 * Ссылка | Кнопка 2 * Ссылка\nКнопка 3 * Ссылка', reply_markup=back())
    await state.set_state(chain_last_privet_state.message)
    await state.update_data(chain_id=chain_id)

@router.message(chain_last_privet_state.message)
async def chain_last_privet_state_handler(message: Message, state: FSMContext):
    parse_message = parse_last_privet_message(message.text)
    state_data = await state.get_data()
    db.update_last_element_privet(state_data['chain_id'], str({'text': parse_message[0], 'keyboard': parse_message[1]}))
    await message.answer('Обновлено! ✅', reply_markup=back())

@router.callback_query(lambda x: 'viewlastprivet_' in x.data)
async def viewlastprivet_handler(call: CallbackQuery):
    chain_id = call.data.split('_')[1]
    chain = db.get_chain(chain_id)
    if chain['last_element_privet'] is not None:
        last_element_privet = eval(chain['last_element_privet'])
        keyboard_ = build_last_privet_keyboard(last_element_privet['keyboard'], True)
        await call.message.answer(last_element_privet['text'], reply_markup=keyboard_)
    else:
        await call.answer('Не добавлено!', show_alert=True)

@router.callback_query(lambda x: 'delchain_' in x.data)
async def delchain_han(call: CallbackQuery):
    chain_id = call.data.split('_')[1]
    chain = db.get_chain(chain_id)
    await call.message.edit_text('<b>Уверены ли вы, что хотите удалить цепь?</b>\n\nВместе с ней будут удалены все звенья. Файл статистики будет отправлен Вам', parse_mode="HTML", reply_markup=del_chain_key(chain_id, chain['name']))

@router.callback_query(lambda x: 'DLCHN_' in x.data)
async def DLCHN_handler(call: CallbackQuery, state: FSMContext):
    db.delete_chain(call.data.split('_')[1])
    await call.message.edit_text('Цепь была удалена. Загружаю статистику по ней...', reply_markup=back())


@router.callback_query(lambda x: 'chainstate_' in x.data)
async def chainstate_handler(call: CallbackQuery, state: FSMContext):
    chain = db.get_chain(call.data.split('_')[1])
    elements = db.get_elements(chain['id'])
    max_element_id = sorted(elements, key=lambda x: x['queue'])[-1]['queue']
    print(f'max {max_element_id}')
    for i in elements:
        print(i['queue'])
        actual_link = db.get_links_by_chain_and_positions_actual(chain['id'], i['queue'], i['queue'] + 1)
        next_link = db.get_links_by_chain_and_positions_actual(chain['id'], i['queue']+1, i['queue']+2)
        privet = db.get_privet_by_id_and_pull(actual_link['privet_id'], chain['pull_id'])
        if i['queue'] != max_element_id:
            await call.message.answer(f'''<b>👔 Звено №{i["queue"]}</b> {"- оригинальный канал" if i['main'] else ''}
        
🔹 Актуальная приветка: ниже
🔹 Залито: {actual_link['requests']}
🔹 Перелито: {next_link['requests'] if next_link is not None else 'следующее звено последнее в цепи'}
🔹 Конверсия: {next_link['requests']/actual_link['requests'] if actual_link['requests'] != 0 else 0}

    ''', parse_mode="HTML")

            await call.message.answer(privet['text'], reply_markup=build_privet_keyboard(privet['keyboard'], 't.me'), parse_mode="HTML")
    # export_conversion_to_excel(db.get_privets(chain['pull_id']), db.get_all_actual_crm_links_by_chain_id(chain['id']), db.get_elements(chain['id']),
    # await call.message.answer_document(types.FSInputFile('files/стата_по_цепи.xlsx'))