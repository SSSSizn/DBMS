import sqlite3 as sqlite

import mysql.connector

from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
            self,
            user_id: str,
            store_id: str,
            book_id: str,
            book_json_str: str,
            stock_level: int,
    ):
        cursor = self.conn.cursor()
        try:
            # 检查用户ID和商店ID是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 插入新书籍信息
            cursor.execute(
                "INSERT INTO store (store_id, book_id, book_info, stock_level) "
                "VALUES (%s, %s, %s, %s)",
                (store_id, book_id, book_json_str, stock_level)
            )

            # 提交事务
            self.conn.commit()

        except mysql.connector.Error as e:
            # 捕获并打印MySQL错误
            return 528, "{}".format(str(e))
        except BaseException as e:
            # 捕获其他异常
            return 530, "{}".format(str(e))
        finally:
            # 确保关闭游标
            cursor.close()

        return 200, "ok"

    def add_stock_level(
            self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        cursor = self.conn.cursor()
        try:
            # 检查用户ID、商店ID和书籍ID是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 更新书籍的库存量
            cursor.execute(
                "UPDATE store SET stock_level = stock_level + %s "
                "WHERE store_id = %s AND book_id = %s",
                (add_stock_level, store_id, book_id)
            )

            # 提交事务
            self.conn.commit()

        except mysql.connector.Error as e:
            # 捕获并打印MySQL错误
            return 528, "{}".format(str(e))
        except BaseException as e:
            # 捕获其他异常
            return 530, "{}".format(str(e))
        finally:
            # 确保关闭游标
            cursor.close()

        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            # Step 1: 检查 user_id 是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)  # 用户不存在，返回相应错误

            # Step 2: 检查 store_id 是否已存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)  # 商店已存在，返回相应错误
            print(f"user_id: {user_id}, store_id: {store_id}")

            # 获取游标对象
            cursor = self.conn.cursor()

            # Step 3: 插入新的商店记录
            cursor.execute(
                "INSERT INTO user_store(store_id, user_id) VALUES (%s, %s)",  # 使用 MySQL 占位符 %s
                (store_id, user_id)
            )

            # 提交事务
            self.conn.commit()

            # 关闭游标
            cursor.close()

            return 200, "Store created successfully"

        except mysql.connector.Error as e:
            print(f"MySQL error: {str(e)}")
            return 528, "{}".format(str(e))


        except BaseException as e:
            return 530, "{}".format(str(e))
