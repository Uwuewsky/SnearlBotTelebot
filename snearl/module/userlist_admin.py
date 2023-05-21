from pathlib import Path

import snearl.module.userlist_db as db

def userlist_main():
    page = 0
    max_users = 20
    while True:
        user_list = db.get_table()

        print("\nВведите ID пользователя\n"\
              f"Страница {page}\n"\
              " <-- a | q: выход | d --> \n")

        offset = page * max_users
        for user in user_list[offset:offset+max_users]:
            print(f" ID: {user[0]:2} | {user[1] or '-':17} | {user[2] or '-':25} "\
                  f"| {user[3] or '-':17} | {'Avatar' if user[4] else '-':6} |")
        a = input("> ")

        if a == "q":
            return
        if a == "a":
            page -= 1
            continue
        if a == "d":
            page += 1
            continue

        user_id = int(a)

        print("Выберите действие:\n"\
              "1. Установать никнейм\n"\
              "2. Установить аватар")
        a = input("> ")

        if a == "1":
            _set_nick(user_id)
        if a == "2":
            _set_avatar(user_id)
        db.con.commit()

def _set_nick(user_id):
    print("Введите никнейм:\n"\
          "(null чтобы удалить ник)")
    a = input("> ")

    if a == "null":
        db.set_nick(user_id, None)
        print("\nНикнейм сброшен")
    else:
        db.set_nick(user_id, a)
        print("\nНикнейм установлен")

def _set_avatar(user_id):
    path = Path(".")
    files = [*path.glob("*.jpg")]
    files += [*path.glob("*.png")]

    print("Выберите файл:\n"\
          "(null чтобы удалить ник)")

    if files:
        for i, f in enumerate(files):
            print(f"{i:2}. {f}")
    else:
        print("Файлы не найдены.\n"\
              f"Скопируйте в папку {path.absolute()} файлы .jpg или .png "\
              "(желательно 48x48).")

    a = input("> ")

    if a == "null":
        db.set_avatar(user_id, None)
        print("\nАватар сброшен")
    else:
        db.set_avatar(user_id, files[int(a)].read_bytes())
        print("\nАватар установлен")
