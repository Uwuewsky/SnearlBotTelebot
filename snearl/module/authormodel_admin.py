"""
Администраторские функции модели authormodel
"""

import time

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
        chat_id = r[0]
        author_name = r[2]
        file_id = r[1]
        file_name = r[3]
        file_blob = db_get_blob(file_id)

        file_dir = table_dir / chat_id / author_name

        file_path = (file_dir / file_name).with_suffix(file_ext)

        if file_path.exists():
            file_path = file_path.with_stem(file_id)

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_blob)

    print(f"\nУспешно экспортировано в папку {table_dir}.")

async def init_table(update, context,
                     dir_name, file_ext,
                     send_attachment,
                     db_create_table, db_add):
    """
    Загрузка файлов в Телеграм для дальнейшего использования.
    """
    # папка с импортируемыми войсами
    table_dir = db.import_dir / dir_name
    if not table_dir.is_dir():
        print(f"Папка импорта не найдена:\n{table_dir}")
        return

    # список файлов
    files = list(table_dir.rglob(f"*{file_ext}"))
    if len(files) == 0:
        print(f"Папка импорта не содержит файлов {file_ext}:\n{table_dir}")
        return

    db_create_table()
    start_t = time.time()
    for f in files:
        msg = await send_attachment(f, read_timeout=20,
                                    connect_timeout=20,
                                    pool_timeout=20)

        chat_id = f.parts[-3]
        file_id = msg.effective_attachment.file_id
        file_author = f.parts[-2]
        file_desc = f.stem
        file_blob = f.read_bytes()

        db_add(chat_id, file_id, file_author, file_desc, file_blob)
        time.sleep(0.05)
    db.con.commit()

    await update.effective_chat.send_message(
        "Импорт завершен.\n"\
        f"Кол-во: {len(files)} шт.\n"
        f"Время: {int(time.time() - start_t)} сек.\n"\
        "Вернитесь к консоли и нажмите Ctrl+C.")

    print("\nУспешно импортировано в базу данных.")
