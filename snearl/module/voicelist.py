"""
Модуль для голосовых сообщений.
Позволяет сохранять войсы через команды,
а затем отправлять в чат через поиск инлайн.
"""

import math, re
from io import BytesIO

from telegram import (
    InlineQueryResultCachedVoice, InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    InlineQueryHandler, CommandHandler, CallbackQueryHandler)

from snearl.instance import app, help_messages, check_access
import snearl.module.voicelist_db as db

####################
# main             #
####################

def main():
    db.voicelist_create_table()
    db.con.commit()

    help_messages.append("""
*Хранить и отправлять инлайн списки голосовых сообщений*
  a\. Добавить войс:
      `/voice_add [ИмяАвтора] [КраткоеОписание]`;
  b\. Открыть инлайн список войсов:
      `@SnearlBot [ТекстЗапроса]`;
      Запросом может быть _имя автора_ или _строка из описания_;
  c\. Удалить войс:
      `/voice_delete [ИмяАвтора] [НомерВойса]`;
  d\. Отредактировать описание войса:
      `/voice_edit [ИмяАвтора] [НомерВойса] [НовоеОписание]`;
  e\. Список войсов: /voicelist;
""")

    # команды
    app.add_handler(CommandHandler("voice_add", voice_add))
    app.add_handler(CommandHandler("voice_delete", voice_delete))
    app.add_handler(CommandHandler("voicelist", voicelist_show))

    # инлайн
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(
        voicelist_show_callback,
        pattern="^voicelist"))

    return

####################
# inline functions #
####################

async def inline_query(update, context):
    """Функция инлайн запроса списка войсов."""
    query = update.inline_query.query
    if update.inline_query.offset:
        offset = int(update.inline_query.offset)
    else:
        offset = 0

    # список найденных войсов в бд
    if vl := db.voicelist_search(query, offset):
        # составляем инлайн список
        results = [
            InlineQueryResultCachedVoice(
                id=str(i),
                voice_file_id=e[1],
                title=f"{e[2]} — {e[3]}",
                caption=f"{e[2]} — {e[3]}"
            ) for i, e in enumerate(vl)
        ]
    elif not offset:
        # иначе выдаем сообщение что ничего не найдено
        # not offset чтобы это сообщение не выдавало в конце списка
        s = f"По запросу {update.inline_query.query} ничего не найдено"
        results = [
            InlineQueryResultArticle(
                id = "0",
                title = s,
                input_message_content = InputTextMessageContent(s))
        ]
    else:
        return # пролистали до конца списка

    try:
        await update.inline_query.answer(results, next_offset=offset+50)
    except Exception as e:
        # выдаем в инлайн сообщение об ошибке
        s = f"Во время запроса {update.inline_query.query} произошла ошибка"
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id = "0",
                title = s,
                description = str(e),
                input_message_content = InputTextMessageContent(
                    f"{s}:\n{str(e)}"))
        ])
    return

####################
# /voice_add       #
####################

async def voice_add(update, context):
    """Команда добавления нового голосового сообщения."""
    if await check_access(update):
        return

    if update.message.reply_to_message is None:
        await update.message.reply_text(
            "Нужно отправить команду ответом на голосовое сообщение.")
        return

    if update.message.reply_to_message.voice is None:
        await update.message.reply_text("Это не голосовое сообщение.")
        return

    if len(context.args) < 2:
        await update.message.reply_markdown_v2(
            "Нужно указать имя автора и описание, например:\n"\
            "`/voice_add Эрл Ну шо вы ребятки`\n"\
            "Учтите, что имя чувствительно к регистру\.")
        return

    chat_id = update.effective_chat.id
    file_id = update.message.reply_to_message.voice.file_id
    # второй индекс ограничивает длину строки в 20 и 50 символов
    file_author = context.args[0][:20]
    file_desc =  " ".join(context.args[1:])[:50]

    # проверка имен на валидность
    regexp = re.compile("^[\w ]*$")
    if not (re.match(regexp, file_author) and
            re.match(regexp, file_desc)):
        await update.message.reply_text(
            "Имя автора или описание содержит недопустимые символы.")
        return

    if db.voicelist_get(file_id):
        await update.message.reply_text(
            "Это голосовое сообщение уже в списке.")
        return

    with BytesIO() as file_blob:
        f = await app.bot.get_file(file_id)
        await f.download_to_memory(file_blob)
        db.voicelist_create_table()
        db.voicelist_add(chat_id, file_id,
                         file_author, file_desc,
                         file_blob.getbuffer())
        db.con.commit()

    await update.message.reply_text(
        f"В дискографию {file_author} успешно добавлено {file_desc}")
    return

####################
# /voice_delete    #
####################

async def voice_delete(update, context):
    """Команда удаления голосового сообщения."""
    if await check_access(update):
        return

    try:
        chat_id = update.effective_chat.id
        file_author = context.args[0]
        file_num = int(context.args[1]) - 1

        # взять войс по указанному в команде номеру
        vl = db.voicelist_by_author(chat_id, file_author)
        if file_num < 0 or file_num > len(vl) - 1:
            raise Exception

        entry = vl[file_num]
        file_id, file_desc = entry[1], entry[3]

        db.voicelist_delete(file_id)
        db.con.commit()

    except Exception:
        await update.message.reply_markdown_v2(
            "Нужно указать имя автора войса и "\
            "номер сообщения из /voicelist, например:\n"\
            "`/voice_delete Эрл 15`\n"\
            "Учтите, что имя чувствительно к регистру\.")
        return

    await update.message.reply_text(
        f"Из дискографии {file_author} успешно удален {file_desc}")
    return

####################
# /voicelist       #
####################

async def voicelist_show(update, context):
    """Команда показа списка голосовых сообщений."""
    out_message = _voicelist_show_text(update.effective_chat.id, 0, 0)
    markup = _voicelist_show_keyboard(
        update.effective_chat.id, 0, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)
    return

async def voicelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /voicelist."""
    call_data = update.callback_query.data.split()
    call_chat = call_data[1]
    call_author = int(call_data[2])
    call_page = int(call_data[3])
    call_user = call_data[4]
    call_type = call_data[5]

    if call_user != str(update.callback_query.from_user.id):
        await update.callback_query.answer(
            "Вы можете листать только отправленный Вам список.")
        return
    if call_type == "pageinfo":
        await update.callback_query.answer(f"Страница #{call_page+1}")
        return
    if call_type == "authorinfo":
        await update.callback_query.answer(f"Автор #{call_author+1}")
        return

    if call_type == "pageback":
        call_page -= 1
    if call_type == "pagenext":
        call_page += 1

    if "author" in call_type:
        call_page = 0
    if call_type == "authorback":
        call_author -= 1
    if call_type == "authornext":
        call_author += 1

    out_message = _voicelist_show_text(
        call_chat, call_author, call_page)
    markup = _voicelist_show_keyboard(
        call_chat, call_author, call_page, call_user)
    await update.callback_query.edit_message_text(
        out_message, reply_markup=markup)
    return

def _voicelist_show_text(chat_id, author_num, page):
    """Возвращает текст сообщения /voicelist"""

    if al := db.voicelist_authors_list(chat_id):
        # найти автора по номеру из списка всех авторов чата
        if author_num >= 0 and author_num < len(al):
            file_author = al[author_num]
        else:
            file_author = al[0]

        # список всех войсов автора для составления текста
        vl = db.voicelist_by_author(chat_id, file_author)
        s = "Список голосовых сообщений:\n\n"
        offset = page * 25

        # сформатировать текст в виде списка войсов
        # с постраничным отступом и нумерацией
        if not vl[offset:offset+25]:
            offset = 0
        for i, e in enumerate(vl[offset:offset+25], start=offset+1):
            s += f"{i}) {e[3]}\n"

        return s
    return "Список голосовых сообщений пуст."

def _voicelist_show_keyboard(chat_id, author_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    al = db.voicelist_authors_list(chat_id)
    if not al:
        return None
    ##################################
    # Клавиатура перехода по авторам #

    # ищем имя автора по номеру
    index_max = len(al) - 1
    if author_num >= 0 and author_num <= index_max:
        file_author = al[author_num]
    else:
        file_author = al[0]
        author_num = 0

    # используем автора чтобы получить список его войсов
    # и последнюю страницу для пролистывания их списка
    if vl := db.voicelist_by_author(chat_id, file_author):
        page_max = max(0, math.ceil(len(vl)/25) - 1)
    if page > page_max or page < 0:
        page = 0

    # данные, передающиеся в коллбека при нажатии на кнопку
    call_data = f"voicelist {chat_id} {author_num} {page} {user_id}"

    # Имена авторов для кнопок перехода
    author_name_next = ""
    author_name_back = ""
    if author_num == 0 and author_num < index_max:
        author_name_next = al[author_num + 1]
    elif author_num == index_max and author_num != 0:
        author_name_back = al[author_num - 1]
    elif author_num > 0 and author_num < index_max:
        author_name_next = al[author_num + 1]
        author_name_back = al[author_num - 1]

    # Сами кнопки
    btn_author_back = InlineKeyboardButton(
        f"< {author_name_back}",
        callback_data=f"{call_data} authorback")
    btn_author_info = InlineKeyboardButton(
        file_author,
        callback_data=f"{call_data} authorinfo")
    btn_author_next = InlineKeyboardButton(
        f"{author_name_next} >",
        callback_data=f"{call_data} authornext")

    # Добавление этих кнопок в ряд клавиатуры
    keyboard = []
    keyboard_author = []

    if author_num == 0 and author_num < index_max:
        keyboard_author += [btn_author_info, btn_author_next]
    elif author_num == index_max and author_num != 0:
        keyboard_author += [btn_author_back, btn_author_info]
    elif author_num > 0 and author_num < index_max:
        keyboard_author += [
            btn_author_back, btn_author_info, btn_author_next
        ]
    else:
        keyboard_author += [btn_author_info]

    keyboard.append(keyboard_author)

    ########################################### 
    # Клавиатура перехода по страницам войсов #

    # Кнопки
    btn_page_back = InlineKeyboardButton(
        "< Назад",
        callback_data=f"{call_data} pageback")
    btn_page_info = InlineKeyboardButton(
        f"{page+1}/{page_max+1}",
        callback_data=f"{call_data} pageinfo")
    btn_page_next = InlineKeyboardButton(
        "Вперед >",
        callback_data=f"{call_data} pagenext")

    # Добавление этих кнопок во второй ряд клавиатуры
    keyboard_page = []
    if page == 0 and page < page_max:
        keyboard_page += [btn_page_info, btn_page_next]
    elif page == page_max and page != 0:
        keyboard_page += [btn_page_back, btn_page_info]
    elif page > 0 and page < page_max:
        keyboard_page += [btn_page_back, btn_page_info, btn_page_next]
    else:
        keyboard_page += [btn_page_info]
    keyboard.append(keyboard_page)

    # Составление клавиатуры
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup
