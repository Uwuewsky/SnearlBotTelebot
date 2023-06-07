"""
База данных модели authormodel
"""

import snearl.database as db
from snearl.module import userlist_db

class ModelDB:
    def __init__(self, table_type):
        self.table_type = table_type
        self.table = f"{table_type}list".capitalize()
        self.con = db.con
        self.cur = db.cur
        self.create_table()

    def create_table(self):
        """Создание таблицы"""
        userlist_db.create_table()
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.table} (
        chat_id TEXT,
        file_id TEXT,
        user_id INTEGER REFERENCES Userlist(id) ON UPDATE CASCADE ON DELETE CASCADE,
        file_desc TEXT,
        file_blob BLOB,
        type TEXT
        )""")

    def add(self, chat_id, file_id, user_name, user_title, file_desc, file_blob):
        """Добавление записи"""
        user_id = userlist_db.get(user_name, user_title)
        self.cur.execute(f"INSERT INTO {self.table} VALUES (?, ?, ?, ?, ?, ?)",
                         (chat_id, file_id,
                          user_id, file_desc,
                          file_blob, self.table_type))

    def delete(self, file_id):
        """Удаление записи по file_id"""
        self.cur.execute(f"DELETE FROM {self.table} WHERE file_id=?",
                         (file_id, ))

    # Функции-геттеры
    #################

    #
    # Данные функции не возвращают всю запись целиком
    # по умолчанию опущены file_blob и user_name
    # file_blob не грузится из-за занимаемой памяти
    # user_name используется только для проверки пользователя
    #

    def get(self, file_id):
        """Вернуть всю запиcь по file_id"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "user_title, file_desc "\
                               f"FROM {self.table} "\
                               "JOIN Userlist "\
                               f"ON Userlist.id = {self.table}.user_id "\
                               "WHERE file_id=?",
                               (file_id, ))
        if result := res.fetchone():
            return result
        return None

    def get_blob(self, file_id):
        """Вернуть файл по его file_id"""
        res = self.cur.execute("SELECT file_blob "\
                               f"FROM {self.table} WHERE file_id=?",
                               (file_id, ))
        if result := res.fetchone():
            return result[0]
        return None

    def get_all(self):
        """Список всех записей в таблице"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "user_name, user_title, file_desc "\
                               f"FROM {self.table} "\
                               "JOIN Userlist "\
                               f"ON Userlist.id = {self.table}.user_id "\
                               "ORDER BY user_title, file_desc")
        return res.fetchall()

    def by_chat(self,chat_id):
        """Список записей чата"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "user_title, file_desc "\
                               f"FROM {self.table} "\
                               "JOIN Userlist "\
                               f"ON Userlist.id = {self.table}.user_id "\
                               "WHERE chat_id=? "\
                               "ORDER BY user_title, file_desc",
                               (chat_id, ))
        return res.fetchall()

    def by_author(self, chat_id, user_title):
        """Список записей по автору"""
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "user_title, user_nick, file_desc "\
                               f"FROM {self.table} "\
                               "JOIN Userlist "\
                               f"ON Userlist.id = {self.table}.user_id "\
                               "WHERE (chat_id=:chat_id AND user_title=:query) "\
                               "OR (chat_id=:chat_id AND user_nick=:query) "\
                               "ORDER BY file_desc",
                               {
                                   "chat_id": chat_id,
                                   "query": user_title
                               })
        return res.fetchall()

    def authors_names_list(self, chat_id):
        """Список авторов"""
        al = self.authors_list(chat_id)
        return [a[2] or a[1] for a in al]

    def authors_list(self, chat_id):
        """Список авторов"""
        res = self.cur.execute("SELECT DISTINCT user_name, user_title, user_nick "\
                               "FROM Userlist "\
                               f"JOIN {self.table} "\
                               f"ON Userlist.id = {self.table}.user_id "\
                               "WHERE chat_id=? "\
                               "ORDER BY user_title",
                               (chat_id, ))
        return [(*a,) for a in res.fetchall()]

    def search(self, query, offset, limit):
        """Функция поиска по тексту"""
        query = f"%{query}%".lower()
        res = self.cur.execute("SELECT chat_id, file_id, "\
                               "user_title, user_nick, file_desc, type "\

                               f"FROM {self.table} "\
                               "JOIN Userlist "\
                               f"ON Userlist.id = {self.table}.user_id "\

                               "WHERE LOWER(user_title) LIKE :query "\
                               "OR LOWER(user_nick) LIKE :query "\
                               "OR LOWER(file_desc) LIKE :query "\

                               "ORDER BY user_nick, user_title, file_desc "\
                               "LIMIT :limit "\
                               "OFFSET :offset",
                               {
                                   "query": query,
                                   "limit": limit,
                                   "offset": offset
                               })
        return res.fetchall()

    def get_random_file(self, chat_id):
        """Выбирает случайный файл из бд"""
        res = self.cur.execute("SELECT file_blob "\
                                f"FROM {self.table} WHERE chat_id=? "\
                                "ORDER BY RANDOM() LIMIT 1",
                                (chat_id, ))
        if result := res.fetchone():
            return result[0]
        return None

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
