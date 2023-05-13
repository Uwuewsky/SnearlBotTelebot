"""
База данных модели authormodel
"""

import snearl.database as db

class ModelDB:
    def __init__(self, table_type):
        self.table_type = table_type
        self.table = f"{table_type}list".capitalize()
        self.con = db.con
        self.cur = db.cur

    def create_table(self):
        """Создание таблицы"""
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.table} (
        chat_id TEXT,
        file_id TEXT,
        file_author TEXT,
        file_desc TEXT,
        file_blob BLOB,
        type TEXT
        )""")

    def add(self, chat_id, file_id, file_author, file_desc, file_blob):
        """Добавление записи"""
        self.cur.execute(f"INSERT INTO {self.table} VALUES (?, ?, ?, ?, ?, ?)",
                    (chat_id, file_id,
                     file_author, file_desc,
                     file_blob, self.table_type))

    def delete(self, file_id):
        """Удаление записи по file_id"""
        self.cur.execute(f"DELETE FROM {self.table} WHERE file_id=?",
                         (file_id, ))

    # Функции-геттеры
    #################

    def get(self, file_id):
        """Вернуть всю запить по file_id"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "file_author, file_desc "\
                               f"FROM {self.table} WHERE file_id=?",
                               (file_id, ))
        if r:= res.fetchone():
            return r[0]
        return None

    def get_blob(self, file_id):
        """Вернуть файл по его file_id"""
        res = self.cur.execute("SELECT file_blob "\
                               f"FROM {self.table} WHERE file_id=?",
                               (file_id, ))
        if r:= res.fetchone():
            return r[0]
        return None

    def get_all(self):
        """Список всех записей в таблице"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "file_author, file_desc "\
                               f"FROM {self.table} "\
                               "ORDER BY file_author, file_desc")
        return res.fetchall()

    def by_chat(self,chat_id):
        """Список записей чата"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "file_author, file_desc "\
                               f"FROM {self.table} WHERE chat_id=? "\
                               "ORDER BY file_author, file_desc",
                               (chat_id, ))
        return res.fetchall()

    def by_author(self, chat_id, file_author):
        """Список записей по автору"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "file_author, file_desc "\
                               f"FROM {self.table} "\
                               "WHERE chat_id=? AND file_author=? "\
                               "ORDER BY file_desc",
                               (chat_id, file_author))
        return res.fetchall()

    def authors_list(self, chat_id):
        """Список авторов"""
        res = self.cur.execute("SELECT DISTINCT file_author "\
                               f"FROM {self.table} WHERE chat_id=? "\
                               "ORDER BY file_author",
                               (chat_id, ))
        return [a[0] for a in res.fetchall()]

    def search(self, query, offset, limit):
        """Функция поиска по тексту"""
        query = f"%{query}%".lower()
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "file_author, file_desc, type "\

                               f"FROM {self.table} "\
                               "WHERE LOWER(file_author) LIKE :query "\
                               "OR LOWER(file_desc) LIKE :query "\

                               "ORDER BY file_author, file_desc "\
                               "LIMIT :limit "\
                               "OFFSET :offset",
                               {
                                   "query": query,
                                   "limit": limit,
                                   "offset": offset
                               })
        return res.fetchall()

    # Технические функции
    #####################

    def migration(self, old_chat, new_chat):
        """Функция миграции данных в новый чат"""
        self.cur.execute(f"UPDATE {self.table} "\
                         "SET chat_id=?"\
                         "WHERE chat_id=?",
                         (new_chat, old_chat))

    def clear_by_chat(self, chat_id):
        """Функция удаления все данных для чата"""
        self.cur.execute(f"DELETE FROM {self.table} "\
                         "WHERE chat_id=?", (chat_id,))
