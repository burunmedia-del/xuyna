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
from utils.crm_auto import change_privet, find_better_privet_id
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

@router.chat_join_request()
async def request_handler(update: ChatJoinRequest, bot: Bot):
    try:
        RC = int(db.get_config_value('rc'))
        update_link_full = update.invite_link.invite_link if update.invite_link else None
        update_link_name = update.invite_link.name if update.invite_link else None
        update_link_requests = 1  # Фиксированное значение вместо pending_join_request_count
        update_channel_id = update.chat.id
        update_user_id = update.from_user.id

        _log_event(
            "join_request_received",
            user_id=update_user_id,
            chat_id=update_channel_id,
            link=update_link_full,
            link_name=update_link_name,
            link_requests=update_link_requests,
            rc=RC
        )

        element_by_chat_id = db.get_element_by_channel_id(update_channel_id)
        if element_by_chat_id is None:
            _log_event("no_element_for_channel", chat_id=update_channel_id)
            return

        sort = sorted(db.get_elements(element_by_chat_id['chain_id']), key=lambda x: x['queue'])
        if sort[-1] == element_by_chat_id:
            chain = db.get_chain(element_by_chat_id['chain_id'])
            if chain['last_element_privet'] is not None:
                last_privet = eval(chain['last_element_privet'])
                last_privet_text = last_privet['text']
                last_privet_keyboard = build_last_privet_keyboard(last_privet['keyboard'])
                _log_event(
                    "send_last_privet",
                    user_id=update_user_id,
                    chat_id=update_channel_id,
                    chain_id=element_by_chat_id['chain_id']
                )
                await bot.send_message(
                    chat_id=update_user_id,
                    text=last_privet_text,
                    reply_markup=last_privet_keyboard,
                    parse_mode="HTML"
                )
                return

        if element_by_chat_id['main']:
            next_link = db.get_links_by_chain_and_positions_actual(element_by_chat_id['chain_id'], 1, 2)
            last_change_requests = element_by_chat_id['last_change_requests']
            requests_in_main_channel_now = await get_requests_count(update_channel_id)

            _log_event(
                "main_channel_state",
                chat_id=update_channel_id,
                chain_id=element_by_chat_id['chain_id'],
                last_change_requests=last_change_requests,
                requests_now=requests_in_main_channel_now,
                threshold_rc=RC,
                auto=bool(element_by_chat_id['auto']),
                next_link_id=next_link['id'] if next_link else None
            )

            if requests_in_main_channel_now - last_change_requests >= RC:
                _log_event(
                    "rc_exceeded_main",
                    delta=requests_in_main_channel_now - last_change_requests
                )
                chain = db.get_chain(element_by_chat_id['chain_id'])
                if element_by_chat_id['auto'] and next_link:
                    await change_privet(next_link)
                    db.update_element_last_change_requests(element_by_chat_id['id'], requests_in_main_channel_now)
                    _log_event(
                        "privet_changed_main",
                        element_id=element_by_chat_id['id'],
                        new_last_change_requests=requests_in_main_channel_now,
                        next_link_id=next_link['id']
                    )
                elif not element_by_chat_id['auto'] and next_link:
                    better_id = find_better_privet_id(element_by_chat_id['chain_id'], chain['pull_id'], 1, 2, 5)
                    if better_id:
                        _log_event(
                            "privet_changed_better_conversion",
                            element_id=element_by_chat_id['id'],
                            old_privet_id=next_link['privet_id'],
                            new_privet_id=better_id,
                            reason="better_conversion"
                        )
                        await change_privet(next_link, new_privet_id=better_id)
                        db.update_element_last_change_requests(element_by_chat_id['id'], requests_in_main_channel_now)

            if next_link:
                next_link_privet = db.get_privet_by_id(next_link['privet_id'])
                text_for_send = next_link_privet['text']
                keyboard_for_attach = build_privet_keyboard(next_link_privet['keyboard'], next_link['link'])
                _log_event(
                    "send_next_privet_main",
                    user_id=update_user_id,
                    chat_id=update_channel_id,
                    next_link_id=next_link['id']
                )
                await bot.send_message(
                    chat_id=update_user_id,
                    text=text_for_send,
                    reply_markup=keyboard_for_attach,
                    parse_mode='HTML'
                )
            return

        link = None
        if update_link_full:
            link = db.get_link_by_partial_link(update_link_full[:-3])

        if link is None:
            _log_event(
                "no_link_for_partial",
                chat_id=update_channel_id,
                link_partial=update_link_full[:-3] if update_link_full else None
            )
            return

        next_link = db.get_links_by_chain_and_positions_actual(
            element_by_chat_id['chain_id'],
            link['element2_position'],
            link['element2_position'] + 1
        )

        _log_event(
            "non_main_flow_state",
            chat_id=update_channel_id,
            chain_id=element_by_chat_id['chain_id'],
            current_link_id=link['id'],
            current_link_requests=link['requests'],
            update_link_requests=update_link_requests,
            threshold_rc=RC,
            auto=bool(element_by_chat_id['auto']),
            next_link_id=next_link['id'] if next_link else None
        )

        if update_link_requests is not None and update_link_requests > link['requests']:
            db.update_crm_link_requests(link['id'], update_link_requests)
            _log_event(
                "link_requests_updated",
                link_id=link['id'],
                new_requests=update_link_requests
            )
            chain = db.get_chain(element_by_chat_id['chain_id'])
            if update_link_requests >= RC and element_by_chat_id['auto'] and next_link:
                await change_privet(next_link)
                _log_event(
                    "privet_changed_non_main",
                    element_id=element_by_chat_id['id'],
                    next_link_id=next_link['id']
                )
            elif update_link_requests >= RC and not element_by_chat_id['auto'] and next_link:
                better_id = find_better_privet_id(element_by_chat_id['chain_id'], chain['pull_id'], link['element2_position'], link['element2_position'] + 1, 5)
                if better_id:
                    _log_event(
                        "privet_changed_better_conversion",
                        element_id=element_by_chat_id['id'],
                        old_privet_id=next_link['privet_id'],
                        new_privet_id=better_id,
                        reason="better_conversion"
                    )
                    await change_privet(next_link, new_privet_id=better_id)

        if next_link:
            next_link_privet = db.get_privet_by_id(next_link['privet_id'])
            text_for_send = next_link_privet['text']
            keyboard_for_attach = build_privet_keyboard(next_link_privet['keyboard'], next_link['link'])
            _log_event(
                "send_next_privet_non_main",
                user_id=update_user_id,
                chat_id=update_channel_id,
                next_link_id=next_link['id']
            )
            await bot.send_message(
                chat_id=update_user_id,
                text=text_for_send,
                reply_markup=keyboard_for_attach,
                parse_mode='HTML'
            )

    except Exception as e:
        _log_event("error", error=str(e), chat_id=update.chat.id if update and update.chat else None)
        raise