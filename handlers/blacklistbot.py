from data.bot_instance import bot
from services.databases import blacklist, write_to_blacklist

#Проверка на возможность применять команды
def check_admin(chat_id, user_id, message):
    status = bot.get_chat_member(chat_id, user_id).status
    if status == "creator" or status == "administrator":
        return True
    else:
        bot.reply_to(message, text="У тебя нет прав использовать админскую команду, чмо.")
        return False

#Добавление группы в блеклист
@bot.message_handler(commands=['add'])
def add_chat_to_blacklist(message):
    if not check_admin(message.chat.id, message.from_user.id, message):
        return
    if message.reply_to_message is None:
        bot.reply_to(message, text="Нужно отправить команду ответом на пост из группы.")
        return 
    
    if message.reply_to_message.forward_from_chat is None:
        bot.reply_to(message, text="Это ответ не на пост из группы. Фух.")
        return

    chat_id = message.reply_to_message.forward_from_chat.id
    chat_title = message.reply_to_message.forward_from_chat.title
    entry = [chat_id, chat_title]
    
    if entry in blacklist:
        bot.reply_to(message, text=f"{chat_title} уже в блеклисте, алло.")
        return
    
    blacklist.append(entry)
    write_to_blacklist()
    bot.reply_to(message, text=f"Репосты из {chat_title} добавлены в блеклист. Ибо нехуй.")

#Удаление группы из блеклиста
@bot.message_handler(commands=['delete'])
def delete_chat_from_blacklist(message):
    if not check_admin(message.chat.id, message.from_user.id, message):
        return
    
    message_offset = 0
    for i in message.entities:
        if i.type == "bot_command":
            message_offset = i.length+1
            break
    try:
        remove_index = int(message.text[message_offset:])-1
        chat_title = blacklist[remove_index][1]
        del blacklist[remove_index]
    except Exception:
        bot.reply_to(message, text="Нужно указать действительный номер чата из списка /blacklist, тыкалкин бля.")
        return
    
    write_to_blacklist()
    bot.reply_to(message, text=f"{chat_title} удален из блеклиста. Живи пока.")

#Просмотр блеклиста
@bot.message_handler(commands=['blacklist'])
def show_blacklist(message):
    s = "Список заблокированных чатов:"
    index = 0
    for i in blacklist:
        index += 1
        s += f"\n{index}) {i[1]} [{i[0]}]"
    bot.reply_to(message, text=s)

#Удаление репостнутой из канала из черного списка записи
@bot.message_handler(func=lambda message: message.forward_from_chat, content_types=["text", "photo", "video"])
def delete_reposts(message):
    if any(message.forward_from_chat.id in i for i in blacklist):
        groupname = message.forward_from_chat.title
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, 'Иди нахуй со своим ' +groupname)


