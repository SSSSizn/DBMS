import jwt
import time
import logging
import sqlite3 as sqlite
import mysql.connector


from be.model import error
from be.model import db_conn

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    # return encoded.decode("utf-8")
    return encoded


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def register(self, user_id: str, password: str):
        try:
            # Step 1: 检查 user_id 是否已经存在
            cursor = self.conn.cursor()
            print("test id", user_id)

            # 查询当前用户是否存在
            cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (user_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                # 如果用户已经存在，返回错误信息并结束函数
                cursor.close()
                print(f"User {user_id} already exists.")
                return 512, {"message": f"User ID {user_id} already exists"}  # 返回错误代码 512，表示用户已存在

            # Step 2: 如果用户不存在，进行注册
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            # 插入新用户
            cursor.execute(
                "INSERT INTO user (user_id, password, balance, token, terminal) "
                "VALUES (%s, %s, %s, %s, %s);",
                (user_id, password, 0, token, terminal),
            )

            # 检查插入操作是否成功
            if cursor.rowcount == 1:
                print(f"User {user_id} successfully registered.")
            else:
                print(f"Failed to register user {user_id}.")

            self.conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            # MySQL 错误
            print(f"MySQL error: {e}")
            return 500, {"message": "Internal server error"}
        except Exception as e:
            # 其他异常
            print(f"Unexpected error: {e}")
            return 400, {"message": "Unexpected error"}

        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            # Check the password first
            code, message = self.check_password(user_id, password)
            if code != 200:
                print(f"Password check failed: {message}")
                return code, message

            # Log to check if the user exists before deleting
            print(f"Attempting to unregister user_id: {user_id}")

            # Execute the delete operation
            cursor = self.conn.cursor()

            # 使用明确的参数化查询，确保传递的是正确的参数类型
            cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))

            # 检查是否删除了行
            if cursor.rowcount == 0:
                # If no rows were deleted, it means the user doesn't exist
                print(f"No user found with user_id: {user_id}")
                cursor.close()
                return error.error_authorization_fail()  # Return authorization failure if user doesn't exist

            # 提交事务并关闭游标
            self.conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            # If there is a MySQL error, return the error code and message
            if cursor:
                cursor.close()
            print(f"MySQL Error: {str(e)}")
            return 528, f"MySQL error: {str(e)}"
        except BaseException as e:
            # Catch any other exception and return a generic error
            if cursor:
                cursor.close()
            print(f"Unexpected Error: {str(e)}")
            return 530, f"Unexpected error: {str(e)}"

        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        try:
            cursor = self.conn.cursor()

            # 查询 user_id 是否存在
            cursor.execute("SELECT password FROM user WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            # 如果用户不存在
            if row is None:
                cursor.close()
                return error.error_authorization_fail()

            # 如果用户存在，比较密码
            if password != row[0]:
                cursor.close()
                return error.error_authorization_fail()

            # 密码正确
            cursor.close()
            return 200, "ok"

        except mysql.connector.Error as e:
            # 记录数据库错误信息，便于排查问题
            cursor.close()
            return 528, f"MySQL error: {str(e)}"

        except BaseException as e:
            # 记录其他异常信息，确保捕获所有错误
            cursor.close()
            return 530, f"Unexpected error: {str(e)}"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            # Step 1: 检查 user_id 是否存在，以及密码是否正确
            cursor = self.conn.cursor()
            cursor.execute("SELECT password FROM user WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            if row is None:
                # 用户不存在
                cursor.close()
                return 401, "User ID does not exist", token

            if row[0] != password:
                # 密码不匹配
                cursor.close()
                return 401, "Incorrect password", token

            # Step 2: 密码正确，生成 token
            token = jwt_encode(user_id, terminal)

            # Step 3: 更新数据库中的 token 和 terminal
            cursor.execute(
                "UPDATE user SET token = %s, terminal = %s WHERE user_id = %s",
                (token, terminal, user_id)
            )

            if cursor.rowcount == 0:
                # 如果没有更新到任何行，表示更新失败
                cursor.close()
                return 400, "Failed to update user token", token

            # 提交数据库事务
            self.conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            # 捕获数据库相关错误
            return 528, f"MySQL error: {str(e)}", token

        except BaseException as e:
            # 捕获其他异常
            return 530, f"Unexpected error: {str(e)}", token

        # 如果一切顺利，返回成功代码和 token
        return 200, "Login successful", token

    def logout(self, user_id: str, token: str) -> (int, str):
        try:
            # Step 1: 检查 user_id 是否存在
            cursor = self.conn.cursor()
            cursor.execute("SELECT token FROM user WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            if row is None:
                # 用户不存在
                cursor.close()
                return 401, "User ID does not exist"

            # Step 2: 验证 token 是否正确
            if row[0] != token:
                # Token 不匹配
                cursor.close()
                return 401, "Invalid token"

            # Step 3: 生成一个临时的 dummy_token 和 terminal，表示注销
            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            # Step 4: 更新数据库中的 token 和 terminal 字段
            cursor.execute(
                "UPDATE user SET token = %s, terminal = %s WHERE user_id = %s",
                (dummy_token, terminal, user_id)
            )

            if cursor.rowcount == 0:
                # 如果没有更新任何行，表示没有找到该用户
                cursor.close()
                return 400, "Failed to update user token"

            # 提交数据库事务
            self.conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            # 捕获 MySQL 错误
            return 528, f"MySQL error: {str(e)}"

        except BaseException as e:
            # 捕获其他错误
            return 530, f"Unexpected error: {str(e)}"

        # 注销成功
        return 200, "Logout successful"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> (int, str):
        try:
            # Step 1: 验证旧密码是否正确
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message  # 如果密码验证失败，直接返回相应的错误

            # Step 2: 生成新的 token 和 terminal
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            # Step 3: 更新用户的密码、token 和 terminal
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE user SET password = %s, token = %s, terminal = %s WHERE user_id = %s",
                (new_password, token, terminal, user_id),
            )

            # Step 4: 如果没有更新任何行，表示没有找到该用户，或者用户信息没有更改
            if cursor.rowcount == 0:
                cursor.close()
                return error.error_authorization_fail()  # 用户未找到或未更新

            # 提交数据库事务
            self.conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            # 捕获 MySQL 错误
            return 528, f"MySQL error: {str(e)}"

        except BaseException as e:
            # 捕获其他错误
            return 530, f"Unexpected error: {str(e)}"

        # 密码修改成功
        return 200, "Password changed successfully"

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False



    def __check_token(self, user_id: str, db_token: str, token: str) -> bool:
        # 假设这个方法比较传入的 token 和数据库的 token
        return db_token == token

    def check_token(self, user_id: str, token: str) -> (int, str):
        try:
            # 使用 cursor 显式创建
            cursor = self.conn.cursor()
            cursor.execute("SELECT token FROM user WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                return error.error_authorization_fail()

            db_token = row[0]
            if not self.__check_token(user_id, db_token, token):
                return error.error_authorization_fail()

            return 200, "ok"

        except mysql.connector.Error as e:
            return 528, f"MySQL error: {str(e)}"
        except BaseException as e:
            return 530, f"Unexpected error: {str(e)}"