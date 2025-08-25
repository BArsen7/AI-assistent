import sqlite3
import pandas as pd

DB_PATH = "operators.db"
UDB_PATH = "users.db"
CSV_PATH = "logins.csv"

def init_auth_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()
    
    connection = sqlite3.connect(UDB_PATH)
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY,
        FIO TEXT NOT NULL,
        user_group TEXT NOT NULL,           
        username TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT
        )
        ''')
    connection.commit()
    connection.close()

def authorize_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO authorized_users (id) VALUES (?)", (user_id,))

    conn.commit()
    conn.close()

def deauthorize_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM authorized_users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

def is_authorized(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM authorized_users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None

def get_all_authorized_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM authorized_users")
    users = cursor.fetchall()

    conn.close()
    return users

def logpasscheck(login, password):
    try:
        df = pd.read_csv(CSV_PATH)
        row = df[(df['login'] == login) & (df['password'] == password)]
        return not row.empty
    except FileNotFoundError:
        print("logins.csv не найден")
        return False


"""
connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

# Обновляем возраст пользователя "newuser"
cursor.execute('UPDATE Users SET age = ? WHERE username = ?', (29, 'newuser'))

# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()

"""
def find_user(id):
    connection = sqlite3.connect(UDB_PATH)
    cursor = connection.cursor()
    cursor.execute(f"SELECT EXISTS(SELECT 1 FROM Users WHERE id = ?)", (id,))
    responce = cursor.fetchone()[0]
    connection.close()
    return responce

def reg_user(data):
    connection = sqlite3.connect(UDB_PATH)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO Users (id, FIO, user_group, username, first_name, last_name) VALUES (?, ?, ?, ?, ?, ?)", data)
    connection.commit()
    connection.close()
    