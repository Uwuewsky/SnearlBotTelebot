import os, json

############################################
# Классы для хранения и управления данными #
############################################

class Datalist:
    def __init__(self, filename):
        self.data_directory = "data"
        self.filename = filename
        self.read_data()
    
    def write_data(self):
        path = os.path.join(self.data_directory, self.filename)
        with open(path, mode="w", encoding="utf8") as f:
            json.dump(self.data, f, indent="    ", ensure_ascii=False)
        return
    
    def read_data(self):
        path = os.path.join(self.data_directory, self.filename)
        if os.path.isfile(path):
            with open(path, mode="r", encoding="utf8") as f:
                self.data = json.load(f)
        else:
            self.data = {}
        return
    
    def __getitem__(self, key):
        key = str(key)
        if key in self.data.keys():
            return self.data[key]
        return None
    
    def __setitem__(self, key, value):
        self.data[str(key)] = value
        return
    
    def __iter__(self):
        return self.data
    
    def __contains__(self, item):
        return True if self[item] else False

class DatalistChat(Datalist):
    """Тип списка данных для отдельных чатов."""
    
    def add_chat(self, chat_id):
        """Добавляет пустой список для чата, если его нет."""
        if self[chat_id] is None:
            self[chat_id] = {}
        return
    
    def delete_chat(self, chat_id):
        """Удаляет список чата."""
        del self.data[str(chat_id)]
        return
    
    def get_chat_entry(self, chat_id, entry_key):
        """Возвращает запись entry_key в чате chat_id."""
        entry_key = str(entry_key)
        if not self[chat_id] is None:
            if entry_key in self[chat_id]:
                return self[chat_id][entry_key]
        return None
    
    def add_chat_entry(self, chat_id, entry_key, entry_value):
        """Добавляет запись для данного чата."""
        entry_key = str(entry_key)
        self.add_chat(chat_id)
        self[chat_id][entry_key] = entry_value
        self.write_data()
        return
    
    def delete_chat_entry(self, chat_id, entry_key):
        """Удаляет запись из данного чата."""
        entry_key = str(entry_key)
        if self[chat_id]:
            if entry_key in self[chat_id]:
                del self[chat_id][entry_key]
            if len(self[chat_id]) == 0:
                self.delete_chat(chat_id)
            self.write_data()
        return

class DatalistActor(DatalistChat):
    """Тип списка данных для отдельных актеров."""
    
    def get_actor_entry(self, chat_id, actor_name, entry_key):
        """Возвращает запись по entry_key в списке актера."""
        entry_key = str(entry_key)
        if actor := self.get_chat_entry(chat_id, actor_name):
            if entry_key in actor.keys():
                return actor[entry_key]
        return None
    
    def add_actor_entry(self, chat_id, actor_name, entry_key, entry_value):
        """Добавляет новую запись актеру в чате."""
        entry_key = str(entry_key)
        actor = self.get_chat_entry(chat_id, actor_name)
        if actor is None:
            self.add_chat_entry(chat_id, actor_name, {})
            actor = self.get_chat_entry(chat_id, actor_name)
        actor[entry_key] = entry_value
        self.write_data()
        return
    
    def delete_actor_entry(self, chat_id, actor_name, entry_key):
        """Удаляет запись актера."""
        if actor := self.get_chat_entry(chat_id, actor_name):
            del self.data[str(chat_id)][str(actor_name)][str(entry_key)]
            if len(actor) == 0:
                self.delete_chat_entry(chat_id, actor_name)
            self.write_data()
        return
