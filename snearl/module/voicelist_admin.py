import time

from snearl.database import export_dir, import_dir
import snearl.module.voicelist_db as db

#############
# Functions #
#############

def export_voicelist():
    """
    Экспорт войсов из базы данных.
    """
    voice_dir = export_dir / "voicelist"

    for r in db.voicelist_get_all():
        chat_id = r[0]
        author_name = r[2]
        file_id = r[1]
        file_name = r[3]
        file_blob = db.voicelist_get_blob(file_id)

        file_dir = voice_dir / chat_id / author_name
        file_path = (file_dir / file_name).with_suffix(".ogg")

        if file_path.exists():
            file_path = file_path.with_stem(file_id)

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_blob)

    print(f"\nГолосовые сообщения успешно экспортированы в папку {voice_dir}.")
    return

def import_voicelist():
    """
    Импорт войсов в базу данных.
    """
    from telegram.ext import CommandHandler
    from snearl.instance import app, start_bot

    print("Теперь нужно отправить боту команду /voice_init.\n"\
          "Бот начнет отправлять в чат войсы - не удаляйте данные сообщения.")

    app.add_handler(CommandHandler("voice_init", _init_voices))
    start_bot() # запустить бота для загрузки войсов на сервер
    return

async def _init_voices(update, context):
    """
    Загрузка войсов в Телеграм для дальнейшего использования.
    """
    # папка с импортируемыми войсами
    voice_dir = import_dir / "voicelist"
    if not voice_dir.is_dir():
        print(f"Папка импорта не найдена:\n{voice_dir}")
        return

    # список файлов .ogg
    files = [f for f in voice_dir.rglob('*.ogg')]
    if len(files) == 0:
        print(f"Папка импорта не содержит файлов .ogg:\n{voice_dir}")
        return

    db.voicelist_create_table()
    for f in files:
        m = await update.effective_chat.send_voice(f)
        chat_id = f.parts[-3]
        file_id = m.voice.file_id
        file_author = f.parts[-2]
        file_desc = f.stem
        file_blob = f.read_bytes()
        db.voicelist_add(chat_id, file_id, file_author, file_desc, file_blob)
        time.sleep(0.05)
    db.con.commit()

    await update.effective_chat.send_message(
        "Импорт завершен. Вернитесь к консоли и нажмите Ctrl+C.")

    print("\nГолосовые сообщения успешно импортированы в базу данных.")
    return
