import math

from telebot import types
from telebot.util import content_type_media, extract_arguments

from snearl.instance import bot
from snearl.datalist import DatalistChat
from snearl.util import *

_blacklist = DatalistChat("blacklist.json")

#####################
# handler functions #
#####################

@bot.message_handler(func=lambda message: message.forward_from_chat,
                     content_types=content_type_media)
def blacklist_delete_reposts(message):
    """Функция удаления сообщения, репостнутой из чата черного списка."""
    if _blacklist.get_chat_entry(message.chat.id, message.forward_from_chat.id):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"Репост из {message.forward_from_chat.title} удален.")
    return

#####################
# /block            #
#####################

@bot.message_handler(commands=["block"])
def blacklist_add_chat(message):
    """Команда добавления чата в блеклист."""
    if not check_admin(message):
        return
    
    if message.reply_to_message is None:
        bot.reply_to(message, text="Нужно отправить команду ответом на репост из группы.")
        return 
    
    if message.reply_to_message.forward_from_chat is None:
        bot.reply_to(message, text="Это не репост из группы.")
        return
    
    block_chat_id = message.reply_to_message.forward_from_chat.id
    block_chat_title = message.reply_to_message.forward_from_chat.title

    if _blacklist.get_chat_entry(message.chat.id, block_chat_id):
        bot.reply_to(message, text=f"{block_chat_title} уже в блеклисте.")
        return
    else:
        _blacklist.add_chat_entry(message.chat.id, block_chat_id, block_chat_title)
        bot.reply_to(message, text=f"Репосты из {block_chat_title} добавлены в черный список.")
    return

#####################
# /allow            #
#####################

@bot.message_handler(commands=["allow"])
def blacklist_delete_chat(message):
    """Команда удаления чата из блеклиста."""
    if not check_admin(message):
        return
    try:
        remove_index = int(extract_arguments(message.text))
        if bl := _blacklist[message.chat.id]:
            for i, entry in enumerate(bl.items(), start=1):
                if i == remove_index:
                    block_chat_id, block_chat_title = entry
        _blacklist.delete_chat_entry(message.chat.id, block_chat_id)
        bot.reply_to(message, text=f"{block_chat_title} удален из черного списка.")
    except Exception:
        bot.reply_to(message, text="Нужно указать номер чата из списка /blacklist.")
        return

#####################
# /blacklist        #
#####################

@bot.message_handler(commands=["blacklist"])
def blacklist_show(message):
    """Команда показа списка заблокированных чатов."""
    out_message = _blacklist_get_keyboard_text(message.chat.id, 0)
    markup = _blacklist_get_keyboard(message.chat.id, 0, message.from_user.id)
    bot.reply_to(message, text=out_message, reply_markup=markup)
    return

@bot.callback_query_handler(func = lambda callback: callback.data.split()[0] == "blacklist")
def _blacklist_keyboard_callback(callback):
    """Функция, отвечающая на коллбэки от нажатия кнопок клавиатуры /blacklist."""
    call_data = callback.data.split()
    call_chat = call_data[1]
    call_page = int(call_data[2])
    call_user = call_data[3]
    call_type = call_data[4]
    
    if call_user != str(callback.from_user.id):
        bot.answer_callback_query(callback.id, text="Вы можете листать только отправленный Вам список.")
        return
    if call_type == "pageinfo":
        bot.answer_callback_query(callback.id, text=f"Страница #{call_page+1}")
        return
    
    if call_type == "pageback":
        call_page -= 1
    if call_type == "pagenext":
        call_page += 1
    
    out_message = _blacklist_get_keyboard_text(call_chat, call_page)
    markup = _blacklist_get_keyboard(call_chat, call_page, call_user)
    bot.edit_message_text(out_message, message_id=callback.message.id,
                          chat_id=callback.message.chat.id, reply_markup=markup)
    return

def _blacklist_get_keyboard(chat_id, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    if bl := _blacklist[chat_id]:
        page_max = max(0, math.ceil(len(bl)/25) - 1)
        
        if page > page_max or page < 0:
            page = 0
        
        call_data = f"blacklist {chat_id} {page} {user_id}"
        
        btn_back = types.InlineKeyboardButton("< Назад",
                                              callback_data=f"{call_data} pageback")
        btn_info = types.InlineKeyboardButton(f"{page+1}/{page_max+1}",
                                              callback_data=f"{call_data} pageinfo")
        btn_next = types.InlineKeyboardButton("Вперед >",
                                              callback_data=f"{call_data} pagenext")
        if page == 0 and page < page_max:
            keyboard.add(btn_info, btn_next)
        elif page == page_max and page != 0:
            keyboard.add(btn_back, btn_info)
        elif page > 0 and page < page_max:
            keyboard.add(btn_back, btn_info, btn_next)
        else:
            keyboard.add(btn_info)
    
    return keyboard

def _blacklist_get_keyboard_text(chat_id, page):
    """Функция, возвращающая текст сообщения с постраничной клавиатурой."""
    if bl := _blacklist[chat_id]:
        s = "Список заблокированных чатов:\n\n"
        offset = page * 25
        original_list = [*bl.values()]
        print_list = original_list[offset:offset+25]
        
        # может произойти если удалить записи из списка
        # и нажать на кнопку старого сообщения
        if len(print_list) == 0:
            print_list = original_list[0:25]
            offset = 0
        
        for i, j in enumerate(print_list, start=offset+1):
            s += f"{i}) {j}\n"
        return s
    else:
        return f"Список заблокированных чатов пуст."
