import snearl.database as db

cur = db.cur
con = db.con

#####################
# Таблица Blacklist #
#####################

# Создание таблицы
###################

def blacklist_create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS Blacklist (
    chat_id TEXT,
    group_id TEXT,
    group_desc TEXT
    )""")
    return

# Добавление записи
###################

def blacklist_add(chat_id, group_id, group_desc):
    cur.execute("INSERT INTO Blacklist VALUES (?, ?, ?)",
                (chat_id, group_id, group_desc))
    return

# Удаление записи
#################

def blacklist_delete(chat_id, group_id):
    cur.execute("DELETE FROM Blacklist WHERE chat_id=? AND group_id=?",
                (chat_id, group_id))
    return

# Функции-геттеры
#################

def blacklist_get(chat_id, group_id):
    res = cur.execute("SELECT * FROM Blacklist WHERE chat_id=? AND group_id=?",
                      (chat_id, group_id))
    if r:= res.fetchone():
        return r[0]
    return None

def blacklist_by_chat(chat_id):
    res = cur.execute("SELECT * FROM Blacklist WHERE chat_id=?", (chat_id, ))
    return res.fetchall()

# Функция миграции данных в новый чат
#####################################

def blacklist_migration(old_chat, new_chat):
    res = cur.execute("UPDATE Blacklist "\
                      "SET chat_id=?"\
                      "WHERE chat_id=?",
                      (new_chat, old_chat))
    return

# Функция удаления все данных для чата
######################################

def blacklist_clear_by_chat(chat_id):
    cur.execute("DELETE FROM Blacklist WHERE chat_id=?", (chat_id,))
    return

