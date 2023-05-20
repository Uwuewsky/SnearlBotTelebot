"""
Администраторские функции модуля цитат.
"""

from snearl.module.quotelist_db import db
import snearl.module.authormodel_admin as model

#############
# Functions #
#############

def export_quotelist():
    """
    Экспорт цитат из базы данных.
    """
    return model.export_table("quotelist", ".webp", db.get_all, db.get_blob)

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

async def _init_quotes(update, context):
    """
    Загрузка цитат в Телеграм для дальнейшего использования.
    """
    return await model.init_table(update, context,
                                  "quotelist", ".webp",
                                  update.effective_chat.send_sticker,
                                  db.add)
