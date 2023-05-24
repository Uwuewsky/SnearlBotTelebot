"""
База данных списка пользователей.
"""

import snearl.database as db

cur = db.cur
con = db.con

#####################
# Таблица Userlist  #
#####################

def create_table():
    """Создание таблицы"""
    cur.execute("""CREATE TABLE IF NOT EXISTS Userlist (
    id INTEGER PRIMARY KEY,
    user_name TEXT,
    user_title TEXT,
    user_nick TEXT DEFAULT NULL,
    avatar BLOB DEFAULT NULL
    )""")

def get(user_name, user_title):
    """Возвращает ID записи, создает запись если нужно."""
    if res := find(user_name, user_title):
        result = res[0]
    else:
        add(user_name, user_title)
        con.commit()
        result = find_id(user_name, user_title)
    return result

def add(user_name, user_title):
    """Добавление записи."""
    cur.execute("INSERT INTO Userlist (user_name, user_title) "\
                "VALUES (?, ?)",
                (user_name, user_title))

def add_with_id(user_id, user_name, user_title):
    """Добавление записи с ID."""
    cur.execute("INSERT INTO Userlist (id, user_name, user_title) "\
                "VALUES (?, ?, ?)",
                (user_id, user_name, user_title))

def delete(user_id):
    """Удаление записи"""
    cur.execute("DELETE FROM Userlist WHERE id=?", (user_id,))

def update(user_name, user_title):
    """Обновление записи"""
    if not (user_name and user_title):
        return

    cur.execute("UPDATE Userlist "\
                "SET user_title=? "\
                "WHERE user_name=?",
                (user_title, user_name))

def find(user_name, user_title):
    """Имеется ли запись в БД. Возвращает запись целиком."""
    res = cur.execute("SELECT id, user_name, user_title FROM Userlist "\
                      "WHERE user_name=? OR user_title=?",
                      (user_name, user_title))
    result = res.fetchone()

    return result

def find_id(user_name, user_title):
    """Имеется ли запись в БД. Возвращает только id."""
    res = find(user_name, user_title)
    if res:
        return res[0]
    return res

def get_avatar(user_id):
    """Возвращает аватарку."""
    res = cur.execute("SELECT avatar FROM Userlist "\
                      "WHERE id=?",
                      (user_id, ))
    if result := res.fetchone():
        return result[0]
    return None

def set_avatar(user_id, blob):
    """Устанавливает аватарку пользователю."""
    res = cur.execute("UPDATE Userlist "\
                      "SET avatar=?"
                      "WHERE id=?",
                      (blob, user_id))

def get_nick(user_id):
    """Возвращает никнейм."""
    res = cur.execute("SELECT user_nick FROM Userlist "\
                      "WHERE id=?",
                      (user_id, ))
    if result := res.fetchone():
        return result[0]
    return None

def set_nick(user_id, user_nick):
    """Устанавливает никнейм пользователю."""
    res = cur.execute("UPDATE Userlist "\
                      "SET user_nick=?"
                      "WHERE id=?",
                      (user_nick, user_id))

def get_all():
    """Все записи таблицы"""
    res = cur.execute("SELECT id, user_name, user_title FROM Userlist")
    return res.fetchall()

def get_table():
    """Вся таблица целиком"""
    res = cur.execute("SELECT * FROM Userlist")
    return res.fetchall()

create_table()
