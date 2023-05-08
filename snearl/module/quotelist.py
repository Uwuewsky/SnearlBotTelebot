"""
Модуль для сохранения сообщений в изображения.
Позволяет сохранять цитаты через команды,
а затем отправлять в чат через поиск инлайн.
"""

from telegram import InlineQueryResultCachedSticker
from telegram.ext import CommandHandler, CallbackQueryHandler

from snearl.module import utils
from snearl.instance import app, help_messages

import snearl.module.authormodel as datamodel
import snearl.module.authormodel_kbrd as kbrd
from snearl.module.quotelist_db import db
import snearl.module.quotelist_draw as drawing

####################
# main             #
####################

def main():
    db.create_table()
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

    # коллбек /quotelist
    app.add_handler(CallbackQueryHandler(
        quotelist_show_callback,
        pattern="^quotelist"))

####################
# inline functions #
####################

def quote_search(query, offset, limit):
    return db.search(query, offset, limit)

def quote_query_result(i, e):
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

    if await utils.check_access(update):
        return

    message = update.message.reply_to_message
    args = context.args

    if not message:
        await update.message.reply_text(
            "Нужно отправить команду ответом на сообщение.")
        return

    # переменные для рисования цитаты
    quote_text = utils.get_description(message)
    quote_nickname = utils.get_sender_title_short(message)
    quote_avatar = await utils.get_avatar(message)
    quote_picture = await utils.get_picture(message)

    if not (quote_text or quote_picture):
        await update.message.reply_text(
            "Цитируемое сообщение должно содержать "\
            "либо текст, либо фото или стикер.")
        return

    # имя автора записи в бд
    file_author = utils.validate(quote_nickname)
    if args and not file_author:
        file_author = utils.validate(args[0])
        args = args[1:]

    if not file_author:
        await update.message.reply_markdown_v2(
            "Введите имя вручную, например\:\n"\
            "`/quote_add Эрл`")
        return

    # описание записи в бд
    file_desc = utils.validate(quote_text)
    if args and not file_desc:
        file_desc = utils.validate(" ".join(context.args))

    if not file_desc:
        await update.message.reply_markdown_v2(
            "Введите описание вручную, например\:\n"\
            "`/quote_add Продал все приставки`")
        return

    # сам файл цитаты в виде BytesIO
    try:
        quote_img = drawing.draw_quote(quote_nickname, quote_avatar,
                                       quote_text, quote_picture)
    except Exception:
        await update.message.reply_text(
            "Данный тип сообщений не поддерживается.")
        return

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

    # добавляем в базу данных
    db.create_table()
    db.add(chat_id, file_id,
           file_author, file_desc,
           quote_img.getbuffer())
    db.con.commit()

    # закрыть последний оставшийся BytesIO
    quote_img.close()

    await update.message.reply_text(
        f"В сборник афоризмов {file_author} успешно добавлено {file_desc}")

####################
# /quote_delete    #
####################

async def quote_delete(update, context):
    """Команда удаления цитаты."""
    await datamodel.entry_delete(
        update, context,
        db.authors_list,
        db.by_author,
        db.delete,
        "quote", "сборника афоризмов"
    )

####################
# /quotelist       #
####################

async def quotelist_show(update, context):
    """Команда показа списка цитат."""
    out_message = _quotelist_show_text(update.effective_chat.id, 0, 0)
    markup = _quotelist_show_keyboard(
        update.effective_chat.id, 0, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)

async def quotelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /quotelist."""
    await kbrd.callback(update, context,
                        _quotelist_show_text,
                        _quotelist_show_keyboard)

def _quotelist_show_text(chat_id, author_num, page):
    """Возвращает текст сообщения /quotelist"""
    e = kbrd.get_text(chat_id, author_num, page,
                      db.authors_list,
                      db.by_author,
                      "Список цитат")
    return e

def _quotelist_show_keyboard(chat_id, author_num, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.show_keyboard(chat_id, author_num, page, user_id,
                           db.authors_list,
                           db.by_author,
                           "quotelist")
    return e
