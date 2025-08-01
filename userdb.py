import sqlite3
import pandas as pd

DB_PATH = "operators.db"
CSV_PATH = "logins.csv"

def init_auth_user_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()

def authorize_user(user_id: int):
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

def is_authorized(user_id: int):
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

def logpasscheck(login: str, password: str):
    try:
        df = pd.read_csv(CSV_PATH)
        row = df[(df['login'] == login) & (df['password'] == password)]
        return not row.empty
    except FileNotFoundError:
        print("logins.csv не найден")
        return False