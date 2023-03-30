from snearl.instance import bot

#############
# Функции   #
#############

# Функция запуска бота
def start_bot():
    print("SnearlBot запущен.\nCtrl+C чтобы остановить бота.")
    
    # каждый отдельный импорт
    # можно отключить/подключить
    # для отдельной функциональности
    import snearl.module.blacklist
    import snearl.module.voicelist
    
    bot.infinity_polling()

# Проверка на возможность применять админские команды
def check_admin(message):
    status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if status in ["administrator", "creator"]:
        return True
    else:
        bot.reply_to(message, text="У тебя нет прав использовать админскую команду.")
        return False
