import snearl.database as db

con = db.con
cur = db.cur

#####################
# Таблица Voicelist #
#####################

# Создание таблицы
##################

def voicelist_create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS Voicelist (
    chat_id TEXT,
    file_id TEXT,
    file_author TEXT,
    file_desc TEXT,
    file_blob BLOB,
    type TEXT
    )""")
    return

# Добавление записи
###################

def voicelist_add(chat_id, file_id, file_author, file_desc, file_blob):
    cur.execute("INSERT INTO Voicelist VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, file_id, file_author, file_desc, file_blob, "voice"))
    return

# Удаление записи
#################

def voicelist_delete(file_id):
    cur.execute("DELETE FROM Voicelist WHERE file_id=?", (file_id, ))
    return

# Функции-геттеры
#################

def voicelist_get(file_id):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Voicelist WHERE file_id=?",
                      (file_id, ))
    if r:= res.fetchone():
        return r[0]
    return None

def voicelist_get_blob(file_id):
    res = cur.execute("SELECT file_blob "\
                      "FROM Voicelist WHERE file_id=?",
                      (file_id, ))
    if r:= res.fetchone():
        return r[0]
    return None

def voicelist_get_all():
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Voicelist")
    return res.fetchall()

def voicelist_by_chat(chat_id):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Voicelist WHERE chat_id=?",
                      (chat_id, ))
    return res.fetchall()

def voicelist_by_author(chat_id, file_author):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Voicelist WHERE chat_id=? AND file_author=?",
                      (chat_id, file_author))
    return res.fetchall()

# Список авторов
################

def voicelist_authors_list(chat_id):
    res = cur.execute("SELECT DISTINCT file_author "\
                      "FROM Voicelist WHERE chat_id=?",
                      (chat_id, ))
    return [a[0] for a in res.fetchall()]


# Функция миграции данных в новый чат
#####################################

def voicelist_migration(old_chat, new_chat):
    res = cur.execute("UPDATE Voicelist "\
                      "SET chat_id=?"\
                      "WHERE chat_id=?",
                      (new_chat, old_chat))
    return

# Функция удаления все данных для чата
######################################

def voicelist_clear_by_chat(chat_id):
    cur.execute("DELETE FROM Voicelist WHERE chat_id=?", (chat_id,))
    return
