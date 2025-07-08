import pymysql
import logging
import asyncio
import  json

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
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


    def get_link_by_partial_link(self, partial_link, channel_id):
        """
        Получает все записи из таблицы links, у которых поле link содержит заданную подстроку (LIKE %partial_link%).
        """
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            like_pattern = f"%{partial_link}%"
            cursor.execute(
                "SELECT * FROM links WHERE link LIKE %s AND channel_id = %s",
                (like_pattern, channel_id)
            )
            x = cursor.fetchall()
            return x[0] if len(x) else False

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
