"""
Главный модуль приложения, базовых команд и функций.
"""

import logging
from logging.handlers import RotatingFileHandler

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    PicklePersistence)

import snearl.database as db

persistence = PicklePersistence(filepath=db.data_dir / "persistence")

app = (
    Application.builder()
    .token(db.settings_get("token"))
    .persistence(persistence=persistence)
    .build()
)
help_messages = ["SnearlBot умеет:\n"]

##########################
# Информационные команды #
##########################

async def send_help(update, context):
    msg = "".join(help_messages)
    await update.message.reply_markdown_v2(msg)

async def send_info(update, context):
    await update.message.reply_markdown_v2(
        f"Chat ID: `{update.effective_chat.id}`\n"\
        f"User ID: `{update.effective_user.id}`")

########################
# Функция запуска бота #
########################

def start_bot():
    handler1 = RotatingFileHandler(db.data_dir / "log.txt",
                                   maxBytes=100*1024,
                                   backupCount=1,
                                   encoding="utf-8")
    handler2 = logging.StreamHandler()
    logging.basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s",
                        level=logging.WARNING, handlers=[handler1, handler2])

    app.add_handler(CommandHandler("start", send_help))
    app.add_handler(CommandHandler("help", send_help))
    app.add_handler(CommandHandler("info", send_info))

    import snearl.module.blacklist
    snearl.module.blacklist.main()

    import snearl.module.voicelist
    snearl.module.voicelist.main()

    import snearl.module.quotelist
    snearl.module.quotelist.main()

    import snearl.module.dataupdate
    snearl.module.dataupdate.main()

    import snearl.module.inline_handler
    snearl.module.inline_handler.main()

    print("SnearlBot запущен.\nCtrl+C чтобы остановить бота.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
