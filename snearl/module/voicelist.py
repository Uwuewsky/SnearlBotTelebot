"""
Модуль для голосовых сообщений.
Позволяет сохранять войсы через команды,
а затем отправлять в чат через поиск инлайн.
"""

from telegram import InlineQueryResultCachedVoice
from telegram.ext import CommandHandler, CallbackQueryHandler

from snearl.module import utils
from snearl.instance import app, help_messages

import snearl.module.authormodel as datamodel
import snearl.module.authormodel_kbrd as kbrd
from snearl.module.voicelist_db import db

####################
# main             #
####################

def main():
    db.create_table()
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

    # коллбек /voicelist
    app.add_handler(CallbackQueryHandler(
        voicelist_show_callback,
        pattern="^voicelist"))

####################
# inline functions #
####################

def voice_search(query, offset, limit):
    return db.search(query, offset, limit)

def voice_query_result(i, e):
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
    message = update.message.reply_to_message
    args = context.args

    if await utils.check_access(update):
        return

    if not message:
        await update.message.reply_text(
            "Нужно отправить команду ответом на голосовое сообщение.")
        return

    if not message.voice:
        await update.message.reply_text("Это не голосовое сообщение.")
        return

    chat_id = update.effective_chat.id
    file_id = message.voice.file_id

    if db.get(file_id):
        await update.message.reply_text(
            "Это голосовое сообщение уже в списке.")
        return

    # имя автора записи в бд
    file_author = utils.validate(
        utils.get_sender_title_short(message))
    if args and not file_author:
        file_author = utils.validate(args[0])
        args = args[1:]

    if not file_author:
        await update.message.reply_markdown_v2(
            "Введите имя вручную, например\:\n"\
            "`/voice_add Эрл`")
        return

    # описание записи в бд
    file_desc = utils.validate(
        utils.get_description(message))
    if args and not file_desc:
        file_desc = utils.validate(" ".join(args))

    if not file_desc:
        await update.message.reply_markdown_v2(
            "Введите описание вручную, например\:\n"\
            "`/voice_add Продал все приставки`")
        return

    # скачиваем войс и добавляем в БД
    file_blob = await utils.download_file(file_id)
    db.create_table()
    db.add(chat_id, file_id,
           file_author, file_desc,
           file_blob.getbuffer())
    db.con.commit()
    file_blob.close()

    await update.message.reply_text(
        f"В дискографию {file_author} успешно добавлено {file_desc}")

####################
# /voice_delete    #
####################

async def voice_delete(update, context):
    """Команда удаления голосового сообщения."""
    if await utils.check_access(update):
        return

    await datamodel.entry_delete(
        update, context,
        db.authors_list,
        db.by_author,
        db.delete,
        "voice", "дискографии"
    )

####################
# /voicelist       #
####################

async def voicelist_show(update, context):
    """Команда показа списка голосовых сообщений."""
    out_message = _voicelist_show_text(update.effective_chat.id, 0, 0)
    markup = _voicelist_show_keyboard(
        update.effective_chat.id, 0, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)

async def voicelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /voicelist."""
    await kbrd.callback(update, context,
                        _voicelist_show_text,
                        _voicelist_show_keyboard)

def _voicelist_show_text(chat_id, author_num, page):
    """Возвращает текст сообщения /voicelist"""
    e = kbrd.get_text(chat_id, author_num, page,
                      db.authors_list,
                      db.by_author,
                      "Список голосовых сообщений")
    return e

def _voicelist_show_keyboard(chat_id, author_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.show_keyboard(chat_id, author_num, page, user_id,
                           db.authors_list,
                           db.by_author,
                           "voicelist")
    return e
