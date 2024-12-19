import mysql.connector

def check_user_table_exists():
    try:
        # 连接到数据库
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Gyx20040927',
            database='bookstore'
        )
        cursor = conn.cursor()

        # 查询 user 表是否存在
        cursor.execute("SHOW TABLES LIKE 'user'")
        result = cursor.fetchone()

        if result:
            print("Table 'user' exists")
            return True
        else:
            print("Table 'user' does not exist")
            return False
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

check_user_table_exists()
