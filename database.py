import sqlite3
from typing import List

def create_connection():
    conn = sqlite3.connect('shopping_list.db')
    return conn

def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    # Таблица для покупок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping (
            user_id INTEGER,
            item TEXT,
            category TEXT
        )
    ''')
    # Таблица для напоминаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            user_id INTEGER,
            item TEXT,
            remind_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_item(user_id: int, item: str, category: str = "Без категории"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO shopping (user_id, item, category) VALUES (?, ?, ?)', (user_id, item, category))
    conn.commit()
    conn.close()

def remove_item(user_id: int, item: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM shopping WHERE user_id = ? AND item = ?', (user_id, item))
    conn.commit()
    conn.close()

def get_items(user_id: int) -> List[str]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT item FROM shopping WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return [item[0] for item in items]

def get_items_grouped(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT item, category FROM shopping WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    grouped = {}
    for item, category in items:
        if category in grouped:
            grouped[category].append(item)
        else:
            grouped[category] = [item]
    return grouped

def clear_items(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM shopping WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_reminder(user_id: int, item: str, remind_at: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reminders (user_id, item, remind_at) VALUES (?, ?, ?)', (user_id, item, remind_at))
    conn.commit()
    conn.close()

def get_due_reminders(current_time: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, item FROM reminders WHERE remind_at <= ?', (current_time,))
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def remove_reminder(user_id: int, item: str, remind_at: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE user_id = ? AND item = ? AND remind_at = ?', (user_id, item, remind_at))
    conn.commit()
    conn.close()
