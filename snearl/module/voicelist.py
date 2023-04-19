import math

from telebot import types
from telebot.util import extract_arguments

from snearl.instance import bot
from snearl.datalist import DatalistActor
from snearl.util import *

_voicelist = DatalistActor("voicelist.json")

####################
# inline functions #
####################

@bot.inline_handler(lambda query: True)
def voice_inline_send(inline_query):
    """Функция инлайн запроса списка войсов."""
    offset = 0 if inline_query.offset == "" else int(inline_query.offset)
    
    # выдать результат, если таковой есть
    if out_list := get_inline_query(inline_query.query, offset=offset):
        bot.answer_inline_query(inline_query.id, out_list,
                                cache_time=60, next_offset=str(offset+50))
    # иначе выдать сообщение об ошибке
    elif offset == 0:
        s = f"По запросу {inline_query.query} ничего не найдено."
        out_message = [types.InlineQueryResultArticle("id_nothing", s,
                                                      types.InputTextMessageContent(s))]
        bot.answer_inline_query(inline_query.id, out_message, cache_time=60)
    return

def get_inline_query(query, offset=0):
    """Возвращает список войсов для отправки через инлайн."""
    if vl := get_query_entries(query):
        return [types.InlineQueryResultCachedVoice(str(i), v_id, v_title)
                for i, (v_id, v_title) in enumerate(vl)][offset:offset+50]
    return None

def get_query_entries(query):
    """
    Возвращает список записей от автора,
    либо ищет запрос в описаниях.
    """
    query = query.lower()
    result_actor_list = []
    result_search_list = []
    
    # поиск проходит по спискам всех чатов
    for chat in _voicelist.data.values():
        for actor_name, actor_voices in chat.items():
            # добавить всю коллекцию от автора
            if query == actor_name.lower():
                result_actor_list += [*actor_voices.items()]
            # иначе искать совпадения в описании войсов
            else:
                for voice_id, voice_desc in actor_voices.items():
                    if query in voice_desc.lower():
                        result_search_list.append([voice_id, voice_desc])
    
    if len(result_actor_list) > 0:
        return result_actor_list
    elif len(result_search_list) > 0:
        return result_search_list
    
    return None

####################
# /voice_add       #
####################

@bot.message_handler(commands=["voice_add"])
def voice_add(message):
    """Команда добавления нового голосового сообщения."""
    if not check_admin(message):
        return
    
    if message.reply_to_message is None:
        bot.reply_to(message, text="Нужно отправить команду ответом на голосовое сообщение.")
        return 
    
    if message.reply_to_message.voice is None:
        bot.reply_to(message, text="Это не голосовое сообщение.")
        return
    
    try:
        chat_id = message.chat.id
        args = extract_arguments(message.text).split()
        actor_name = args[0]
        voice_id = message.reply_to_message.voice.file_id
        voice_title =  " ".join(args[1:])
        if actor_name == "" or voice_title == "":
            raise Exception
    except Exception:
        bot.reply_to(message, text="Нужно указать имя автора войса и описание, например:\n"\
                                   "/voice_add Эрл Ну шо вы ребятки\n"\
                                   "Учтите, что имя чувствительно к регистру.")
        return
    
    current_voice = _voicelist.get_actor_entry(chat_id, actor_name, voice_id, voice_title)
    if current_voice:
        if current_voice == voice_title:
            bot.reply_to(message, text = "Голосовое сообщение с таким названием уже есть, придумайте другое название.")
            return
        bot.reply_to(message, text="Это голосовое сообщение уже в списке.")
        return
    else:
        _voicelist.add_actor_entry(chat_id, actor_name, voice_id, voice_title)

        file_for_downloading = bot.get_file(voice_id)
        downloaded_file = bot.download_file(file_for_downloading.file_path)
        _voicelist.download_actor_entry(downloaded_file, actor_name, voice_title)

        bot.reply_to(message, text=f"В дискографию {actor_name} успешно добавлено {voice_title}")
    return

####################
# /voice_edit      #
####################

@bot.message_handler(commands=["voice_edit"])
def voice_edit(message):
    if not check_admin(message):
        return

    try:
        chat_id = message.chat.id
        args = extract_arguments(message.text).split()
        actor_name = args[0]
        voice_num = int(args[1]) - 1
        new_title = " ".join(args[2:])
        al = _voicelist.get_chat_entry(chat_id, actor_name)

        if voice_num < 0 or voice_num > len(al)-1:
            raise Exception
        
        voice_id, old_title = [*al.items()][voice_num]
        
    except Exception:
        bot.reply_to(message, text="Нужно указать имя автора войса, его номер из списка voicelist и новое описание, например:\n"\
                                   "/voice_edit Митя 3 Очень интересный вопрос\n"\
                                   "Учтите, что имя чувствительно к регистру.")
        return
    
    if _voicelist.get_actor_entry(chat_id, actor_name, voice_id, new_title) == new_title:
        bot.reply_to(message, text = "Голосовое сообщение с таким названием уже есть, придумайте другое название.")
        return
    
    _voicelist.rename_downloaded_file(actor_name, new_title, old_title)
    _voicelist.edit_actor_entry(chat_id, actor_name, voice_id, new_title)

    bot.reply_to(message, text = f"Название войса {old_title} успешно изменено на {new_title}.")
    return

####################
# /voice_delete    #
####################

@bot.message_handler(commands=["voice_delete"])
def voice_delete(message):
    """Команда удаления голосового сообщения."""
    if not check_admin(message):
        return
    
    try:
        chat_id = message.chat.id
        args = extract_arguments(message.text).split()
        actor_name = args[0]
        voice_num = int(args[1]) - 1
        al = _voicelist.get_chat_entry(chat_id, actor_name)
        
        if voice_num < 0 or voice_num > len(al) - 1:
            raise Exception
        
        voice_id, voice_title = [*al.items()][voice_num]
        _voicelist.delete_actor_entry(chat_id, actor_name, voice_id)
    except Exception:
        bot.reply_to(message, text="Нужно указать имя автора войса и номер сообщения из /voicelist, например:\n"\
                                   "/voice_delete Эрл 15\n"\
                                   "Учтите, что имя чувствительно к регистру.")
        return
    bot.reply_to(message, text=f"Из дискографии {actor_name} успешно удален {voice_title}")
    return

####################
# /voicelist       #
####################

@bot.message_handler(commands=["voicelist"])
def voicelist_show(message):
    """Команда показа списка голосовых сообщений."""
    out_message = _voicelist_get_keyboard_text(message.chat.id, 0, 0)
    markup = _voicelist_get_keyboard(message.chat.id, 0, 0, message.from_user.id)
    bot.reply_to(message, text=out_message, reply_markup=markup)
    return

@bot.callback_query_handler(func = lambda callback: callback.data.split()[0] == "voicelist")
def _voicelist_keyboard_callback(callback):
    """Функция, отвечающая на коллбэки от нажатия кнопок клавиатуры /voicelist."""
    call_data = callback.data.split()
    call_chat = call_data[1]
    call_actor = int(call_data[2])
    call_page = int(call_data[3])
    call_user = call_data[4]
    call_type = call_data[5]
    
    if call_user != str(callback.from_user.id):
        bot.answer_callback_query(callback.id, text="Вы можете листать только отправленный Вам список.")
        return
    if call_type == "pageinfo":
        bot.answer_callback_query(callback.id, text=f"Страница #{call_page+1}")
        return
    if call_type == "actorinfo":
        bot.answer_callback_query(callback.id, text=f"Автор #{call_actor+1}")
        return
    
    if call_type == "pageback":
        call_page -= 1
    if call_type == "pagenext":
        call_page += 1
    
    if "actor" in call_type:
        call_page = 0
    if call_type == "actorback":
        call_actor -= 1
    if call_type == "actornext":
        call_actor += 1
    
    out_message = _voicelist_get_keyboard_text(call_chat, call_actor, call_page)
    markup = _voicelist_get_keyboard(call_chat, call_actor, call_page, call_user)
    bot.edit_message_text(out_message, message_id=callback.message.id,
                          chat_id=callback.message.chat.id, reply_markup=markup)
    return

def _voicelist_get_keyboard_text(chat_id, actor_num, page):
    """Возвращает текст сообщения /voicelist"""
    if _voicelist[chat_id]:
        actors_names = [*_voicelist[chat_id].keys()]
        if actor_num >= 0 and actor_num < len(actors_names):
            actor_name = actors_names[actor_num]
        else:
            actor_name = actors_names[0]
        
        if al := _voicelist.get_chat_entry(chat_id, actor_name):
            s = "Список голосовых сообщений:\n\n"
            offset = page * 25
            original_list = [*al.values()]
            print_list = original_list[offset:offset+25]
            
            # может произойти если удалить записи из списка
            # и нажать на кнопку старого сообщения
            if len(print_list) == 0:
                print_list = original_list[0:25]
                offset = 0
            
            for i, j in enumerate(print_list, start=offset+1):
                s += f"{i}) {j}\n"
            return s
    return "Список голосовых сообщений пуст."

def _voicelist_get_keyboard(chat_id, actor_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    if vl := _voicelist[chat_id]:
        actors_names = [*vl.keys()]
        index_max = len(actors_names) - 1
        
        if actor_num >= 0 and actor_num <= index_max:
            actor_name = actors_names[actor_num]
        else:
            actor_name = actors_names[0]
            actor_num = 0
        page_max = max(0, math.ceil(len(vl[actor_name])/25) - 1)
        if page > page_max or page < 0:
            page = 0
        
        call_data = f"voicelist {chat_id} {actor_num} {page} {user_id}"
        
        # Страницы авторов
        actor_name_next = ""
        actor_name_back = ""
        if actor_num == 0 and actor_num < index_max:
            actor_name_next = actors_names[actor_num+1]
        elif actor_num == index_max and actor_num != 0:
            actor_name_back = actors_names[actor_num-1]
        elif actor_num > 0 and actor_num < index_max:
            actor_name_next = actors_names[actor_num+1]
            actor_name_back = actors_names[actor_num-1]

        btn_actor_back = types.InlineKeyboardButton(f"< {actor_name_back}",
                                                    callback_data=f"{call_data} actorback")
        btn_actor_info = types.InlineKeyboardButton(actor_name,
                                                    callback_data=f"{call_data} actorinfo")
        btn_actor_next = types.InlineKeyboardButton(f"{actor_name_next} >",
                                                    callback_data=f"{call_data} actornext")
        
        if actor_num == 0 and actor_num < index_max:
            keyboard.add(btn_actor_info, btn_actor_next)
        elif actor_num == index_max and actor_num != 0:
            keyboard.add(btn_actor_back, btn_actor_info)
        elif actor_num > 0 and actor_num < index_max:
            keyboard.add(btn_actor_back, btn_actor_info, btn_actor_next)
        else:
            keyboard.add(btn_actor_info)
        
        # Страницы списка
        btn_page_back = types.InlineKeyboardButton("< Назад",
                                                   callback_data=f"{call_data} pageback")
        btn_page_info = types.InlineKeyboardButton(f"{page+1}/{page_max+1}",
                                                   callback_data=f"{call_data} pageinfo")
        btn_page_next = types.InlineKeyboardButton("Вперед >",
                                                   callback_data=f"{call_data} pagenext")
        if page == 0 and page < page_max:
            keyboard.add(btn_page_info, btn_page_next)
        elif page == page_max and page != 0:
            keyboard.add(btn_page_back, btn_page_info)
        elif page > 0 and page < page_max:
            keyboard.add(btn_page_back, btn_page_info, btn_page_next)
        else:
            keyboard.add(btn_page_info)
    return keyboard
