from data.database import Database
import uuid
from .channels import create_link_in_channel
from random import choice
import datetime
import time
import traceback
import json
import os
import logging

logger = logging.getLogger(__name__)
db = Database()

LOGS_DIR = "logs"

def _ensure_logs_dir():
    os.makedirs(LOGS_DIR, exist_ok=True)

def log_change_privet(message: str, trace_id: str, **extra):
    now = datetime.datetime.now()
    ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    base = f"{ts_str} | trace={trace_id} | {message}"
    if extra:
        kv = " ".join(f"{k}={repr(v)}" for k, v in extra.items())
        base = f"{base} | {kv}"
    _write_log_line(base, now)

    json_record = {
        "ts": ts_str,
        "trace": trace_id,
        "msg": message,
        **extra
    }
    _write_log_line(json.dumps(json_record, ensure_ascii=False), now)
def _log_file_path(ts: datetime.datetime | None = None) -> str:
    if ts is None:
        ts = datetime.datetime.now()
    return os.path.join(LOGS_DIR, f"change_privet_{ts.strftime('%Y-%m-%d')}.txt")

def _write_log_line(text: str, ts: datetime.datetime | None = None):
    _ensure_logs_dir()
    path = _log_file_path(ts)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def log_change_privet(message: str, trace_id: str, **extra):
    now = datetime.datetime.now()
    ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    base = f"{ts_str} | trace={trace_id} | {message}"
    if extra:
        kv = " ".join(f"{k}={repr(v)}" for k, v in extra.items())
        base = f"{base} | {kv}"
    _write_log_line(base, now)

    json_record = {
        "ts": ts_str,
        "trace": trace_id,
        "msg": message,
        **extra
    }
    _write_log_line(json.dumps(json_record, ensure_ascii=False), now)

class StepTimer:
    def __init__(self, name: str, trace_id: str):
        self.name = name
        self.trace_id = trace_id
        self.t0 = None
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        dt = (time.perf_counter() - self.t0) * 1000.0
        if exc:
            log_change_privet(
                f"Шаг '{self.name}' завершился ОШИБКОЙ",
                self.trace_id,
                duration_ms=round(dt, 2),
                error=str(exc)
            )
        else:
            log_change_privet(
                f"Шаг '{self.name}' выполнен",
                self.trace_id,
                duration_ms=round(dt, 2)
            )

def get_conversion_for_privet(link, previous_requests=0):
    current_requests = link['requests']
    if previous_requests == 0:
        if not link['previuos_pair']:
            log_change_privet("conversion_error", trace_id=str(uuid.uuid4()), link_id=link['id'], note="Нет previuos_pair")
            return {"link_id": link['id'], "conversion": None, "note": "Нет previuos_pair"}
        previous = db.get_crm_link_by_id(link['previuos_pair'])
        if not previous:
            log_change_privet("conversion_error", trace_id=str(uuid.uuid4()), link_id=link['id'], previous_id=link['previuos_pair'],
                              error="Previous link not found")
            return {"link_id": link['id'], "conversion": None,
                    "note": f"Previous link {link['previuos_pair']} not found"}
        prev_requests = previous['requests']
        conversion = round((current_requests / prev_requests) * 100, 2) if prev_requests > 0 else 0
        log_change_privet("conversion_calculated", trace_id=str(uuid.uuid4()), link_id=link['id'], current_requests=current_requests,
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
        log_change_privet("conversion_calculated", trace_id=str(uuid.uuid4()), link_id=link['id'], current_requests=current_requests,
                          previous_requests=prev_requests, conversion=conversion, mode="provided_requests")
        return {
            "link_id": link['id'],
            "current_requests": current_requests,
            "previous_requests": prev_requests,
            "conversion": conversion,
            "mode": "provided_requests"
        }

def get_used_privet_ids_for_pair(chain_id, element1_position, element2_position):
    links = db.get_links_by_chain_and_positions(chain_id, element1_position, element2_position)
    return {link['privet_id'] for link in links}

def get_next_free_privet_id(chain_id, pull_id, element1_position, element2_position):
    all_privets = db.get_privets(pull_id)
    used = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    active = db.get_active_privet_ids(chain_id)
    free = [p['id'] for p in all_privets if p['id'] not in used and p['id'] not in active]
    return choice(free) if free else None

def get_best_privet_id_for_pair(chain_id, pull_id, element1_position, element2_position):
    used_privets = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    if not used_privets:
        log_change_privet("no_used_privets", trace_id=str(uuid.uuid4()), chain_id=chain_id, element1_position=element1_position, element2_position=element2_position)
        return None
    best_id = None
    best_conv = -1
    for pid in used_privets:
        link = db.get_crm_link_by_privet_and_positions(chain_id, element1_position, element2_position, pid)
        if not link:
            log_change_privet("no_link_for_privet", trace_id=str(uuid.uuid4()), chain_id=chain_id, element1_position=element1_position, element2_position=element2_position, privet_id=pid)
            continue
        conv_info = get_conversion_for_privet(link)
        conv = conv_info.get('conversion')
        if conv is None:
            continue
        if conv > best_conv:
            best_conv = conv
            best_id = pid
    if best_id:
        log_change_privet(
            "best_privet_found",
            trace_id=str(uuid.uuid4()),
            chain_id=chain_id,
            element1_position=element1_position,
            element2_position=element2_position,
            privet_id=best_id,
            conversion=best_conv
        )
    return best_id

def find_better_privet_id(chain_id, pull_id, element1_position, element2_position, threshold=5):
    current_link = db.get_links_by_chain_and_positions_actual(chain_id, element1_position, element2_position)
    if not current_link:
        log_change_privet("no_current_link", trace_id=str(uuid.uuid4()), chain_id=chain_id, element1_position=element1_position, element2_position=element2_position)
        return None

    current_conv = get_conversion_for_privet(current_link).get('conversion')
    if current_conv is None:
        log_change_privet("no_current_conversion", trace_id=str(uuid.uuid4()), link_id=current_link['id'])
        return None

    used_privets = get_used_privet_ids_for_pair(chain_id, element1_position, element2_position)
    best_id = None
    best_conv = current_conv

    for pid in used_privets:
        if pid == current_link['privet_id']:
            continue
        privet_link = db.get_crm_link_by_privet_and_positions(chain_id, element1_position, element2_position, pid)
        if not privet_link:
            log_change_privet("no_link_for_privet", trace_id=str(uuid.uuid4()), chain_id=chain_id, element1_position=element1_position, element2_position=element2_position, privet_id=pid)
            continue
        conv_info = get_conversion_for_privet(privet_link)
        conv = conv_info.get('conversion')
        if conv is None:
            continue
        if conv > best_conv + threshold:
            best_conv = conv
            best_id = pid

    if best_id:
        log_change_privet(
            "better_privet_found",
            trace_id=str(uuid.uuid4()),
            chain_id=chain_id,
            element1_position=element1_position,
            element2_position=element2_position,
            old_privet_id=current_link['privet_id'],
            new_privet_id=best_id,
            old_conversion=current_conv,
            new_conversion=best_conv
        )
    return best_id

async def change_privet(link, new_privet_id=None):
    trace_id = str(uuid.uuid4())
    log_change_privet("Запуск change_privet", trace_id, link_summary={k: link.get(k) for k in ("id","name","chain_id","element1_position","element2_position","privet_id")})

    required_keys = ["chain_id", "element2_id", "element1_position", "element2_position", "id", "name", "privet_id"]
    missing = [k for k in required_keys if k not in link]
    if missing:
        log_change_privet("Отсутствуют обязательные ключи в link", trace_id, missing=missing)
        raise KeyError(f"change_privet: missing keys in link: {missing}")

    try:
        with StepTimer("Получение chain", trace_id):
            chain = db.get_chain(link["chain_id"])
        log_change_privet("Получена chain", trace_id, chain_id=chain.get("id"), pull_id=chain.get("pull_id"))

        with StepTimer("Получение element (element2)", trace_id):
            element = db.get_element(link["element2_id"])
        log_change_privet("Получен element", trace_id, element_id=element.get("id"), channel_id=element.get("channel_id"))

        with StepTimer("Пометка старой ссылки как неактуальной", trace_id):
            db.set_link_actual_false_by_id(link["id"])
        log_change_privet("Старая ссылка помечена неактуальной", trace_id, link_id=link["id"])

        # Создание новой ссылки для текущего звена с той же приветкой
        with StepTimer("Создание новой ссылки в канале", trace_id):
            new_link = await create_link_in_channel(element["channel_id"], link["name"])
        log_change_privet("Создана новая ссылка для текущего звена", trace_id, new_link=new_link)

        with StepTimer("Получение prev_pair", trace_id):
            prev_pair = db.get_links_by_chain_and_positions_actual(
                chain["id"],
                link["element1_position"] - 1,
                link["element2_position"] - 1
            )
        prev_id = prev_pair["id"] if prev_pair else 0
        log_change_privet("Определён prev_id", trace_id, prev_id=prev_id)

        with StepTimer("Добавление новой CRM-ссылки в БД", trace_id):
            db.add_crm_link(
                name=link["name"],
                link=new_link,
                element1_id=link["element1_id"],
                element2_id=link["element2_id"],
                element1_position=link["element1_position"],
                element2_position=link["element2_position"],
                chain_id=chain["id"],
                privet_id=link["privet_id"],  # Сохраняем текущую приветку
                requests=0,
                last_privet=0,
                actual=True,
                previous_pair=prev_id
            )
        log_change_privet("Новая CRM-ссылка добавлена для текущего звена", trace_id, chain_id=chain["id"], privet_id=link["privet_id"], prev_id=prev_id)

        # Создание новой ссылки для предыдущего звена
        prev_pos1 = link["element1_position"] - 1
        if prev_pos1 >= 1:
            prev_pos2 = link["element1_position"]
            prev_link = db.get_links_by_chain_and_positions_actual(chain["id"], prev_pos1, prev_pos2)
            if prev_link:
                with StepTimer("Получение element для предыдущего звена", trace_id):
                    prev_element = db.get_element(prev_link["element2_id"])
                log_change_privet("Получен element для предыдущего звена", trace_id, element_id=prev_element.get("id"), channel_id=prev_element.get("channel_id"))

                with StepTimer("Сбор used_privets для предыдущего звена", trace_id):
                    used_privets = [
                        x["privet_id"]
                        for x in db.get_links_by_chain_and_positions(chain["id"], prev_pos1, prev_pos2)
                    ]
                log_change_privet("Собраны used_privets для предыдущего звена", trace_id, count=len(used_privets), sample=used_privets[:10])

                with StepTimer("Сбор not_available для предыдущего звена", trace_id):
                    not_available = [
                        x["privet_id"]
                        for x in db.get_all_actual_crm_links_by_chain_id(chain["id"])
                    ]
                log_change_privet("Собраны not_available для предыдущего звена", trace_id, count=len(not_available), sample=not_available[:10])

                cant_use = set(used_privets + not_available)
                log_change_privet("Собран cant_use для предыдущего звена", trace_id, count=len(cant_use))

                with StepTimer("Получение all_privets из пула", trace_id):
                    all_privets = [p["id"] for p in db.get_privets(chain["pull_id"])]
                log_change_privet("Получены all_privets для предыдущего звена", trace_id, count=len(all_privets), sample=all_privets[:10])

                can_use = [p for p in all_privets if p not in cant_use]
                log_change_privet("Посчитан can_use для предыдущего звена", trace_id, count=len(can_use), sample=can_use[:10])

                prev_new_privet = new_privet_id
                if not prev_new_privet:
                    if can_use:
                        prev_new_privet = choice(can_use)
                        log_change_privet("Выбрана свободная приветка для предыдущего звена", trace_id, new_privet=prev_new_privet)
                    else:
                        log_change_privet("Свободных нет — ищем лучшую по конверсии для предыдущего звена", trace_id)
                        prev_new_privet = get_best_privet_id_for_pair(chain["id"], chain["pull_id"], prev_pos1, prev_pos2)
                        if not prev_new_privet:
                            prev_new_privet = prev_link["privet_id"]  # Fallback: текущая приветка
                            log_change_privet("Нет доступных или лучших приветок, используется текущая", trace_id, new_privet=prev_new_privet)

                if prev_new_privet:
                    with StepTimer("Создание новой ссылки для предыдущего звена", trace_id):
                        new_prev_link_url = await create_link_in_channel(prev_element["channel_id"], prev_link["name"])
                    log_change_privet("Создана новая ссылка для предыдущего звена", trace_id, new_link=new_prev_link_url)

                    with StepTimer("Пометка старой ссылки как неактуальной (предыдущее звено)", trace_id):
                        db.set_link_actual_false_by_id(prev_link["id"])
                    log_change_privet("Старая ссылка помечена неактуальной (предыдущее звено)", trace_id, link_id=prev_link["id"])

                    with StepTimer("Добавление новой CRM-ссылки для предыдущего звена", trace_id):
                        db.add_crm_link(
                            name=prev_link["name"],
                            link=new_prev_link_url,
                            element1_id=prev_link["element1_id"],
                            element2_id=prev_link["element2_id"],
                            element1_position=prev_pos1,
                            element2_position=prev_pos2,
                            chain_id=chain["id"],
                            privet_id=prev_new_privet,
                            requests=0,
                            last_privet_requests=0,  # Исправлено
                            actual=True,
                            previuos_pair=0
                        )
                    log_change_privet(
                        "new_link_created_prev",
                        trace_id,
                        chain_id=chain["id"],
                        element1_position=prev_pos1,
                        element2_position=prev_pos2,
                        new_privet=prev_new_privet,
                        new_link_url=new_prev_link_url
                    )

        log_change_privet("Успешное завершение change_privet", trace_id)

    except Exception as e:
        tb = traceback.format_exc()
        log_change_privet("ОШИБКА в change_privet", trace_id, error=str(e), traceback=tb)
        raise