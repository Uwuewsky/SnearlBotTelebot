"""
Администраторские функции модуля войсов.
"""

from snearl.module.voicelist_db import db
import snearl.module.authormodel_admin as model

#############
# Functions #
#############

def export_voicelist():
    """
    Экспорт войсов из базы данных.
    """
    return model.export_table("voicelist", ".ogg", db.get_all, db.get_blob)

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

async def _init_voices(update, context):
    """
    Загрузка войсов в Телеграм для дальнейшего использования.
    """
    return await model.init_table(update, context,
                                  "voicelist", ".ogg",
                                  update.effective_chat.send_voice,
                                  db.create_table, db.add)
