"""
Администраторские функции модели authormodel
"""

import time
import json

import snearl.database as db

#############
# Functions #
#############

def export_table(dir_name, file_ext, db_get_all, db_get_blob):
    """
    Экспорт из базы данных.
    """
    table_dir = db.export_dir / dir_name

    for r in db_get_all():
        # "SELECT chat_id, file_id, user_name, user_title, file_desc"
        chat_id, file_id, user_name, user_title, file_desc = r
        file_blob = db_get_blob(file_id)

        file_dir = table_dir / chat_id / user_title
        info_file = file_dir / "info.json"

        file_path = (file_dir / file_desc).with_suffix(file_ext)

        if file_path.is_file():
            for i in range(1, 100):
                temp_path = file_path.with_stem(file_desc + f" ({i})")
                if not temp_path.is_file():
                    file_path = temp_path
                    break
            if file_path.is_file():
                file_path = file_path.with_stem(file_id)

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_blob)

        with open(info_file, "w", encoding="utf-8") as f:
            json.dump({"user_name": user_name, "user_title": user_title},
                      f, ensure_ascii = False, indent = "    ")

    print(f"\nУспешно экспортировано в папку {table_dir}.")

async def init_table(update, context,
                     dir_name, file_ext,
                     send_attachment, db_add):
    """
    Загрузка файлов в Телеграм для дальнейшего использования.
    """
    # папка с импортируемыми войсами
    table_dir = db.import_dir / dir_name
    if not table_dir.is_dir():
        print(f"Папка импорта не найдена:\n{table_dir}")
        return

    file_count = 0
    start_t = time.time()

    # directory = import/tablelist/chat_id/author1/
    for directory in table_dir.glob("./*/*/"):
        info_file = directory / "info.json"

        if not info_file.is_file():
            print(f"Папка данных не содержит info.json:\n{directory}")
            continue

        with open(info_file, "r", encoding="utf-8") as f:
            info_data = json.load(f)

        user_name = info_data["user_name"]
        user_title = info_data["user_title"]
        chat_id = directory.parts[-2]

        for f in directory.glob(f"*{file_ext}"):
            file_count += 1
            msg = await send_attachment(f, read_timeout=20,
                                        connect_timeout=20,
                                        pool_timeout=20)

            file_id = msg.effective_attachment.file_id
            file_desc = f.stem
            file_blob = f.read_bytes()

            db_add(chat_id, file_id, user_name, user_title, file_desc, file_blob)
            time.sleep(0.05)
    db.con.commit()

    await update.effective_chat.send_message(
        "Импорт завершен.\n"\
        f"Кол-во: {file_count} шт.\n"
        f"Время: {int(time.time() - start_t)} сек.\n"\
        "Вернитесь к консоли и нажмите Ctrl+C.")

    print("\nУспешно импортировано в базу данных.")
