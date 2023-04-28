import snearl.database as db

# импорт из модулей
from snearl.module.dataupdate import chat_migrate
from snearl.module.voicelist_admin import (
    import_voicelist, export_voicelist
)

commands = [] # список команд заполняется в конце файла

###################
# basic functions #
###################

def chat_migration():
    """
    Заменяет в записях базы данных значения колонки чата на новое.
    """
    old = input("(Получить ID чата можно командой /info)\n"\
                "Вставьте ID старого чата:\n"\
                "> ")
    new = input("\nВставьте ID нового чата:\n"\
                "> ")

    chat_migrate(old, new)

    print("\nМиграция данных успешно завершена.")
    return

def set_local_mode():
    """
    Запрещает использовать команды редактирующие базу данных
    везде кроме указанного чата.
    """
    print("Локальный режим запрещает для пользователей из других чатов\n"\
          "команды, которые выполняют запись в базу данных.\n\n"\
          "Введите ID чата которому бот разрешит пользоваться такими командами;\n"\
          "Либо введите q чтобы отключить локальный режим:\n"\
          "(Получить ID чата можно командой /info)")

    chat_id = input("> ")
    if chat_id == "q":
        db.settings_delete("local_mode")
        print("\nЛокальный режим отключен.")
    else:
        db.settings_set("local_mode", chat_id)
        print("\nЛокальный режим включен")
    return

def clear_table():
    print("Внимание: данная функция необратимо удаляет все данные из таблицы!\n"\
          "Введите номер очищаемой таблицы (q для отмены):\n"\
          "1. Таблица данных черного списка.\n"\
          "2. Таблица данных голосовых сообщений.")

    a = input("> ")
    if a == "1":
        db.table_clear("Blacklist")
        print("\nТаблица Blacklist очищена.")
    elif a == "2":
        db.table_clear("Voicelist")
        print("\nТаблица Voicelist очищена.")
    else:
        return

    db.con.commit()
    return

def export_token():
    token_file = db.export_dir / "token.txt"
    token = db.settings_get("token")

    db.export_dir.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)

    print(f"\nТокен успешно экспортирован в файл {token_file}.")
    return

def import_token():
    """
    Импорт токена в базу данных из файла.
    """
    token_file = db.import_dir / "token.txt"
    if not token_file.exists():
        print(f"Файл токена не найден:\n{token_file}")
        return

    token = token_file.read_text()
    db.settings_set("token", token)

    print("\nТокен успешно сохранен в базу данных.")
    return

############
# Commands #
############

commands += [
    (
        "Импортировать токен",
        import_token
    ),
    (
        "Импортировать войсы",
        import_voicelist
    ),
    (
        "Экспортировать токен",
        export_token
    ),
    (
        "Экспортировать войсы",
        export_voicelist
    ),
    (
        "Миграция данных чата",
        chat_migration
    ),
    (
        "Включить локальный режим",
        set_local_mode
    ),
    (
        "Удалить данные из БД",
        clear_table
    )
]

############
# main     #
############

if __name__ == "__main__":
    while True:
        msg = "\nВведите номер действия (q для выхода):\n"
        for i, e in enumerate(commands, start=1):
            msg += f"{i}. {e[0]};\n"
        print(msg)

        a = input("> ")
        try:
            commands[int(a)-1][1]()
        except Exception as e:
            print(e)
            print("Выходим...")
            break
