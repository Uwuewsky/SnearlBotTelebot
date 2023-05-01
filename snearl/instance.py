"""
Главный модуль приложения, базовых команд и функций.
"""

from telegram import Chat, Update
from telegram.ext import Application, CommandHandler

import snearl.database as db

app = Application.builder().token(db.settings_get("token")).build()
help_messages = ["SnearlBot умеет:\n"]

##########################
# Информационные команды #
##########################

async def send_help(update, context):
    msg = "".join(help_messages)
    await update.message.reply_markdown_v2(msg)
    return

async def send_info(update, context):
    await update.message.reply_markdown_v2(
        f"Chat ID: `{update.effective_chat.id}`\n"\
        f"User ID: `{update.effective_user.id}`")
    return

########################
# Функция запуска бота #
########################

def start_bot():
    app.add_handler(CommandHandler("start", send_help))
    app.add_handler(CommandHandler("help", send_help))
    app.add_handler(CommandHandler("info", send_info))

    # каждый отдельный импорт
    # можно отключить/подключить
    # для отдельной функциональности
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
    return
