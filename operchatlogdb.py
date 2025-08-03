import sqlite3
from authdb import is_authorized

DB_PATH = "operator_dialogs.db"
SEPARATOR = "\n ### \n"

def init_chatlog_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dialogs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            history TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()

def add_message(user_id, operator_id = 0, new_message = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1) есть активный диалог
    cursor.execute("SELECT id, history FROM dialogs WHERE user_id = ? AND operator_id = ?", (user_id, operator_id))
    row = cursor.fetchone()

    separator = SEPARATOR

    # обрезаем историю до 10000 символов, вообще SQLITE может до 1Гб хранить текст
    max_length = 10000

    if row is None: # 2) нет активного диалога, но есть сообщение от пользователя (прикрепляем оператора к диалогу)
        cursor.execute("SELECT id, history FROM dialogs WHERE user_id = ?", (user_id,))
        row1 = cursor.fetchone()

        if row1 is None: # 3) ничего нет
            history = new_message
            cursor.execute("INSERT INTO dialogs (user_id, operator_id, history) VALUES (?, 0, ?)",
                        (user_id, history))
        else: # 2)
            dialog_id, history = row1
            updated_history = history + separator + new_message if history else new_message

            if len(updated_history) > max_length:
                updated_history = updated_history[-max_length:]

            cursor.execute("UPDATE dialogs SET history = ?, operator_id = ? WHERE id = ?", (updated_history, operator_id, dialog_id))
    else: # 1)
        dialog_id, history = row
        updated_history = history + separator + new_message if history else new_message

        if len(updated_history) > max_length:
            updated_history = updated_history[-max_length:]

        cursor.execute("UPDATE dialogs SET history = ? WHERE id = ?", (updated_history, dialog_id))

    conn.commit()
    conn.close()

def get_inbox():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, history FROM dialogs WHERE operator_id = ?", (0,))
    inbox = cursor.fetchall()

    conn.close()
    return inbox

def detach_operator(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE dialogs SET operator_id = ? WHERE user_id = ?", (1, user_id))

    conn.commit()
    conn.close()

def get_history(dude_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if is_authorized(dude_id):
        pattern = f"%{dude_id}%"
        cursor.execute("SELECT user_id, history FROM dialogs WHERE history LIKE ?", (pattern,)) # ищем диалоги где хоть раз упомянался оператор
    else:
        cursor.execute("SELECT operator_id, history FROM dialogs WHERE user_id = ?", (dude_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows

def _get_all_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, operator_id, history FROM dialogs")
    rows = cursor.fetchall()

    conn.close()
    return rows
