"""
Модуль для голосовых сообщений.
Позволяет сохранять войсы через команды,
а затем отправлять в чат через поиск инлайн.
"""

import math, re, io

from telegram import (
    InlineQueryResultCachedVoice, InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    InlineQueryHandler, CommandHandler, CallbackQueryHandler)

from snearl.instance import app, help_messages
import snearl.module.voicelist_db as db
import snearl.module.keyboard as kbrd
import snearl.module.utils as utils

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
  d\. Список войсов: /voicelist;
""")

    # команды
    app.add_handler(CommandHandler("voice_add", voice_add))
    app.add_handler(CommandHandler("voice_delete", voice_delete))
    app.add_handler(CommandHandler("voicelist", voicelist_show))

    # инлайн
    app.add_handler(CallbackQueryHandler(
        voicelist_show_callback,
        pattern="^voicelist"))

    return

####################
# inline functions #
####################

def voice_inline_query(i, e):
    """Функция инлайн запроса списка войсов."""
    return InlineQueryResultCachedVoice(
        id=str(i),
        voice_file_id = e[1],
        title=f"{e[2]} — {e[3]}",
        caption=f"{e[2]} — {e[3]}"
    )

####################
# /voice_add       #
####################

async def voice_add(update, context):
    """Команда добавления нового голосового сообщения."""
    if await utils.check_access(update):
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

    with io.BytesIO() as file_blob:
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
    if await utils.check_access(update):
        return

    try:
        chat_id = update.effective_chat.id
        file_author = context.args[0]
        file_num = int(context.args[1]) - 1

        # взять войс по указанному в команде номеру
        l = db.voicelist_by_author(chat_id, file_author)
        if file_num < 0 or file_num > len(l) - 1:
            raise Exception

        entry = l[file_num]
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
    await kbrd.authorlist_show_callback(update, context,
                                        _voicelist_show_text,
                                        _voicelist_show_keyboard)
    return

def _voicelist_show_text(chat_id, author_num, page):
    """Возвращает текст сообщения /voicelist"""
    e = kbrd.authorlist_show_text(chat_id, author_num, page,
                                  db.voicelist_authors_list,
                                  db.voicelist_by_author,
                                  "Список голосовых сообщений")
    return e

def _voicelist_show_keyboard(chat_id, author_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.authorlist_show_keyboard(chat_id, author_num, page, user_id,
                                      db.voicelist_authors_list,
                                      db.voicelist_by_author,
                                      "voicelist")
    return e
