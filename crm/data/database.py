import pymysql
import logging
import asyncio
import json
from data.config import *

class Database:
    def __init__(self):
        self.host = MYSQL_host
        self.user = MYSQL_user
        self.password = MYSQL_password
        self.database = MYSQL_database
        self.connection = None

    def ensure_connection(self):
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
        if not params_list:
            return

        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.executemany(query, params_list)
            self.connection.commit()  # ✅ Фиксируем изменения

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_tables(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chains (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name TEXT,
                    pull_id BIGINT
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
                    FOREIGN KEY (chain_id) REFERENCES chains(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
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
                    last_privet BIGINT, 
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

    def add_element(self, channel_id, channel_name, bot_token, bot_username, bot_id, chain_id, main=False):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM elements WHERE chain_id = %s', (chain_id,))
            if not main:
                elements_ = cursor.fetchall()
                elements_.sort(key=lambda x: x['queue'])
                new_queue_id = elements_[-1]['queue']+1
            else:
                new_queue_id = 1
            cursor.execute(
                "INSERT INTO elements (main, channel_id, channel_name, bot_token, bot_username, bot_id, queue, chain_id) VALUES (%s, %s,%s,%s,%s,%s,%s,%s)",
                (main, channel_id, channel_name, bot_token, bot_username, bot_id, new_queue_id, chain_id)
            )
            self.connection.commit()
            cursor.execute('SELECT * FROM elements WHERE chain_id = %s', (chain_id,))
            return [elements_[-1], cursor.fetchall()[-1]]


    def get_element(self, element_queue_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM elements WHERE queue = %s', (element_queue_id,))
            return cursor.fetchall()[0]

    def get_next_link(self, element_id):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM links WHERE element1_id = %s AND actual = TRUE",
                (element_id,)
            )
            return cursor.fetchone()


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

    def add_link(self, name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet, actual):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "INSERT INTO links (name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet, actual) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                   (name, link, element1_id, element2_id, element1_position, element2_position, chain_id, privet_id, requests, last_privet, actual)
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

    def get_link_by_name(self, name):
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links WHERE name = %s", (name,))
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

    def update_link_requests(self, link_id, requests):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "UPDATE `links` SET `requests` = %s WHERE `id` = %s", (requests, link_id)
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
            if len(cursor.fetchall()):
                return cursor.fetchall()[0]
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


    def get_all_chains(self):
        self.ensure_connection()
        with self.connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM chains")

            return cursor.fetchall()