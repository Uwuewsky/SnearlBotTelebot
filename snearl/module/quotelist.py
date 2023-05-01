"""
Модуль для сохранения сообщений в изображения.
Позволяет сохранять цитаты через команды,
а затем отправлять в чат через поиск инлайн.
"""

import io, re, textwrap

from telegram import InlineQueryResultCachedSticker
from telegram.ext import (
    InlineQueryHandler, CommandHandler, CallbackQueryHandler
)

import snearl.module.utils as utils
import snearl.module.keyboard as kbrd
import snearl.module.quotelist_db as db
import snearl.module.quotelist_draw as drawing
from snearl.instance import app, help_messages

####################
# main             #
####################

def main():
    db.quotelist_create_table()
    db.con.commit()

    help_messages.append("""
*Хранить и отправлять стикеры\-цитаты инлайн*
  a\. Добавить цитату:
      `/quote_add [ИмяАвтора] [КраткоеОписание]`;
  b\. Открыть инлайн список цитат:
      `@SnearlBot [ТекстЗапроса]`;
      Запросом может быть _имя автора_ или _строка из описания_;
  c\. Удалить цитату:
      `/quote_delete [ИмяАвтора] [НомерЦитаты]`;
  d\. Список цитат: /quotelist;
""")

    # команды
    app.add_handler(CommandHandler("quote_add", quote_add))
    app.add_handler(CommandHandler("quote_delete", quote_delete))
    app.add_handler(CommandHandler("quotelist", quotelist_show))

    # инлайн
    app.add_handler(CallbackQueryHandler(
        quotelist_show_callback,
        pattern="^quotelist"))

    return

####################
# inline functions #
####################

def quote_inline_query(i, e):
    """Функция возвращающая InlineQueryResult."""
    return InlineQueryResultCachedSticker(
        id=str(i),
        sticker_file_id = e[1]
        )

####################
# /quote_add       #
####################

async def quote_add(update, context):
    """Команда добавления новой цитаты."""

    msg = update.message.reply_to_message

    if await utils.check_access(update):
        return

    if msg is None:
        await update.message.reply_text(
            "Нужно отправить команду ответом на сообщение.")
        return

    if (msg.text is None
        and msg.sticker is None
        and not msg.photo):

        await update.message.reply_text(
            "Цитируемое сообщение должно содержать "\
            "либо текст, либо фото или стикер.")
        return

    if not msg.text and not context.args:
        await update.message.reply_markdown_v2(
            "Нужно указать описание, например:\n"\
            "`/quote_add Ну шо вы ребятки`")
        return

    # переменные для рисования цитаты
    quote_text = _quote_get_msg_text(msg)
    quote_nickname = _quote_get_msg_nickname(msg)
    quote_avatar = await _quote_get_msg_avatar(msg)
    quote_picture = await _quote_get_msg_picture(msg)

    # сам файл цитаты в виде BytesIO
    quote_img = io.BytesIO()
    drawing.quote_draw(quote_img, quote_nickname,
                       quote_avatar, quote_text, quote_picture)

    # эти файлы тоже BytesIO, закрываем их
    if quote_avatar:
        quote_avatar.close()
    if quote_picture:
        quote_picture.close()

    # отправляем цитату в чат и берем ее file_id
    quote_reply = await update.message.reply_sticker(quote_img.getvalue())

    # переменные для БД
    chat_id = update.effective_chat.id
    file_id = quote_reply.sticker.file_id
    if msg.text:
        file_desc = textwrap.shorten(msg.text, width=50, placeholder="...")
    else:
        file_desc = " ".join(context.args)[:50]

    # добавляем в базу данных
    db.quotelist_create_table()
    db.quotelist_add(chat_id, file_id,
                     quote_nickname, file_desc,
                     quote_img.getbuffer())
    db.con.commit()

    # закрыть последний оставшийся BytesIO
    quote_img.close()

    await update.message.reply_text(
        f"В сборник афоризмов {quote_nickname} успешно добавлен {file_desc}")
    return

###################
# Функции-геттеры #
###################

def _quote_get_msg_nickname(msg):
    if msg.forward_from:
        n =  msg.forward_from.full_name
    elif msg.forward_sender_name:
        n =  msg.forward_sender_name 
    elif msg.from_user:
        n = msg.from_user.full_name
    return textwrap.shorten(n, width=35, placeholder="...")

def _quote_get_msg_text(msg):
    if msg.text:
        return "\n".join(textwrap.wrap(msg.text, width=35, max_lines=15))
    return None

async def _quote_get_msg_picture(msg):
    quote_picture = None
    file_id = None

    if msg.photo:
        file_id = msg.photo[-1].file_id
    if msg.sticker:
        file_id = msg.sticker.file_id

    if file_id:
        quote_picture = io.BytesIO()
        f = await app.bot.get_file(file_id)
        await f.download_to_memory(quote_picture)

    return quote_picture

async def _quote_get_msg_avatar(msg):
    quote_avatar = None
    pl = None

    if msg.forward_from:
        pl = await msg.forward_from.get_profile_photos(limit=1)
    elif msg.from_user and not msg.forward_date:
        pl = await msg.from_user.get_profile_photos(limit=1)

    if pl and pl.total_count > 0:
        p = pl.photos[0][0]
        quote_avatar = io.BytesIO()
        f = await app.bot.get_file(p.file_id)
        await f.download_to_memory(quote_avatar)
    return quote_avatar

####################
# /quote_delete    #
####################

async def quote_delete(update, context):
    """Команда удаления цитаты."""
    if await utils.check_access(update):
        return

    try:
        chat_id = update.effective_chat.id
        file_author = context.args[0]
        file_num = int(context.args[1]) - 1

        # взять цитату по указанному в команде номеру
        l = db.quotelist_by_author(chat_id, file_author)
        if file_num < 0 or file_num > len(l) - 1:
            raise Exception

        entry = l[file_num]
        file_id, file_desc = entry[1], entry[3]

        db.quotelist_delete(file_id)
        db.con.commit()

    except Exception as e:
        await update.message.reply_markdown_v2(
            f"{e}\nНужно указать имя автора цитаты и "\
            "номер сообщения из /quotelist, например:\n"\
            "`/quote_delete Эрл 15`\n"\
            "Учтите, что имя чувствительно к регистру\.")
        return

    await update.message.reply_text(
        f"Из сборника афоризмов {file_author} успешно удален {file_desc}")
    return

####################
# /quotelist       #
####################

async def quotelist_show(update, context):
    """Команда показа списка цитат."""
    out_message = _quotelist_show_text(update.effective_chat.id, 0, 0)
    markup = _quotelist_show_keyboard(
        update.effective_chat.id, 0, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)
    return

async def quotelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /quotelist."""
    await kbrd.authorlist_show_callback(update, context,
                                        _quotelist_show_text,
                                        _quotelist_show_keyboard)
    return

def _quotelist_show_text(chat_id, author_num, page):
    """Возвращает текст сообщения /quotelist"""
    e = kbrd.authorlist_show_text(chat_id, author_num, page,
                                  db.quotelist_authors_list,
                                  db.quotelist_by_author,
                                  "Список цитат")
    return e

def _quotelist_show_keyboard(chat_id, author_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.authorlist_show_keyboard(chat_id, author_num, page, user_id,
                                      db.quotelist_authors_list,
                                      db.quotelist_by_author,
                                      "quotelist")
    return e
