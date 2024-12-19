import logging
import os
import sqlite3 as sqlite
import threading
import mysql.connector


class Store:
    database: str

    def __init__(self, db_path):
        self.database = os.path.join(db_path, "be.db")
        self.init_tables()

    def get_db_conn(self):
        # 建立数据库连接
        return mysql.connector.connect(
            host="localhost",  # 本地数据库
            user="root",  # MySQL 用户名
            password="Gyx20040927",  # MySQL 密码
            database="bookstore",  # 数据库名称
            charset="utf8mb4"  # 设置字符集为 utf8mb4
        )

    def init_tables(self):
        try:
            conn = self.get_db_conn()
            cursor = conn.cursor()

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "user_id VARCHAR(255) PRIMARY KEY, password TEXT NOT NULL, "
                "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
            )

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS user_store("
                "user_id VARCHAR(255), store_id VARCHAR(255), PRIMARY KEY(user_id, store_id));"
            )

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS store( "
                "store_id VARCHAR(255), book_id VARCHAR(255), book_info TEXT, stock_level INTEGER,"
                " PRIMARY KEY(store_id, book_id))"
            )

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS new_order( "
                "order_id VARCHAR(255) PRIMARY KEY, user_id TEXT, store_id TEXT)"
            )

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS new_order_detail( "
                "order_id VARCHAR(255), book_id VARCHAR(255), count INTEGER, price INTEGER,  "
                "PRIMARY KEY(order_id, book_id))"
            )

            conn.commit()
        except ConnectionError as e:
            logging.error(e)
            conn.rollback()

    # def get_db_conn(self) -> sqlite.Connection:
    #     return sqlite.connect(self.database)


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()
