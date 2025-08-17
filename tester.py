import requests
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import pymysql
from data.database import Database  # Импортируем класс Database
from data.config import *  # Импортируем конфигурацию базы данных

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Словарь для хранения pending_join_request_count для каждой ссылки
pending_counts = {}

def send_webhook(url, data, link_id):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Python-Requests",
        "X-Webhook-Secret": "my-secret"
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            logger.info(f"Запрос успешно отправлен на {url} для ссылки {link_id}. pending_join_request_count: {data['chat_join_request']['invite_link']['pending_join_request_count']}")
            return True
        else:
            logger.error(f"Ошибка при отправке запроса на {url} для ссылки {link_id}. Код: {response.status_code}, Ответ: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса на {url} для ссылки {link_id}: {e}")
        return False

def create_db_connection():
    """Создаёт новое соединение с базой данных для каждого потока"""
    try:
        connection = pymysql.connect(
            host=MYSQL_host,
            user=MYSQL_user,
            password=MYSQL_password,
            database=MYSQL_database,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        connection.autocommit(True)
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        return connection
    except pymysql.err.Error as e:
        logger.error(f"Ошибка при создании соединения с БД: {e}")
        return None

def process_link(link):
    link_id = link['id']
    link_url = link['link']
    element1_id = link['element1_id']
    logger.info(f"Обработка ссылки {link_id} с element1_id={element1_id}")

    # Создаём новое соединение для этого потока
    connection = create_db_connection()
    if not connection:
        logger.error(f"Не удалось создать соединение с БД для ссылки {link_id}")
        return

    try:
        with connection.cursor() as cursor:
            # Получаем информацию об элементе (бота) по element1_id
            cursor.execute("SELECT * FROM elements WHERE id = %s", (element1_id,))
            element = cursor.fetchone()
            if not element:
                logger.error(f"Элемент с ID {element1_id} не найден для ссылки {link_id}")
                return

            bot_token = element['bot_token']
            chat_id = element['channel_id']
            if not bot_token:
                logger.error(f"Токен бота не найден для элемента {element1_id}")
                return
            if not chat_id:
                logger.error(f"ID канала не найден для элемента {element1_id}")
                return

            # Формируем URL вебхука
            webhook_url = f"https://991bbfb8c469.ngrok-free.app/svinotraff/bot/{bot_token}"

            # Увеличиваем pending_join_request_count для этой ссылки
            pending_counts[link_id] = pending_counts.get(link_id, link.get('pending_join_request_count', 0)) + 1
            logger.info(f"Установлен pending_join_request_count={pending_counts[link_id]} для ссылки {link_id}")

            # Формируем данные для отправки
            data = {
                "update_id": int(datetime.now(tz=ZoneInfo("UTC")).timestamp() * 1000),  # Уникальный ID
                "chat_join_request": {
                    "chat": {
                        "id": chat_id,  # Берем chat_id из element['channel_id']
                        "type": "channel",
                        "title": element.get('channel_name', "ЗВЕНО 1 NEW")  # Используем channel_name или дефолт
                    },
                    "from": {
                        "id": 6617138756,
                        "is_bot": False,
                        "first_name": "N1K_LL",
                        "username": "nnklllllllll",
                        "language_code": "ru"
                    },
                    "user_chat_id": 6617138756,
                    "date": int(datetime.now(tz=ZoneInfo("UTC")).timestamp()),  # Текущее время
                    "bio": None,
                    "invite_link": {
                        "invite_link": link_url,  # Используем ссылку из crm_links
                        "creator": {
                            "id": 5303987675,
                            "is_bot": False,
                            "first_name": "Cool WORK",
                            "username": "cool_bl"
                        },
                        "creates_join_request": True,
                        "is_primary": False,
                        "is_revoked": False,
                        "pending_join_request_count": pending_counts[link_id]  # Увеличиваемое значение
                    }
                }
            }

            # Отправляем запрос
            send_webhook(webhook_url, data, link_id)

    except Exception as e:
        logger.error(f"Ошибка при обработке ссылки {link_id}: {e}")
    finally:
        connection.close()  # Закрываем соединение

def main():
    db = Database()
    try:
        # Инициализируем пул потоков (10 потоков для начала)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                # Получаем все актуальные ссылки
                logger.info("Получение актуальных ссылок из crm_links...")
                crm_links = db.get_all_actual_crm_links()
                logger.info(f"Найдено {len(crm_links)} актуальных ссылок")
                if not crm_links:
                    logger.info("Актуальные ссылки не найдены. Продолжаем...")
                    continue

                # Запускаем обработку всех ссылок параллельно
                executor.map(process_link, crm_links)

                # Без задержки переходим к следующему циклу
                logger.info("Завершён цикл отправки. Продолжаем...")

    except KeyboardInterrupt:
        logger.info("Процесс остановлен пользователем")
    finally:
        db.close()
        logger.info("Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()