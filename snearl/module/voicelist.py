"""
Модуль для голосовых сообщений.
Позволяет сохранять войсы через команды,
а затем отправлять в чат через поиск инлайн.
"""

from telegram import (
    InlineQueryResultCachedVoice,
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
from snearl.module.voicelist_db import db
from snearl.module import userlist_db

####################
# main             #
####################

def main():
    help_messages.append("""
*Хранить и отправлять инлайн списки голосовых сообщений*
  a\. Добавить войс:
      /v;
  b\. Открыть инлайн список войсов:
      `@SnearlBot в [ТекстЗапроса]`;
      Запросом может быть _имя автора_ или _строка из описания_;
  c\. Удалить войс:
      `/voice_delete [НомерАвтора] [НомерВойса]`;
  d\. Список войсов: /voicelist;
""")

    # команды
    app.add_handler(CommandHandler("voice_delete", voice_delete))
    app.add_handler(CommandHandler("voicelist", voicelist_show))

    app.add_handler(ConversationHandler(
        entry_points = [CommandHandler("v", voice_start)],
        states = {
            1: [MessageHandler(filters.ALL & ~filters.Regex("^[Оо]тмена$"),
                               voice_get_info)],
            2: [MessageHandler(filters.Regex("^[Аа]втор$"), voice_get_info)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL,
                                                         voice_cancel)]
        },
        fallbacks = [MessageHandler(filters.Regex("^[Оо]тмена$"), voice_cancel)],
        conversation_timeout = 30), group=3)

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
        title=f"{e[3] or e[2]} — {e[4]}",
        # текстовые подписи вида
        # "Автор - Описание войса"
        # убраны по умолчанию
        # caption=f"{e[2]} — {e[3]}"
    )

####################
# /voice_add       #
####################

# Start
############

async def voice_start(update, context):
    """Команда добавления нового голосового сообщения."""

    if await utils.check_access(update):
        return ConversationHandler.END

    message = update.message.reply_to_message

    if not message:
        await update.message.reply_text(
            "Нужно отправить команду ответом на голосовое сообщение.")
        return ConversationHandler.END

    if not message.voice:
        await update.message.reply_text("Это не голосовое сообщение.")
        return ConversationHandler.END

    file_id = message.voice.file_id

    if db.get(file_id):
        await update.message.reply_text(
            "Это голосовое сообщение уже в списке.")
        return ConversationHandler.END

    # создать пользователю данные войса
    file_desc = utils.validate(" ".join(context.args))
    user_title = utils.validate(utils.get_sender_title_short(message))
    user_name = utils.validate(utils.get_sender_username(message))

    context.user_data.clear()
    # список сообщений для удаления в конце команды
    context.user_data["voice_delete"] = []
    context.user_data["voice_user_name"] = user_name
    context.user_data["voice_user_title"] = user_title
    context.user_data["voice_desc"] = file_desc
    context.user_data["voice_id"] = file_id

    # проверить наличие имени автора и описания
    # если нет, то ждать ввода от пользователя
    if res := await _voice_check_info(update, context):
        return res # stage 1

    return (await voice_add(update, context))

# Add
############

async def voice_add(update, context):
    """Команда добавления нового голосового сообщения."""
    chat_id = update.effective_chat.id
    file_id = context.user_data["voice_id"]
    file_desc = context.user_data["voice_desc"]
    user_name = context.user_data["voice_user_name"]
    user_title = context.user_data["voice_user_title"]

    # скачиваем войс и добавляем в БД
    file_blob = await utils.download_file(file_id)
    db.create_table()
    db.add(chat_id, file_id,
           user_name, user_title,
           file_desc, file_blob.getbuffer())
    userlist_db.update(user_name, user_title)
    db.con.commit()
    file_blob.close()

    await update.message.reply_text(
        f"В дискографию {user_title} успешно добавлено {file_desc}",
        reply_markup=ReplyKeyboardRemove())
    return (await voice_end(update, context))

# Stage 1
############

async def voice_get_info(update, context):
    """
    Функция получения имени автора/описания
    если их нельзя извлечь из сообщения
    """

    context.user_data["voice_delete"].append(update.message)

    # взять из текста сообщения
    if not context.user_data["voice_user_title"]:
        context.user_data["voice_user_title"] = utils.validate(
        utils.get_description(update.message))

    elif not context.user_data["voice_desc"]:
        context.user_data["voice_desc"] = utils.validate(
        utils.get_description(update.message))

    # проверить наличие имени автора и описания
    # если нет, то ждать ввода от пользователя
    if res := await _voice_check_info(update, context):
        return res # stage 1

    status = await voice_add(update, context)
    return status

# Cancel
############

async def voice_cancel(update, context):
    """Отмена команды добавления."""

    context.user_data["voice_delete"].append(update.message)
    await update.message.reply_text("Добавление войса отменено.",
    reply_markup=ReplyKeyboardRemove())
    return (await voice_end(update, context))

async def voice_end(update, context):
    """Завершение команды добавления."""

    for m in context.user_data["voice_delete"]:
        try:
            await m.delete()
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END

# Вспомогательные функции
###########################

async def _voice_check_info(update, context):
    """Проверяет наличие имени автора и описания."""

    # если автора или описания нет, то
    # ждем пока пользователь их введет
    s = None

    if not context.user_data["voice_desc"]:
        s = "описание"

    if not context.user_data["voice_user_title"]:

        if res := userlist_db.find(
            context.user_data["voice_user_name"],
            context.user_data["voice_user_title"]):

            context.user_data["voice_user_title"] = res[2]
        else:
            s = "имя автора"
    
    if context.user_data["voice_desc"] == 'Автор':
        s = "имя автора"
        context.user_data["voice_desc"] = None
        context.user_data["voice_user_name"] = None
        context.user_data["voice_user_title"] = None
        
    if not s:
        return None

    if s == 'описание':
        helptext = (f"Теперь напишите {s} для этого войса\.\n\n"\
        "_Описание также можно ввести в команде: `/voice_add Продал все приставки`\n"\
        "Нажмите кнопку `Отмена` чтобы отменить добавление войса\n\n"\
        "Если этот войс на самом деле принадлежит другому автору, то нажмите на кнопку `Автор`_")

    if s == 'имя автора':
        helptext = (f"Теперь напишите {s} для этого войса\.\n\n"\
        "_Укажите текущий никнейм пользователя или его имя\.\n"\
        "Нажмите кнопку `Отмена` чтобы отменить добавление войса_")

    msg = await update.message.reply_markdown_v2(
        helptext,
    
    # создать клавиатуру пользователю
    reply_markup = ReplyKeyboardMarkup.from_row(
        ["Отмена", "Автор"],
        resize_keyboard = True,
        one_time_keyboard = True,
        selective = True))

    context.user_data["voice_delete"].append(msg)

    return 1 # stage 1

####################
# /voice_delete    #
####################

async def voice_delete(update, context):
    """Команда удаления голосового сообщения."""
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
    # Пробуем взять цифру после команды
    try:
        if int(context.args[0]) > 0:
            author_num = int(context.args[0])-1
    except: author_num = 0

    # Берем имя автора после команды
    user_name = ''.join(context.args)

    out_message = _voicelist_show_text(update.effective_chat.id, author_num, 0, user_name)
    markup = _voicelist_show_keyboard(
        update.effective_chat.id, author_num, 0, update.effective_user.id, user_name)
    await update.message.reply_text(out_message, reply_markup=markup)

async def voicelist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /voicelist."""
    await kbrd.callback(update, context,
                        _voicelist_show_text,
                        _voicelist_show_keyboard)

def _voicelist_show_text(chat_id, author_num, page, author_name = None):
    """Возвращает текст сообщения /voicelist"""
    e = kbrd.get_text(chat_id, author_num, page,
                      db.authors_list,
                      db.by_author,
                      "Список голосовых сообщений",
                      author_name)
    return e

def _voicelist_show_keyboard(chat_id, author_num, page, user_id, author_name = None):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.show_keyboard(chat_id, author_num, page, user_id,
                           db.authors_list,
                           db.by_author,
                           "voicelist",
                           author_name)
    return e
