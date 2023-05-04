"""
База данных черного списка
"""

import snearl.database as db

cur = db.cur
con = db.con

#####################
# Таблица Blacklist #
#####################

def create_table():
    """Создание таблицы"""
    cur.execute("""CREATE TABLE IF NOT EXISTS Blacklist (
    chat_id TEXT,
    user_name TEXT
    )""")

def add(chat_id, user_name):
    """Добавление записи"""
    cur.execute("INSERT INTO Blacklist VALUES (?, ?)",
                (chat_id, user_name))

def delete(chat_id, user_name):
    """Удаление записи"""
    cur.execute("DELETE FROM Blacklist WHERE chat_id=? AND user_name=?",
                (chat_id, user_name))

def has(chat_id, user_name):
    """Имеется ли запись в БД по @имени"""
    res = cur.execute("SELECT * FROM Blacklist "\
                      "WHERE chat_id=? AND user_name=?",
                      (chat_id, user_name))
    if r := res.fetchone():
        return True
    return False

def get_all():
    """Все записи таблицы"""
    res = cur.execute("SELECT * FROM Blacklist "\
                      "ORDER BY user_name")
    return res.fetchall()

def by_chat(chat_id):
    """Все записи чата"""
    res = cur.execute("SELECT * FROM Blacklist "\
                      "WHERE chat_id=? "\
                      "ORDER BY user_name",
                      (chat_id, ))
    return res.fetchall()

def migration(old_chat, new_chat):
    """Функция миграции данных в новый чат"""
    cur.execute("UPDATE Blacklist "\
                "SET chat_id=?"\
                "WHERE chat_id=?",
                (new_chat, old_chat))

def clear_by_chat(chat_id):
    """Функция удаления все данных для чата"""
    cur.execute("DELETE FROM Blacklist WHERE chat_id=?", (chat_id,))
