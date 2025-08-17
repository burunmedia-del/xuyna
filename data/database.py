import pymysql
import logging
import asyncio
import json
from data.config import *

class Database:
    def __init__(self, host=None, user=None, password=None, database=None):
        self.host = MYSQL_host
        self.user = MYSQL_user
        self.password = MYSQL_password
        self.database = MYSQL_database
        self.connection = None

    def ensure_connection(self):
        """Проверяет, есть ли подключение, и создаёт новое при необходимости"""
        if self.connection is None or not self.connection.open:
            self.connect()

    def connect(self):
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        self.connection.autocommit(True)
        with self.connection.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

    def execute_many(self, query, params_list):
        """Массово выполняет SQL-запросы (ускоряет работу)"""
        if not params_list:
            return  # Если передан пустой список, просто выходим

        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.executemany(query, params_list)
            self.connection.commit()  # ✅ Фиксируем изменения

    def close(self):
        """Закрывает соединение с БД"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_tables(self):
        """Создает таблицы, если их нет"""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    channel_id BIGINT, 
                    name TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    channel_id BIGINT,
                    title TEXT,
                    link TEXT,
                    price BIGINT NOT NULL DEFAULT 0,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    requests_before_start BIGINT NOT NULL DEFAULT 0,
                    start DATETIME DEFAULT NULL,
                    10m_requests BIGINT NOT NULL DEFAULT 0,
                    10m_joins BIGINT NOT NULL DEFAULT 0,
                    28m_requests BIGINT NOT NULL DEFAULT 0,
                    28m_joins BIGINT NOT NULL DEFAULT 0,
                    60m_requests BIGINT NOT NULL DEFAULT 0,
                    60m_joins BIGINT NOT NULL DEFAULT 0,
                    24h_requests BIGINT NOT NULL DEFAULT 0,
                    24h_joins BIGINT NOT NULL DEFAULT 0,
                    48h_requests BIGINT NOT NULL DEFAULT 0,
                    48h_joins BIGINT NOT NULL DEFAULT 0,
                    72h_requests BIGINT NOT NULL DEFAULT 0,
                    72h_joins BIGINT NOT NULL DEFAULT 0
                    
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chains (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name TEXT,
                    pull_id BIGINT, 
                    last_element_privet TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pulls (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS privets (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    text TEXT, 
                    keyboard TEXT, 
                    pull_id BIGINT,
                    FOREIGN KEY (pull_id) REFERENCES pulls(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elements (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    main BOOLEAN DEFAULT FALSE NOT NULL,
                    channel_id BIGINT, 
                    channel_name TEXT, 
                    bot_token TEXT,
                    bot_username TEXT,
                    bot_id BIGINT,
                    queue BIGINT,
                    chain_id BIGINT,
                    auto BIGINT,
                    last_change_requests BIGINT,
                    FOREIGN KEY (chain_id) REFERENCES chains(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crm_links (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name TEXT,
                    link TEXT,
                    element1_id BIGINT,
                    element2_id BIGINT, 
                    element1_position BIGINT, 
                    element2_position BIGINT,
                    chain_id BIGINT, 
                    privet_id BIGINT, 
                    requests BIGINT,
                    last_privet_requests BIGINT, 
                    previous_pair BIGINT, 
                    actual BOOLEAN
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    `key` VARCHAR(255) PRIMARY KEY,
                    value TEXT
                )
            """)
            self.connection.commit()

            initial_config = [
                ('rc', '200'),
                ('organize_time', '60')
            ]
            cursor.executemany("""
                INSERT IGNORE INTO configuration (`key`, value) VALUES (%s, %s)
            """, initial_config)

            self.connection.commit()

    def set_start_time(self, link_id: int):
        """Устанавливает текущее время в поле start для указанного id."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE links SET start = CURRENT_TIMESTAMP WHERE id = %s",
                (link_id,)
            )
        self.connection.commit()  # Фиксируем изменения

    def add_channel(self, channel_id, name):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM channels WHERE channel_id = %s ",
                (channel_id,)
            )
            existing_channel = cursor.fetchone()

            if existing_channel:
                return False

            cursor.execute(
                "INSERT INTO channels (channel_id, name) VALUES (%s, %s)",
                (channel_id, name)
            )
            self.connection.commit()
            return True  # Пользователь успешно добавлен

    def update_last_element_privet(self, chain_id: int, new_value: str) -> int:
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE chains SET last_element_privet = %s WHERE id = %s",
                (new_value, chain_id)
            )
            self.connection.commit()
            return cursor.rowcount  # сколько строк обновили

    def disable_element_auto(self, element_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE elements SET auto = FALSE WHERE id = %s", (element_id,))
            self.connection.commit()
            return cursor.rowcount  # сколько строк обновили

    def get_links_by_chain_and_positions(self, chain_id, element1_position, element2_position):
        """
        Получает все записи из crm_links по chain_id и позициям элементов.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM crm_links
                WHERE chain_id = %s
                  AND element1_position = %s
                  AND element2_position = %s
                """,
                (chain_id, element1_position, element2_position)
            )
            return cursor.fetchall()


    def get_links_by_chain_and_positions_actual(self, chain_id, element1_position, element2_position):
        print(chain_id, element1_position, element2_position, ' пидор')
        """
        
        Получает все записи из crm_links по chain_id и позициям элементов.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM crm_links
                WHERE chain_id = %s
                  AND element1_position = %s
                  AND element2_position = %s
                  AND actual = TRUE
                """,
                (chain_id, element1_position, element2_position)
            )
            x = cursor.fetchall()
            print(f'сука апдейт {self.get_all_actual_crm_links()}')
            print(x)
            return x[0] if len(x) else None

    def set_link_actual_false_by_id(self, link_id):
        """
        Устанавливает actual = FALSE для записи по id.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE crm_links
                SET actual = FALSE
                WHERE id = %s
                """,
                (link_id,)
            )
            self.connection.commit()
            return cursor.rowcount  # Количество обновлённых строк

    def get_all_channels(self):
        """Получает всех пользователей для указанного bot_id."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM channels",
            )
            return cursor.fetchall()  # Список всех пользователей для бота

    def get_channel_by_id(self, channel_id):
        """Получает одного пользователя (канал) по указанному id."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM channels WHERE id = %s",
                (channel_id,)
            )
            return cursor.fetchone()  # Один канал по id

    def add_link(self, channel_id, title, link, price):
        """
        Добавляет новую запись в таблицу links.
        stats — словарь или None, будет сериализован в JSON.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM links WHERE channel_id = %s AND link = %s",
                (channel_id, link)
            )
            if cursor.fetchone():
                return False  # Такая ссылка уже есть

            cursor.execute(
                "INSERT INTO links (channel_id, title, link, price) VALUES (%s, %s, %s, %s)",
                (channel_id, title, link, price)
            )
            self.connection.commit()
            return True

    def get_links_by_channel(self, channel_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links WHERE channel_id = %s", (channel_id,))
            return cursor.fetchall()

    def get_link_by_id(self, link_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links WHERE id = %s", (link_id,))
            return cursor.fetchone()

    def get_crm_link_by_id(self, link_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links WHERE id = %s", (link_id,))
            return cursor.fetchone()

    def get_all_active_links(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links")
            return cursor.fetchall()


    def delete_link(self, link_id):
        """
        Удаляет ссылку по ID.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM links WHERE id = %s",
                (link_id,)
            )
            self.connection.commit()
            return cursor.rowcount > 0

    def delete_chain(self, chain_id):
        """
        Удаляет ссылку по ID.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM elements WHERE chain_id = %s",
                (chain_id,)
            )
            cursor.execute(
                "DELETE FROM chains WHERE id = %s",
                (chain_id,)
            )
            self.connection.commit()
            return cursor.rowcount > 0

    def get_link_by_partial_link(self, partial_link):
        """
        Получает все записи из таблицы links, у которых поле link содержит заданную подстроку (LIKE %partial_link%).
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            like_pattern = f"%{partial_link}%"
            cursor.execute(
                "SELECT * FROM crm_links WHERE link LIKE %s",
                (like_pattern,)
            )
            x = cursor.fetchall()
            return x[0] if len(x) else None

    def channel_exists(self, channel_id):
        """
        Проверяет, есть ли канал с указанным channel_id в таблице channels.
        Возвращает True, если канал найден, иначе False.
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            query = "SELECT * FROM channels WHERE channel_id = %s"
            cursor.execute(query, (channel_id,))
            result = cursor.fetchall()
            return bool(len(result))


    def update_link_value(self, link_id, field_name, new_value):
        """
        Обновляет поле field_name у записи с id = link_id в таблице links значением new_value.
        """
        self.ensure_connection()

        with self.connection.cursor() as cursor:
            query = f"UPDATE links SET {field_name} = %s WHERE id = %s"
            cursor.execute(query, (new_value, link_id))
            self.connection.commit()

    def get_config_value(self, key):
        """Получает значение по ключу из таблицы configuration."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT value FROM configuration WHERE `key` = %s", (key,))
            result = cursor.fetchone()
            return result['value'] if result else None

    def set_config_value(self, key, value):
        """Устанавливает значение по ключу в таблице configuration."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO configuration (`key`, value) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE value = %s
            """, (key, value, value))
            self.connection.commit()

    def add_element(self, channel_id, channel_name, bot_token, bot_username, bot_id, chain_id, main=False, last_change_requests=0):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM elements WHERE chain_id = %s', (chain_id,))
            if not main:
                elements_ = cursor.fetchall()
                elements_.sort(key=lambda x: x['queue'])
                new_queue_id = elements_[-1]['queue']+1
            else:
                elements_ = ['']
                new_queue_id = 1
            cursor.execute(
                "INSERT INTO elements (main, channel_id, channel_name, bot_token, bot_username, bot_id, queue, chain_id, auto, last_change_requests) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (main, channel_id, channel_name, bot_token, bot_username, bot_id, new_queue_id, chain_id, 1,
                 last_change_requests)
            )
            self.connection.commit()
            cursor.execute('SELECT * FROM elements WHERE chain_id = %s', (chain_id,))
            return [elements_[-1], cursor.fetchall()[-1]]


    def get_element_by_queue(self, element_queue_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM elements WHERE queue = %s', (element_queue_id,))
            return cursor.fetchall()[0]

    def get_next_crm_link(self, element_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM crm_links WHERE element1_id = %s AND actual = TRUE",
                (element_id,)
            )
            return cursor.fetchone()

    def get_all_actual_crm_links(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM crm_links WHERE actual = TRUE"
            )
            return cursor.fetchall()

    def get_all_actual_crm_links_by_chain_id(self, chain_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM crm_links WHERE actual = TRUE AND chain_id=%s", (chain_id,)
            )
            return cursor.fetchall()

    def add_chain(self, name):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "INSERT INTO chains (name) VALUES (%s)",
                (name,)
            )
            self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM chains')
            last_chain = cursor.fetchone()
            return last_chain['id']

    def add_pull(self, name):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "INSERT INTO pulls (name) VALUES (%s)",
                (name,)
            )
            self.connection.commit()

    def add_crm_link(self, name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet, actual, previous_pair=0):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "INSERT INTO crm_links (name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet_requests, actual, previuos_pair) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                   (name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet, actual, previous_pair)
            )
            self.connection.commit()



    def add_privet(self, text, keyboard, pull_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO privets (text, keyboard, pull_id) VALUES (%s, %s, %s)",
                (text, keyboard, pull_id)
            )
            self.connection.commit()



    def get_pulls(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM pulls"
            )
            return cursor.fetchall()

    def get_crm_link_by_name(self, name):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM crm_links WHERE name = %s", (name,))
            r = cursor.fetchone()
            if r:
                print(f'cyka {r}')
                return r
            return None

    def get_pull(self, pull_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM pulls WHERE `id` = %s", (pull_id,)
            )
            return cursor.fetchall()[0]

    def get_chain(self, chain_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM chains WHERE `id` = %s", (chain_id,)
            )
            return cursor.fetchall()[0]

    def update_chain_pull_id(self, chain_id, new_pull_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "UPDATE `chains` SET `pull_id` = %s WHERE `id` = %s", (new_pull_id, chain_id)
            )
            self.connection.commit()

    def update_crm_link_requests(self, link_id, requests):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "UPDATE `crm_links` SET `requests` = %s WHERE `id` = %s", (requests, link_id)
            )
            self.connection.commit()

    def update_element_last_change_requests(self, element_id, new_last_change_requests):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "UPDATE `elements` SET `last_change_requests` = %s WHERE `id` = %s", (new_last_change_requests, element_id)
            )
            self.connection.commit()

    def get_privets(self, pull_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM privets WHERE `pull_id` = %s", (pull_id,)
            )
            return cursor.fetchall()

    def get_privet_by_id(self, privet_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM privets WHERE id = %s", (privet_id,)
            )
            return cursor.fetchone()

    def get_privet_by_id_and_pull(self, privet_id, pull_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM privets WHERE id = %s AND pull_id = %s", (privet_id, pull_id)
            )
            return cursor.fetchone()

    def get_elements(self, chain_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM elements WHERE `chain_id` = %s", (chain_id,)
            )
            return cursor.fetchall()

    def get_element_by_channel_id(self, channel_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM elements WHERE `channel_id` = %s", (channel_id,)
            )
            return cursor.fetchall()[0]

    def get_link_by_element_ids(self, element1_id, element2_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM links WHERE `element1_id` = %s AND `element2_id` = %s",
                (element1_id, element2_id)
            )
            results = cursor.fetchall()
            if len(results):
                return results[0]
            else:
                return None

    def get_elements_all(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM elements"
            )
            return cursor.fetchall()

    def get_element(self, element_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM elements WHERE `id` = %s", (element_id,)
            )
            return cursor.fetchall()[0]

    def get_element_by_id_and_position(self, element_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM elements WHERE `id` = %s", (element_id,)
            )
            return cursor.fetchall()[0]


    def get_all_chains(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM chains")

            return cursor.fetchall()

    def get_conversion_for_privet(self, chain_id, element1_position, element2_position, privet_id, requests=0):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            # Ищем текущую строку
            cursor.execute("""
                SELECT id, requests, previuos_pair
                FROM crm_links
                WHERE chain_id = %s AND element1_position = %s AND element2_position = %s AND privet_id = %s
                LIMIT 1
            """, (chain_id, element1_position, element2_position, privet_id))
            current = cursor.fetchone()

            if not current:
                return {"error": "Не найдена строка с заданными параметрами"}

            link_id = current["id"]
            current_requests = current["requests"]

            if requests == 0:
                # Берём previuos_pair и смотрим его requests
                previous_id = current["previuos_pair"]
                if not previous_id:
                    return {
                        "link_id": link_id,
                        "conversion": None,
                        "note": "Нет previuos_pair — невозможно посчитать конверсию"
                    }

                cursor.execute("SELECT requests FROM crm_links WHERE id = %s", (previous_id,))
                previous = cursor.fetchone()
                if not previous:
                    return {"error": f"Строка с id={previous_id} не найдена"}

                prev_requests = previous['requests']
                conversion = round((current_requests / prev_requests) * 100, 2) if prev_requests else 0

                return {
                    "link_id": link_id,
                    "current_requests": current_requests,
                    "previous_requests": prev_requests,
                    "conversion": conversion,
                    "mode": "использовали previuos_pair"
                }

            else:
                # requests передан → считаем его как предыдущий
                prev_requests = requests
                conversion = round((current_requests / prev_requests) * 100, 2) if prev_requests else 0

                return {
                    "link_id": link_id,
                    "current_requests": current_requests,
                    "previous_requests": prev_requests,
                    "conversion": conversion,
                    "mode": "использовали requests как предыдущее"
                }

    def get_active_privet_ids(self, chain_id):
        """Получает ID всех активных приветок для указанной цепочки."""
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT privet_id FROM crm_links WHERE actual = TRUE AND chain_id = %s",
                (chain_id,)
            )
            return {row['privet_id'] for row in cursor.fetchall()}

    def get_crm_link_by_privet_and_positions(self, chain_id, element1_position, element2_position, privet_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM crm_links
                WHERE chain_id = %s AND element1_position = %s AND element2_position = %s AND privet_id = %s
                LIMIT 1
                """,
                (chain_id, element1_position, element2_position, privet_id)
            )
            return cursor.fetchone()

