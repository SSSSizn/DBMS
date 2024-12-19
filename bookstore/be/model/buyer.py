import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import mysql.connector

class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(
            self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        try:
            # 验证用户和商店是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成唯一的订单 ID
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            # 开始处理每个书籍及数量
            for book_id, count in id_and_count:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT book_id, stock_level, book_info FROM store "
                    "WHERE store_id = %s AND book_id = %s;",
                    (store_id, book_id)
                )
                row = cursor.fetchone()
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row[1]
                book_info = row[2]
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                # 检查库存是否足够
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 更新库存
                cursor.execute(
                    "UPDATE store SET stock_level = stock_level - %s "
                    "WHERE store_id = %s AND book_id = %s AND stock_level >= %s;",
                    (count, store_id, book_id, count)
                )
                if cursor.rowcount == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 插入订单详情
                cursor.execute(
                    "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                    "VALUES(%s, %s, %s, %s);",
                    (uid, book_id, count, price)
                )

            # 插入新订单记录
            cursor.execute(
                "INSERT INTO new_order(order_id, store_id, user_id) "
                "VALUES(%s, %s, %s);",
                (uid, store_id, user_id)
            )

            # 提交事务
            self.conn.commit()
            order_id = uid
        except mysql.connector.Error as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = self.conn
        try:
            cursor = conn.cursor()

            # 获取订单信息
            cursor.execute(
                "SELECT order_id, user_id, store_id FROM new_order WHERE order_id = %s",
                (order_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row[0]
            buyer_id = row[1]
            store_id = row[2]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            # 验证买家账户和密码
            cursor.execute(
                "SELECT balance, password FROM user WHERE user_id = %s;", (buyer_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]
            if password != row[1]:
                return error.error_authorization_fail()

            # 验证卖家是否存在
            cursor.execute(
                "SELECT store_id, user_id FROM user_store WHERE store_id = %s;", (store_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[1]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            # 计算订单的总金额
            cursor.execute(
                "SELECT book_id, count, price FROM new_order_detail WHERE order_id = %s;",
                (order_id,)
            )
            total_price = 0
            for row in cursor:
                count = row[1]
                price = row[2]
                total_price += price * count

            # 检查余额是否足够
            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家的余额
            cursor.execute(
                "UPDATE user SET balance = balance - %s WHERE user_id = %s AND balance >= %s",
                (total_price, buyer_id, total_price)
            )
            if cursor.rowcount == 0:
                return error.error_not_sufficient_funds(order_id)

            # 给卖家账户充值
            cursor.execute(
                "UPDATE user SET balance = balance + %s WHERE user_id = %s",
                (total_price, seller_id)
            )
            if cursor.rowcount == 0:
                return error.error_non_exist_user_id(seller_id)

            # 删除订单及订单详情
            cursor.execute("DELETE FROM new_order WHERE order_id = %s", (order_id,))
            if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)

            cursor.execute("DELETE FROM new_order_detail WHERE order_id = %s", (order_id,))
            if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)

            # 提交事务
            conn.commit()

        except mysql.connector.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        finally:
            cursor.close()

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            cursor = self.conn.cursor()

            # 验证用户ID和密码
            cursor.execute(
                "SELECT password FROM user WHERE user_id = %s", (user_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return error.error_authorization_fail()

            if row[0] != password:
                return error.error_authorization_fail()

            # 更新用户余额
            cursor.execute(
                "UPDATE user SET balance = balance + %s WHERE user_id = %s",
                (add_value, user_id)
            )

            # 检查是否成功更新
            if cursor.rowcount == 0:
                return error.error_non_exist_user_id(user_id)

            # 提交事务
            self.conn.commit()

        except mysql.connector.Error as e:
            # 捕获MySQL错误
            return 528, "{}".format(str(e))
        except BaseException as e:
            # 捕获其他异常
            return 530, "{}".format(str(e))
        finally:
            # 确保关闭游标
            cursor.close()

        return 200, "ok"

