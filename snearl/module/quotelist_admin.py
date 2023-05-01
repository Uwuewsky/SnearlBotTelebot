import time

from snearl.database import export_dir, import_dir
import snearl.module.quotelist_db as db

#############
# Functions #
#############

def export_quotelist():
    """
    Экспорт цитат из базы данных.
    """
    quote_dir = export_dir / "quotelist"

    for r in db.quotelist_get_all():
        chat_id = r[0]
        author_name = r[2]
        file_id = r[1]
        file_name = r[3]
        file_blob = db.quotelist_get_blob(file_id)

        file_dir = quote_dir / chat_id / author_name
        file_path = (file_dir / file_name).with_suffix(".webp")

        if file_path.exists():
            file_path = file_path.with_stem(file_id)

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_blob)

    print(f"\nЦитаты успешно экспортированы в папку {quote_dir}.")
    return

def import_quotelist():
    """
    Импорт цитат в базу данных.
    """
    from telegram.ext import CommandHandler
    from snearl.instance import app, start_bot

    print("Теперь нужно отправить боту команду /quote_init.\n"\
          "Бот начнет отправлять в чат цитаты - не удаляйте данные сообщения.")

    app.add_handler(CommandHandler("quote_init", _init_quotes))
    start_bot() # запустить бота для загрузки войсов на сервер
    return

async def _init_quotes(update, context):
    """
    Загрузка цитат в Телеграм для дальнейшего использования.
    """
    # папка с импортируемыми войсами
    quote_dir = import_dir / "quotelist"
    if not quote_dir.is_dir():
        print(f"Папка импорта не найдена:\n{quote_dir}")
        return

    # список файлов .webp
    files = [f for f in quote_dir.rglob('*.webp')]
    if len(files) == 0:
        print(f"Папка импорта не содержит файлов .webp:\n{quote_dir}")
        return

    db.quotelist_create_table()
    start_t = time.time()
    for f in files:
        m = await update.effective_chat.send_sticker(f)
        chat_id = f.parts[-3]
        file_id = m.sticker.file_id
        file_author = f.parts[-2]
        file_desc = f.stem
        file_blob = f.read_bytes()
        db.quotelist_add(chat_id, file_id, file_author, file_desc, file_blob)
        time.sleep(0.05)
    db.con.commit()

    await update.effective_chat.send_message(
        "Импорт завершен.\n"\
        f"Кол-во: {len(files)} шт.\n"
        f"Время: {int(time.time() - start_t)} сек.\n"\
        "Вернитесь к консоли и нажмите Ctrl+C.")

    print("\nЦитаты успешно импортированы в базу данных.")
    return
