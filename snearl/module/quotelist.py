"""
Модуль для сохранения сообщений в изображения.
Позволяет сохранять цитаты через команды,
а затем отправлять в чат через поиск инлайн.
"""

import random
import datetime

from telegram import InlineQueryResultCachedSticker
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters)

from snearl.module import utils
from snearl.module import utils_media
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
      Ответить на сообщение командой /q;
      Переслать несколько сообщений, одновременно введя в поле сообщения /q;

  b\. Открыть инлайн список цитат:
      `@SnearlBot ц [ТекстЗапроса]`;
      Запросом может быть _имя автора_ или _строка из описания_;

  c\. Удалить цитату:
      `/quote_delete <НомерАвтора> <НомерЦитаты>`;

  d\. Список цитат: /quotelist;

  e\. Частота случайных цитат: /quote\_random;
""")

    # команды
    app.add_handler(CommandHandler("quote_delete", quote_delete))
    app.add_handler(CommandHandler("quotelist", quotelist_show))
    app.add_handler(CommandHandler("quote_random", quote_frequency))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND),
                                   send_random_quote))

    app.add_handler(ConversationHandler(
        entry_points = [CommandHandler("q", quote_start)],
        states = {
            0: [MessageHandler(filters.FORWARDED, quote_receive)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL,
                                                         quote_timeout)]
        },
        fallbacks = [MessageHandler(filters.ALL, quote_cancel)],
        conversation_timeout = 1), group=4)

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
    # сообщение пользователя с командой
    context.user_data["quote_command"] = update.message
    # описание цитаты из аргументов после команды
    context.user_data["quote_desc"] = " ".join(context.args) or None

    # если команда отправлена ответом на сообщение,
    # создать цитату из него одного
    if m := update.message.reply_to_message:
        # Сообщение при попытке ввести \q с номером
        try:
            int(context.args[0])
            await update.message.reply_text(
                "Для создания множественной цитаты выделите нужные "\
                "сообщения и перешлите в чат одновременно с командой /q.")
        except Exception:
            pass

        return (await quote_create(update, context, [m]))

    return 0 # stage 0

# Stage 0
############

async def quote_receive(update, context):
    """Получение сообщения для цитаты."""

    messages = context.user_data["quote_messages"]
    messages.append(update.message)

    # если сообщений меньше лимита, то ожидать еще
    if len(messages) < 10:
        return 0

    # иначе создать цитату и закончить разговор
    return (await quote_create(update, context, messages))

# Timeout
############

async def quote_timeout(update, context):
    """Таймаут команды цитирования."""

    # если есть сообщения для цитаты, то создать ее
    if messages := context.user_data["quote_messages"]:
        return (await quote_create(update, context, messages))

    # иначе отмена
    return (await quote_cancel(update, context))

# Cancel
############

async def quote_cancel(update, context):
    """Отмена команды цитирования."""

    await context.user_data["quote_command"].reply_text(
        "Чтобы создать цитату:\n\n"\
        "a. Отправьте команду /q ответом на сообщение.\n"\
        "b. Либо перешлите до 10 сообщений в чат ОДНОВРЕМЕННО с командой /q.")

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
    user_name = data[0]
    user_title = data[1]
    file_desc = context.user_data["quote_desc"] or data[2]
    cluster_list = data[3]

    if not cluster_list:
        await context.user_data["quote_command"].reply_text(
            "Для данных сообщений нельзя создать цитату.")
        return (await quote_end(update, context))

    # рисуем саму цитату
    # файл в виде BytesIO
    try:
        quote_img = drawing.draw_quote(cluster_list)
    except Exception:
        await context.user_data["quote_command"].reply_text(
            "Данный тип сообщений не поддерживается.")
        return (await quote_end(update, context))

    # отправляем цитату в чат
    quote_reply = await context.user_data["quote_command"].reply_sticker(
        quote_img.getvalue())

    # проверить наличие описания
    if not file_desc:
        file_desc = "Без названия"

        # назвать запись "Без названия 2" и т.д.
        if nameless_list := db.search_by_author(user_title, file_desc):
            file_num = 1
            claimed_names = [i[4] for i in nameless_list]

            for i in claimed_names:
                if not file_desc in claimed_names:
                    break
                file_num += 1
                file_desc = f"Без названия {file_num}"

        await quote_reply.reply_markdown_v2(
            f"Эта цитата сохранена как «{file_desc}»\. "\
            "Описание можно ввести вручную, например:\n"\
            "`/q Компромат`")

    # добавляем в базу данных
    db.add(update.effective_chat.id,
           quote_reply.sticker.file_id,
           user_name, user_title,
           file_desc, quote_img.getbuffer())
    userlist_db.update(user_name, user_title)
    db.con.commit()

    # стикер уже отправлен как сообщение о добавлении
    # await context.user_data["quote_command"].reply_text(
    #     f"В сборник афоризмов {user_title} успешно добавлено {file_desc}")

    return (await quote_end(update, context))

# Вспомогательные функции
###########################

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
        message_picture = await utils_media.get_picture(message)

        # переменные для записи в бд
        # записать первое доступное значение
        if not (user_name and user_title):
            user_name = message_user_name
            user_title = utils.get_sender_title(message)
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
        message_avatar = await utils_media.get_avatar(message)

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

    # время, прошедшее с последних апдейтов. Нужно для того,
    # чтобы предотвратить ответы на слишком старые сообщения
    try:
        date_now = datetime.datetime.now(datetime.timezone.utc)
        timedelta = date_now - update.message.date
        if -15 * 60 > timedelta.total_seconds() > 15 * 60:
            return
    except Exception:
        return

    # дефолтная вероятность прислать случайный стикер в чат
    frequency = context.chat_data.get("quote_random", 1)

    if frequency == 0:
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
    except Exception:
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
        db.authors_names_list,
        db.by_author,
        db.delete,
        "quote", "сборника афоризмов"
    )

####################
# /quotelist       #
####################

async def quotelist_show(update, context):
    """Команда показа списка цитат."""

    # Пробуем взять цифру после команды
    try:
        author_num = int(context.args[0]) - 1
    except Exception:
        author_num = 0

    # Берем имя автора после команды
    author_name = " ".join(context.args)

    out_message = _quotelist_show_text(
        update.effective_chat.id, author_num, 0, author_name)
    markup = _quotelist_show_keyboard(
        update.effective_chat.id, author_num, 0,
        update.effective_user.id, author_name)

    msg = await update.message.reply_text(out_message, reply_markup=markup)

    utils.schedule_delete_message(context, "quote_list_delete", msg)

async def quotelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /quotelist."""
    await kbrd.callback(update, context,
                        _quotelist_show_text,
                        _quotelist_show_keyboard)

def _quotelist_show_text(chat_id, author_num, page, author_name = None):
    """Возвращает текст сообщения /quotelist"""
    e = kbrd.get_text(chat_id, author_num, page,
                      db.authors_names_list,
                      db.by_author,
                      "Список цитат",
                      author_name)
    return e

def _quotelist_show_keyboard(chat_id, author_num, page,
                             user_id, author_name = None):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.show_keyboard(chat_id, author_num, page, user_id,
                           db.authors_names_list,
                           db.by_author,
                           "quotelist",
                           author_name)
    return e

