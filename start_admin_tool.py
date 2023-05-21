"""
Инструмент администратора.
"""

import snearl.database as db

# импорт из модулей
import snearl.module.blacklist_admin as admin_b
import snearl.module.voicelist_admin as admin_v
import snearl.module.quotelist_admin as admin_q
import snearl.module.userlist_admin  as admin_u

commands = [] # список команд заполняется в конце файла

###################
# basic functions #
###################

def chat_migration():
    """
    Заменяет в записях базы данных значения колонки чата на новое.
    """
    from snearl.module.dataupdate import chat_migrate
    
    old = input("(Получить ID чата можно командой /info)\n"\
                "Вставьте ID старого чата:\n"\
                "> ")
    new = input("\nВставьте ID нового чата:\n"\
                "> ")

    chat_migrate(old, new)

    print("\nМиграция данных успешно завершена.")

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

def clear_table():
    print("Внимание: данная функция необратимо удаляет все данные из таблицы!\n"\
          "Введите действие: (q для отмены)\n"\
          "1. Удалить [Settings] - настройки (включая токен)\n"\
          "2. Удалить [Userlist] - список пользователей\n"\
          "3. Удалить [Blacklist] - черный список\n"\
          "4. Удалить [Voicelist] - список войсов\n"\
          "5. Удалить [Quotelist] - список цитат")

    a = input("> ")
    if a == "1":
        db.table_clear("Settings")
        print("\nНастройки сборшены!")
    if a == "2":
        db.table_clear("Userlist")
        print("\n[ДАННЫЕ УДАЛЕНЫ]")
    if a == "3":
        db.table_clear("Blacklist")
        print("\n[ДАННЫЕ УДАЛЕНЫ]")
    if a == "4":
        db.table_clear("Voicelist")
        print("\n[ДАННЫЕ УДАЛЕНЫ]")
    if a == "5":
        db.table_clear("Quotelist")
        print("\n[ДАННЫЕ УДАЛЕНЫ]")
    else:
        return

    db.con.commit()

def export_token():
    token_file = db.export_dir / "token.txt"
    token = db.settings_get("token")

    db.export_dir.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)

    print(f"\nТокен успешно экспортирован в файл {token_file}.")

def import_token():
    """
    Импорт токена в базу данных из файла.
    """
    token_file = db.import_dir / "token.txt"
    if not token_file.exists():
        print(f"Файл токена не найден:\n{token_file}")
        return

    token = token_file.read_text().strip()
    db.settings_set("token", token)

    print("\nТокен успешно сохранен в базу данных.")

############
# Commands #
############

commands += [
    (
        "[v] Импортировать токен",
        import_token
    ),
    (
        "[v] Импортировать черный список",
        admin_b.import_blacklist
    ),
    (
        "[v] Импортировать войсы",
        admin_v.import_voicelist
    ),
    (
        "[v] Импортировать цитаты",
        admin_q.import_quotelist
    ),
    (
        "[^] Экспортировать токен",
        export_token
    ),
    (
        "[^] Экспортировать черный список",
        admin_b.export_blacklist
    ),
    (
        "[^] Экспортировать войсы",
        admin_v.export_voicelist
    ),
    (
        "[^] Экспортировать цитаты",
        admin_q.export_quotelist
    ),
    (
        "[!] Редактировать пользователя",
        admin_u.userlist_main
    ),
    (
        "[!] Миграция данных чата",
        chat_migration
    ),
    (
        "[!] Включить локальный режим",
        set_local_mode
    ),
    (
        "[!] Удалить данные из БД",
        clear_table
    )
]

############
# main     #
############

if __name__ == "__main__":
    while True:
        message = "\nВведите номер действия (q для выхода):\n"
        for i, e in enumerate(commands, start=1):
            message += f"{i:2}. {e[0]};\n"
        print(message)

        a = input("> ")
        if a == "q":
            break
        try:
            commands[int(a)-1][1]()
        except Exception as e:
            print(e)
