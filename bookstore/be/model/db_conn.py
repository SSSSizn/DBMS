from be.model import store
import mysql.connector

class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    def get_db_conn(self):
        # 建立数据库连接
        return mysql.connector.connect(
            host="localhost",  # 本地数据库
            user="root",  # MySQL 用户名
            password="Gyx20040927",  # MySQL 密码
            database="bookstore",  # 数据库名称
            charset="utf8mb4"  # 设置字符集为 utf8mb4
        )

    def user_id_exist(self, user_id):
        # 获取游标对象
        cursor = self.conn.cursor()

        try:
            # 使用游标对象执行 SQL 查询
            cursor.execute("SELECT user_id FROM user WHERE user_id = %s;", (user_id,))

            # 获取查询结果
            row = cursor.fetchone()

            # 判断查询结果是否为空
            if row is None:
                return False  # 用户不存在
            else:
                return True  # 用户存在
        except mysql.connector.Error as e:
            print(f"MySQL error: {str(e)}")
            return False  # 如果有 MySQL 错误，则返回 False
        finally:
            # 确保关闭游标
            cursor.close()

    def book_id_exist(self, store_id, book_id):
        # 获取游标对象
        cursor = self.conn.cursor()

        try:
            # 使用游标对象执行 SQL 查询
            cursor.execute(
                "SELECT book_id FROM store WHERE store_id = %s AND book_id = %s;",
                (store_id, book_id)
            )

            # 获取查询结果
            row = cursor.fetchone()

            # 判断查询结果是否为空
            if row is None:
                return False  # 如果没有找到匹配的记录，返回 False
            else:
                return True  # 如果找到匹配的记录，返回 True
        except mysql.connector.Error as e:
            print(f"MySQL error: {str(e)}")
            return False  # 如果有 MySQL 错误，则返回 False
        finally:
            # 确保关闭游标
            cursor.close()

    def store_id_exist(self, store_id):
        # 获取游标对象
        cursor = self.conn.cursor()

        try:
            # 使用游标对象执行 SQL 查询
            cursor.execute("SELECT store_id FROM user_store WHERE store_id = %s;", (store_id,))

            # 获取查询结果
            row = cursor.fetchone()

            # 判断查询结果是否为空
            if row is None:
                return False  # 存储不存在
            else:
                return True  # 存储存在
        except mysql.connector.Error as e:
            print(f"MySQL error: {str(e)}")
            return False  # 如果有 MySQL 错误，则返回 False
        finally:
            # 确保关闭游标
            cursor.close()

