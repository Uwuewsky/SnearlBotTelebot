"""
Модуль для сохранения сообщений в изображения.
Позволяет сохранять цитаты через команды,
а затем отправлять в чат через поиск инлайн.
"""

import random
from datetime import datetime, timezone

from telegram import (
    InlineQueryResultCachedSticker,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters)

from snearl.module import utils
from snearl.module import userlist_db
from snearl.instance import app, help_messages

import snearl.module.authormodel as datamodel
import snearl.module.authormodel_kbrd as kbrd
from snearl.module.quotelist_db import db
import snearl.module.quotelist_draw as drawing
from snearl.module import userlist_db

####################
# main             #
####################

def main():
    help_messages.append("""
*Хранить и отправлять стикеры\-цитаты инлайн*
  a\. Добавить цитату:
      /q;
  b\. Открыть инлайн список цитат:
      `@SnearlBot ц [ТекстЗапроса]`;
      Запросом может быть _имя автора_ или _строка из описания_;
  c\. Удалить цитату:
      `/quote_delete [НомерАвтора] [НомерЦитаты]`;
  d\. Список цитат: /quotelist;
  e\. Частота случайных цитат: /quote\_random;
""")

    # команды
    app.add_handler(CommandHandler("quote_delete", quote_delete))
    app.add_handler(CommandHandler("quotelist", quotelist_show))
    app.add_handler(CommandHandler("quote_random", quote_frequency))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), send_random_quote))

    app.add_handler(ConversationHandler(
        entry_points = [CommandHandler("q", quote_start)],
        states = {
            0: [MessageHandler(filters.FORWARDED | filters.Regex("^[Гг]отово$"),
                               quote_receive)],
            1: [MessageHandler(filters.ALL & ~filters.Regex("^[Оо]тмена$"),
                               quote_get_info)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL,
                                                         quote_cancel)]
        },
        fallbacks = [MessageHandler(filters.Regex("^[Оо]тмена$"), quote_cancel)],
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

    """ if await utils.check_access(update):
        return ConversationHandler.END """

    # создать пользователю список сообщений
    context.user_data.clear()
    # список собственных сообщений для удаления
    context.user_data["quote_delete"] = []
    # список сообщений-репостов для цитаты
    context.user_data["quote_messages"] = []
    context.user_data["quote_user_title"] = None
    context.user_data["quote_user_name"] = None
    context.user_data["quote_cluster"] = None
    context.user_data["quote_desc"] = None

    # если команда отправлена ответом на сообщение,
    # создать цитату из него одного
    if m := update.message.reply_to_message:
        status = await quote_create(update, context, [m])
        return status

    # ждать новых сообщений через ConversationHandler
    help_msg = await update.message.reply_markdown_v2(
        "Теперь отправьте до 10 сообщений чтобы сделать из них цитату\.\n\n"\
        "_Напишите `Готово` чтобы закончить отправку и создать цитату "\
        "или `Отмена` чтобы отменить создание цитаты_",
    # создать клавиатуру пользователю
    reply_markup = ReplyKeyboardMarkup.from_row(
        ["Готово", "Отмена"],
        resize_keyboard = True,
        one_time_keyboard = True,
        selective = True))

    context.user_data["quote_delete"].append(help_msg)

    return 0 # stage 0

# Stage 0
############

async def quote_receive(update, context):
    """Получение сообщения для цитаты."""

    # все отправленные сообщения
    messages = context.user_data["quote_messages"]

    # если пришло цитируемое сообщение
    if not update.message.text in ["Готово", "готово"]:
        # добавить сообщение в список
        messages.append(update.message)

        # если сообщений меньше лимита, то ожидать еще
        if len(messages) < 10:
            return 0

    context.user_data["quote_delete"].append(update.message)

    # создать цитату и закончить разговор
    status = await quote_create(update, context, messages)
    return status

# Stage 1
############

async def quote_get_info(update, context):
    """
    Функция получения имени автора/описания
    если их нельзя извлечь из сообщения.
    """
    # взять из текста сообщения
    if not context.user_data["quote_user_title"]:
        context.user_data["quote_user_title"] = utils.validate(
        utils.get_full_description(update.message))

    elif not context.user_data["quote_desc"]:
        context.user_data["quote_desc"] = utils.validate(
        utils.get_full_description(update.message))

    # проверить наличие имени автора и описания
    # если нет, то ждать ввода от пользователя
    if res := await _quote_check_info(update, context):
        return res # stage 1

    status = await quote_add(update, context)
    return status

# Cancel
############

async def quote_cancel(update, context):
    """Отмена команды цитирования."""

    await update.message.reply_text(
        "Создание цитаты отменено.",
        reply_markup=ReplyKeyboardRemove())

    context.user_data["quote_messages"].append(update.message)

    return (await quote_end(update, context))

async def quote_end(update, context):
    """Завершение команды цитирования"""

    for m in context.user_data["quote_delete"]:
        try:
            await m.delete()
        except Exception:
            pass
    for m in context.user_data["quote_messages"]:
        try:
            await m.delete()
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END

# Create
############

async def quote_create(update, context, messages):
    """Команда создания новой цитаты."""

    # выборка необходимых данных
    data = await _quote_get_message_data(messages)
    context.user_data["quote_user_name"] = data[0]
    context.user_data["quote_user_title"] = data[1]
    context.user_data["quote_desc"] = data[2]
    cluster_list = data[3]

    if not cluster_list:
        await update.message.reply_text(
            "Для данных сообщений нельзя создать цитату.",
            reply_markup=ReplyKeyboardRemove())
        return (await quote_end(update, context))

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
    except Exception:
        await update.message.reply_text(
            "Данный тип сообщений не поддерживается.",
            reply_markup=ReplyKeyboardRemove())
        return (await quote_end(update, context))

    # отправляем цитату в чат
    quote_reply = await update.message.reply_sticker(
        quote_img.getvalue(),
        reply_markup=ReplyKeyboardRemove())

    # выгружаем данные из пользователя
    user_title = context.user_data["quote_user_title"]
    user_name = context.user_data["quote_user_name"]
    file_desc = context.user_data["quote_desc"]

    # добавляем в базу данных
    db.create_table()
    db.add(update.effective_chat.id,
           quote_reply.sticker.file_id,
           user_name, user_title,
           file_desc, quote_img.getbuffer())
    userlist_db.update(user_name, user_title)
    db.con.commit()

    # стикер уже отправлен как сообщение о добавлении
    # await update.message.reply_text(
    #     f"В сборник афоризмов {user_title} успешно добавлено {file_desc}")

    return (await quote_end(update, context))

# Вспомогательные функции
###########################

async def _quote_check_info(update, context):
    """Проверяет наличие имени автора и описания."""

    # если автора или описания нет, то
    # ждем пока пользователь их введет
    s = None

    if not context.user_data["quote_desc"]:
        s = "описание"

    if not context.user_data["quote_user_title"]:

        if res := userlist_db.find(
            context.user_data["quote_user_name"],
            context.user_data["quote_user_title"]):

            context.user_data["quote_user_title"] = res[2]
        else:
            s = "имя автора"

    if not s:
        return None

    msg = await update.message.reply_text(
        f"Теперь напишите {s} для этой цитаты.")

    context.user_data["quote_delete"].append(msg)

    return 1 # stage 1

async def _quote_get_message_data(messages):
    """Извлекает нужные данные из сообщений."""

    user_title = None
    user_name = None
    file_desc = None
    cluster_list = []

    for message in messages:
        # переменные для цитаты
        message_user_id = utils.get_sender_id(message)
        message_user_name = utils.get_sender_username(message)
        message_user_title = utils.get_sender_title_short(message)
        message_text = utils.get_description(message)
        message_picture = await utils.get_picture(message)

        # переменные для записи в бд
        # записать первое доступное значение
        if not (user_name and user_title):
            user_name = utils.validate(message_user_name)
            user_title = utils.validate(message_user_title)
        if not file_desc:
            file_desc = utils.validate(utils.get_full_description(message))

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
            and last_quote["user_title"] == message_user_title
            and last_quote["user_name"] == message_user_name
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
            "user_name": message_user_name, # не отрисовывается
            "user_title": message_user_title,
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

    return (user_name, user_title, file_desc, cluster_list)

####################
# random quotes    #
####################

async def send_random_quote(update, context):

    # дефолтная вероятность прислать случайный стикер в чат
    frequency = context.chat_data.get("quote_random", 1)
    # время, прошедшее с последних апдейтов. Нужно для того,
    # чтобы предотвратить ответы на слишком старые сообщения
    dateOld = update.message.date
    dateNow = datetime.now(timezone.utc)
    timedelta = dateNow-dateOld

    if frequency == 0:
        return
    
    if (timedelta.seconds) > 10:
        return

    r = random.randint(1, 100)
    if r <= frequency:
        random_quote = db.get_random_file(update.message.chat_id)
        if random_quote:
            await update.message.reply_sticker(random_quote)
    return

async def quote_frequency(update, context):

    current_frequency = context.chat_data.get("quote_random", 1)
    if not context.args:
        await update.message.reply_markdown_v2(
            f"Текущая вероятность: {current_frequency}%\.\n"\
            "Изменить: `/quote_random [0-100]`")
        return

    if await utils.check_access(update):
        return

    try:
        frequency = int(context.args[0])
        if 0 <= frequency <= 100:
            context.chat_data["quote_random"] = frequency
            await update.message.reply_text(
                f"Частота ответов теперь {frequency}%.")
        else:
            await update.message.reply_text(
                "Частота должна быть между 0 и 100.")
    except:
        await update.message.reply_markdown_v2(
        "Введите корректную частоту ответов в процентах\.\n"\
        "Например, `/quote_random 20`")

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
