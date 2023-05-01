import snearl.database as db

con = db.con
cur = db.cur

#####################
# Таблица Quotelist #
#####################

# Создание таблицы
##################

def quotelist_create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS Quotelist (
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

def quotelist_add(chat_id, file_id, file_author, file_desc, file_blob):
    cur.execute("INSERT INTO Quotelist VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, file_id, file_author, file_desc, file_blob, "quote"))
    return

# Удаление записи
#################

def quotelist_delete(file_id):
    cur.execute("DELETE FROM Quotelist WHERE file_id=?", (file_id, ))
    return

# Функции-геттеры
#################

def quotelist_get(file_id):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Quotelist WHERE file_id=?",
                      (file_id, ))
    if r:= res.fetchone():
        return r[0]
    return None

def quotelist_get_blob(file_id):
    res = cur.execute("SELECT file_blob "\
                      "FROM Quotelist WHERE file_id=?",
                      (file_id, ))
    if r:= res.fetchone():
        return r[0]
    return None

def quotelist_get_all():
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Quotelist")
    return res.fetchall()

def quotelist_by_chat(chat_id):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Quotelist WHERE chat_id=?",
                      (chat_id, ))
    return res.fetchall()

def quotelist_by_author(chat_id, file_author):
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Quotelist WHERE chat_id=? AND file_author=?",
                      (chat_id, file_author))
    return res.fetchall()

# Список авторов
################

def quotelist_authors_list(chat_id):
    res = cur.execute("SELECT DISTINCT file_author "\
                      "FROM Quotelist WHERE chat_id=?",
                      (chat_id, ))
    return [a[0] for a in res.fetchall()]

# Функция поиска по запросу
###########################

def quotelist_search(query, offset, limit):
    query = f"%{query}%".lower()
    res = cur.execute("SELECT chat_id, file_id, file_author, file_desc "\
                      "FROM Quotelist "\
                      "WHERE LOWER(file_author) LIKE ? "\
                      "OR LOWER(file_desc) LIKE ? "\
                      "ORDER BY file_author "\
                      "LIMIT ? "\
                      "OFFSET ?",
                      (query, query, limit, offset))
    return res.fetchall()

# Функция миграции данных в новый чат
#####################################

def quotelist_migration(old_chat, new_chat):
    res = cur.execute("UPDATE Quotelist "\
                      "SET chat_id=?"\
                      "WHERE chat_id=?",
                      (new_chat, old_chat))
    return

# Функция удаления все данных для чата
######################################

def quotelist_clear_by_chat(chat_id):
    cur.execute("DELETE FROM Quotelist WHERE chat_id=?", (chat_id,))
    return
