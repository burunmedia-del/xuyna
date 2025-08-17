from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.filters import CommandStart, Command
import re
from aiogram.utils.token import validate_token
from aiogram.utils.token import TokenValidationError
from data.config import BASE_WEBHOOK_URL, FOR_OTHER_BOTS
from keyboards import *
from aiogram.fsm.context import FSMContext
from filters.start_filters import *
from data.database import Database
from utils.keyboards import build_privet_keyboard, build_last_privet_keyboard
from utils.channels import create_link_in_channel
from utils.crm_auto import change_privet
from utils.channels_u import get_requests_count

from random import choice
import uuid
import os
import json
from datetime import datetime

router = Router()
db = Database()


def _ensure_logs_dir():
    os.makedirs("logs", exist_ok=True)


def _log_event(event: str, **payload):
    _ensure_logs_dir()
    now = datetime.now()
    path = os.path.join("logs", f"{now.strftime('%Y-%m-%d')}.txt")
    record = {"ts": now.isoformat(timespec="seconds"), "event": event, **payload}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_conversion_for_privet(link, previous_requests=0):
    """Рассчитывает конверсию для указанной ссылки."""
    current_requests = link['requests']
    if previous_requests == 0:
        if not link['previous_pair']:
            _log_event("conversion_error", link_id=link['id'], note="Нет previous_pair")
            return {"link_id": link['id'], "conversion": None, "note": "Нет previous_pair"}
        previous = db.get_crm_link_by_id(link['previous_pair'])
        if not previous:
            _log_event("conversion_error", link_id=link['id'], previous_id=link['previous_pair'],
                       error="Previous link not found")
            return {"link_id": link['id'], "conversion": None,
                    "note": f"Previous link {link['previous_pair']} not found"}
        prev_requests = previous['requests']
        conversion = round((current_requests / prev_requests) * 100, 2) if prev_requests > 0 else 0
        _log_event("conversion_calculated", link_id=link['id'], current_requests=current_requests,
                   previous_requests=prev_requests, conversion=conversion, mode="previous_pair")
        return {
            "link_id": link['id'],
            "current_requests": current_requests,
            "previous_requests": prev_requests,
            "conversion": conversion,
            "mode": "previous_pair"
        }
    else:
        prev_requests = previous_requests
        conversion = round((current_requests / prev_requests) * 100, 2) if prev_requests > 0 else 0
        _log_event("conversion_calculated", link_id=link['id'], current_requests=current_requests,
                   previous_requests=prev_requests, conversion=conversion, mode="provided_requests")
        return {
            "link_id": link['id'],
            "current_requests": current_requests,
            "previous_requests": prev_requests,
            "conversion": conversion,
            "mode": "provided_requests"
        }


def get_used_privet_ids_for_pair(chain_id, element1_position, element2_position):
    """Получает ID всех приветок, использованных для данной пары позиций."""
    links = db.get_links_by_chain_and_positions(chain_id, element1_position, element2_position)
    return {link['privet_id'] for link in links}


def get_next_free_privet_id(chain_id, pull_id, element1_position, element2_position):
    """Находит ID следующей свободной приветки из пула."""
    all_privets = db.get_privets(pull_id)
    used = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    active = db.get_active_privet_ids(chain_id)
    free = [p['id'] for p in all_privets if p['id'] not in used and p['id'] not in active]
    return choice(free) if free else None


def get_best_privet_id_for_pair(chain_id, pull_id, element1_position, element2_position):
    """Находит ID приветки с лучшей конверсией для данной пары позиций."""
    used_privets = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    if not used_privets:
        return None
    best_id = None
    best_conv = -1
    for pid in used_privets:
        link = db.get_crm_link_by_privet_and_positions(chain_id, element1_position, element2_position, pid)
        if not link:
            continue
        conv_info = get_conversion_for_privet(link)
        conv = conv_info.get('conversion')
        if conv is None:
            continue
        if conv > best_conv:
            best_conv = conv
            best_id = pid
    return best_id


def get_current_conversion(chain_id, element1_position, element2_position):
    """Получает конверсию текущей активной ссылки."""
    link = db.get_links_by_chain_and_positions_actual(chain_id, element1_position, element2_position)
    if not link:
        return None
    return get_conversion_for_privet(link).get('conversion')


def find_better_privet_id(chain_id, pull_id, element1_position, element2_position, threshold=5):
    """Находит ID приветки, которая на threshold% лучше текущей."""
    current_conv = get_current_conversion(chain_id, element1_position, element2_position)
    if current_conv is None:
        return None
    link = db.get_links_by_chain_and_positions_actual(chain_id, element1_position, element2_position)
    used_privets = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    best_id = None
    best_conv = current_conv
    for pid in used_privets:
        if pid == link['privet_id']:
            continue
        privet_link = db.get_crm_link_by_privet_and_positions(chain_id, element1_position, element2_position, pid)
        if not privet_link:
            continue
        conv_info = get_conversion_for_privet(privet_link)
        conv = conv_info.get('conversion')
        if conv is None:
            continue
        if conv > best_conv + threshold:
            best_conv = conv
            best_id = pid
    return best_id


async def switch_to_new_privet(chain_id, element1_position, element2_position, new_privet_id):
    """Переключает приветку и создаёт новые ссылки для текущего и предыдущего звеньев."""
    current_link = db.get_links_by_chain_and_positions_actual(chain_id, element1_position, element2_position)
    if not current_link:
        _log_event("switch_privet_error", chain_id=chain_id, element1_position=element1_position,
                   element2_position=element2_position, error="Current link not found")
        return
    old_privet_id = current_link['privet_id']
    db.set_link_actual_false_by_id(current_link['id'])
    element1 = db.get_element(current_link['element1_id'])
    element2 = db.get_element(current_link['element2_id'])

    # Создаём новую ссылку для текущего канала (element2) с той же приветкой
    new_link_url = await create_link_in_channel(element2['channel_id'], f"link_{uuid.uuid4().hex}")

    # Определяем previous_pair
    prev_pos1 = element1_position - 1
    previous_pair = 0
    if prev_pos1 >= 1:
        prev_pos2 = element1_position
        prev_link = db.get_links_by_chain_and_positions_actual(chain_id, prev_pos1, prev_pos2)
        if prev_link:
            # Создаём новую ссылку для предыдущего канала с новой приветкой
            prev_element1 = db.get_element(prev_link['element1_id'])
            prev_element2 = db.get_element(prev_link['element2_id'])
            new_prev_link_url = await create_link_in_channel(prev_element2['channel_id'], f"link_{uuid.uuid4().hex}")
            db.set_link_actual_false_by_id(prev_link['id'])
            db.add_crm_link(
                name=prev_link['name'],
                link=new_prev_link_url,
                element1_id=prev_link['element1_id'],
                element2_id=prev_link['element2_id'],
                element1_position=prev_pos1,
                element2_position=prev_pos2,
                chain_id=chain_id,
                privet_id=new_privet_id,  # Новая приветка для предыдущего звена
                requests=0,
                actual=True
            )
            new_prev_link = db.get_links_by_chain_and_positions_actual(chain_id, prev_pos1, prev_pos2)
            previous_pair = new_prev_link['id'] if new_prev_link else 0

    # Создаём новую ссылку для текущего канала
    requests = current_link['requests'] if new_privet_id == old_privet_id else 0
    db.add_crm_link(
        name=current_link['name'],
        link=new_link_url,
        element1_id=current_link['element1_id'],
        element2_id=current_link['element2_id'],
        element1_position=element1_position,
        element2_position=element2_position,
        chain_id=chain_id,
        privet_id=old_privet_id,  # Сохраняем текущую приветку для следующего звена
        requests=0,  # Сбрасываем requests для новой ссылки
        last_privet=old_privet_id,
        actual=True,
        previous_pair=previous_pair
    )
    _log_event("switch_privet_success", chain_id=chain_id, element1_position=element1_position,
               element2_position=element2_position, old_privet_id=old_privet_id, new_privet_id=new_privet_id,
               new_link_url=new_link_url)

@router.chat_join_request()
async def request_handler(update: ChatJoinRequest, bot: Bot):
    print(update)
    rc = db.get_config_value('RC')

    link = update.invite_link
    link_url = link.invite_link

    link_in_db = db.get_link_by_partial_link(link_url[:-3])
    element = db.get_element_by_channel_id(update.chat.id)

    if link_in_db is None and (element is None or element['main'] != True):
        return

    chain = db.get_chain(element['chain_id'])

    if element['queue'] == max([i['queue'] for i in db.get_elements(chain['id'])]):
        last_privet = eval(chain['last_element_privet'])
        keyboard = build_last_privet_keyboard(last_privet['keyboard'])
        await bot.send_message(update.from_user.id, text=last_privet['text'], reply_markup=keyboard)
        return

    if link_in_db is not None:
        next_link = db.get_links_by_chain_and_positions_actual(chain['id'], element['queue'], element['queue'] + 1)

    if element['main']:
        next_link = db.get_links_by_chain_and_positions_actual(chain['id'], 1, 2)

    privet = db.get_privet_by_id_and_pull(next_link['privet_id'], chain['pull_id'])
    keyboard = build_privet_keyboard(privet['keyboard'], next_link['link'])
    await bot.send_message(update.from_user.id, text=privet['text'], reply_markup=keyboard, parse_mode='HTML')

    if link_in_db is not None:
        new_requests = link.pending_join_request_count
        db.update_crm_link_requests(link_in_db['id'], new_requests)
        chain_id = link_in_db['chain_id']
        chain = db.get_chain(chain_id)
        pull_id = chain['pull_id']
        pos1 = link_in_db['element1_position']
        pos2 = link_in_db['element2_position']

        # Проверяем конверсию только если auto = False
        if not element['auto']:
            better_id = find_better_privet_id(chain_id, pull_id, pos1, pos2, 5)
            if better_id:
                _log_event("change_privet", chain_id=chain_id, element1_position=pos1, element2_position=pos2,
                           old_privet_id=link_in_db['privet_id'], new_privet_id=better_id, reason="better_conversion")
                await switch_to_new_privet(chain_id, pos1, pos2, better_id, bot)
                return

        if new_requests >= int(rc):
            next_id = get_next_free_privet_id(chain_id, pull_id, pos1, pos2)
            if next_id is None:
                next_id = get_best_privet_id_for_pair(chain_id, pull_id, pos1, pos2)
            if next_id:
                _log_event("change_privet", chain_id=chain_id, element1_position=pos1, element2_position=pos2,
                           old_privet_id=link_in_db['privet_id'], new_privet_id=next_id, reason="reached_rc")
                await switch_to_new_privet(chain_id, pos1, pos2, next_id, bot)