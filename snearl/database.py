"""
Модуль базы данных.

Работает как синглтон с помощью:
import snearl.database as db
"""

import sqlite3
from pathlib import Path

##############################
# Общие функции и переменные #
##############################

data_dir = Path("./data")
import_dir = data_dir / "import"
export_dir = data_dir / "export"

con = sqlite3.connect(data_dir / "database.db")
cur = con.cursor()

con.create_function("LOWER", 1, lambda v: v.lower() if v else None) # для поиска
cur.execute("PRAGMA foreign_keys = 1")
con.commit()

def table_clear(table):
    cur.execute(f"DELETE FROM {table}")

####################
# Таблица Settings #
####################

# Содержит вставку неэкранированных
# параметров в текст запроса.
# Функции в этих местах не принимают
# пользовательский ввод, так что всё ок.

def settings_create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS Settings (
    key TEXT,
    value TEXT
    )""")

def settings_get(key):
    res = cur.execute("SELECT value FROM Settings WHERE key=?", (key,))
    if r := res.fetchone():
        return r[0]
    return None

def settings_set(key, value):
    cur.execute(f"DELETE FROM Settings WHERE key='{key}'")
    cur.execute("INSERT INTO Settings VALUES (?, ?)", (key, value))
    con.commit()

def settings_delete(key):
    cur.execute(f"DELETE FROM Settings WHERE key='{key}'")
    con.commit()

settings_create_table()
