#coding: utf-8

import mysql.connector
from mysql.connector import Error, errorcode
from typing import Optional, List

class MySQLReader:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self) -> bool:
        """Устанавливает соединение с БД"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Подключение к базе данных успешно")
                return True
        except Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Ошибка авторизации при подключении к MySQL")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("База данных не существует")
            else:
                print(f"Ошибка подключения к MySQL: {err}")
            return False

    def ensure_connection(self) -> bool:
        """Проверяет и при необходимости восстанавливает соединение"""
        if self.connection is None or not self.connection.is_connected():
            print("Соединение отсутствует. Устанавливаю новое...")
            return self.connect()
        return True

    def execute_query(self, query: str) -> Optional[List]:
        """Выполняет SELECT-запрос и возвращает результат"""
        if not self.ensure_connection():
            print("Не удалось установить соединение для выполнения запроса")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return [row[0] for row in result]
        except Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None

    def get_distinct_post_ids_by_sku(self) -> Optional[List]:
        """Выполняет нужный SELECT-запрос"""
        query = "SELECT DISTINCT `post_id` FROM `z1_postmeta` WHERE `meta_key` = '_sku';"
        result = self.execute_query(query)

        if result is None:
            return None  # Ошибка при выполнении запроса
        return result or False  # Возвращаем False, если список пуст

    def close(self):
        """Закрывает соединение с БД"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Соединение с базой данных закрыто")

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматически закрывает соединение после выхода из with"""
        self.close()