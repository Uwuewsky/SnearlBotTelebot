"""
База данных черного списка
"""

import snearl.database as db
from snearl.module import userlist_db

cur = db.cur
con = db.con

#####################
# Таблица Blacklist #
#####################

def create_table():
    """Создание таблицы"""
    userlist_db.create_table()
    cur.execute("""CREATE TABLE IF NOT EXISTS Blacklist (
    chat_id TEXT,
    user_id INTEGER REFERENCES Userlist(id) ON UPDATE CASCADE ON DELETE CASCADE
    )""")

def add(chat_id, user_name, user_title):
    """Добавление записи"""
    user_id = userlist_db.get(user_name, user_title)
    cur.execute("INSERT INTO Blacklist VALUES (?, ?)",
                (chat_id, user_id))

def delete(chat_id, user_name, user_title):
    """Удаление записи"""
    user_id = userlist_db.find_id(user_name, user_title)
    cur.execute("DELETE FROM Blacklist "\
                "WHERE chat_id=? AND user_id=?",
                (chat_id, user_id))

def has(chat_id, user_name, user_title):
    """Имеется ли запись в БД по @имени"""
    user_id = userlist_db.find_id(user_name, user_title)
    res = cur.execute("SELECT * FROM Blacklist "\
                      "WHERE chat_id=? AND user_id=?",
                      (chat_id, user_id))
    return res.fetchone()

def get_all():
    """Все записи таблицы"""
    res = cur.execute("SELECT chat_id, user_name, user_title FROM Blacklist "\
                      "JOIN Userlist "\
                      "ON Userlist.id = Blacklist.user_id "\
                      "ORDER BY user_title")
    return res.fetchall()

def by_chat(chat_id):
    """Все записи чата"""
    res = cur.execute("SELECT user_name, user_title FROM Blacklist "\
                      "JOIN Userlist "\
                      "ON Userlist.id = Blacklist.user_id "\
                      "WHERE chat_id=? "\
                      "ORDER BY user_title",
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

create_table()
