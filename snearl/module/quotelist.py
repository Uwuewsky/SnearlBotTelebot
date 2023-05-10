"""
Модуль для сохранения сообщений в изображения.
Позволяет сохранять цитаты через команды,
а затем отправлять в чат через поиск инлайн.
"""

from telegram import InlineQueryResultCachedSticker
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters)

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
    app.add_handler(CommandHandler("quote_delete", quote_delete))
    app.add_handler(CommandHandler("quotelist", quotelist_show))

    app.add_handler(ConversationHandler(
        entry_points = [CommandHandler("quote_add", quote_start)],
        states = {
            0: [MessageHandler(filters.ALL & ~filters.Regex("^отмена$"), quote_receive)],
            1: [MessageHandler(filters.ALL & ~filters.Regex("^отмена$"), quote_get_info)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, quote_end)]
        },
        fallbacks = [MessageHandler(filters.Regex("^отмена$"), quote_end)],
        conversation_timeout = 120), group=4)

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

# Start
############

async def quote_start(update, context):
    """Начало команды цитирования."""

    if await utils.check_access(update):
        return ConversationHandler.END

    # создать пользователю список сообщений
    context.user_data["quote_messages"] = []
    context.user_data["quote_cluster"] = None
    context.user_data["quote_author"] = None
    context.user_data["quote_desc"] = None

    # если команда отправлена ответом на сообщение,
    # создать цитату из него одного
    if m := update.message.reply_to_message:
        status = await quote_create(update, context, [m])
        return status

    # ждать новых сообщений через ConversationHandler
    await update.message.reply_markdown_v2(
        "Теперь отправьте до 10 сообщений чтобы сделать из них цитату\.\.\.\n\n"\
        "_Напишите `готово` чтобы закончить отправку и создать цитату "\
        "или `отмена` чтобы отменить создание цитаты_")
    return 0 # stage 0

# Stage 0
############

async def quote_receive(update, context):
    """Получение сообщения для цитаты."""

    # все отправленные сообщения
    messages = context.user_data["quote_messages"]

    # если пришло цитируемое сообщение
    if not (update.message.text
            and update.message.text.lower() == "готово"):
        # добавить сообщение в список
        messages.append(update.message)

        # если сообщений меньше лимита, то ожидать еще
        if len(messages) < 10:
            return 0

    # очистить данные пользователя о цитате
    if "quote_messages" in context.user_data:
        del context.user_data["quote_messages"]

    # создать цитату и закончить разговор
    status = await quote_create(update, context, messages)
    return status

# Stage 1
############

async def quote_get_info(update, context):
    """
    Функция получения имени автора/описания
    если их нельзя извлечь из сообщения
    """
    # взять из текста сообщения
    if not context.user_data["quote_author"]:
        context.user_data["quote_author"] = utils.validate(
        utils.get_sender_title_short(update.message))

    elif not context.user_data["quote_desc"]:
        context.user_data["quote_desc"] = utils.validate(
        utils.get_description(update.message))

    # проверить наличие имени автора и описания
    # если нет, то ждать ввода от пользователя
    if res := await _quote_check_info(update, context):
        return res # stage 1

    status = await quote_add(update, context)
    return status

# Cancel
############

async def quote_end(update, context):
    """Отмена команды цитирования."""

    context.user_data.clear()
    await update.message.reply_text("Создание цитаты отменено.")
    return ConversationHandler.END

# Create
############

async def quote_create(update, context, messages):
    """Команда создания новой цитаты."""

    # выборка необходимых данных
    data = await _quote_get_message_data(messages)
    context.user_data["quote_author"] = data[0]
    context.user_data["quote_desc"] = data[1]
    cluster_list = data[2]

    if not cluster_list:
        await update.message.reply_text(
            "Для данных сообщений нельзя создать цитату.")
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["quote_cluster"] = cluster_list

    # проверить наличие имени автора и описания
    # если нет, то ждать ввода от пользователя
    if res := await _quote_check_info(update, context):
        return res # stage 1

    status = await quote_add(update, context)
    return status

async def quote_add(update, context):
    """Загружает цитату в чат и БД"""

    # рисуем саму цитату
    # файл в виде BytesIO
    try:
        quote_img = drawing.draw_quote(
            context.user_data["quote_cluster"])
    except:
        await update.message.reply_text(
            "Данный тип сообщений не поддерживается.")
        context.user_data.clear()
        return ConversationHandler.END

    # отправляем цитату в чат
    quote_reply = await update.message.reply_sticker(quote_img.getvalue())

    # выгружаем данные из пользователя
    file_author = context.user_data["quote_author"]
    file_desc = context.user_data["quote_desc"]

    # добавляем в базу данных
    db.create_table()
    db.add(update.effective_chat.id,
           quote_reply.sticker.file_id,
           file_author, file_desc,
           quote_img.getbuffer())
    db.con.commit()

    await update.message.reply_text(
        f"В сборник афоризмов {file_author} успешно добавлено {file_desc}")

    # очистить данные пользователя
    context.user_data.clear()
    return ConversationHandler.END

# Вспомогательные функции
###########################

async def _quote_check_info(update, context):
    """Проверяет наличие имени автора и описания."""

    # если автора или описания нет, то
    # ждем пока пользователь их введет
    s = None
    if not context.user_data["quote_author"]:
        s = "имя автора"
    elif not context.user_data["quote_desc"]:
        s = "описание"
    if not s:
        return None

    await update.message.reply_text(
        f"Напишите {s} для этой цитаты.")
    return 1 # stage 1

async def _quote_get_message_data(messages):
    """Извлекает нужные данные из сообщений."""

    file_author = None
    file_desc = None
    cluster_list = []

    for message in messages:
        # переменные для цитаты
        message_user_id = utils.get_sender_id(message)
        message_username = utils.get_sender_username(message)
        message_nickname = utils.get_sender_title_short(message)
        message_text = utils.get_description(message)
        message_picture = await utils.get_picture(message)

        # переменные для записи в бд
        # записать первое доступное значение
        if not file_author:
            file_author = utils.validate(message_nickname)
        if not file_desc:
            file_desc = utils.validate(message_text)

        # пропустить сообщение с недопустимым контентом
        if not (message_text or message_picture):
            continue

        # если последнее сообщение принадлежит этому же юзеру
        # то вместо создания еще одного кластера сообщений
        # загружаем контент в него
        #
        # cave-in: репосты от двух пользователей с одинаковыми никами
        # без юзернеймов и со скрытыми аккаунтами
        # считаются сообщениями от одного пользователем
        last_quote = cluster_list[-1] if cluster_list else None

        if (last_quote
            and last_quote["nickname"] == message_nickname
            and last_quote["username"] == message_username
            and last_quote["user_id"] == message_user_id):

            if message_picture:
                last_quote["content"].append(("pic", message_picture))
            if message_text:
                last_quote["content"].append(("txt", message_text))
            continue

        # загрузить аватар
        message_avatar = await utils.get_avatar(message)

        # объект для рисования цитаты
        # представляет собой сообщения
        # подряд от одного юзера
        cluster = {
            "user_id": message_user_id,   # не отрисовывается
            "username": message_username, # не отрисовывается
            "nickname": message_nickname,
            "avatar": message_avatar,
            "content": []
        }

        if message_picture:
            cluster["content"].append(("pic", message_picture))
        if message_text:
            cluster["content"].append(("txt", message_text))

        # пропустить сообщение без контента
        if cluster["content"]:
            cluster_list.append(cluster)

    return (file_author, file_desc, cluster_list)

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
