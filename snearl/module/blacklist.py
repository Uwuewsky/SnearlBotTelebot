"""
Модуль черного списка.
Позволяет блокировать группу или пользователя,
чтобы бот автоматически удалял репосты.
"""

import time

from telegram.ext import (
    MessageHandler, CommandHandler, CallbackQueryHandler, filters)

from snearl.instance import app, help_messages
from snearl.module import utils
from snearl.module import userlist_db
import snearl.module.list_kbrd as kbrd
import snearl.module.blacklist_db as db


#####################
# main              #
#####################


def main():
    help_messages.append("""
*Удалять репосты из заблокированных чатов*
  a\. Заблокировать чат: /block;
  b\. Разблокировать чат: `/allow [НомерЧата]`;
  c\. Список блокировок: /blacklist;
""")

    app.add_handler(CommandHandler("block", block_group))
    app.add_handler(CommandHandler("allow", allow_group))
    app.add_handler(CommandHandler("blacklist", blacklist_show))

    app.add_handler(MessageHandler(filters.FORWARDED, delete_repost), group=5)
    app.add_handler(CallbackQueryHandler(
        blacklist_show_callback,
        pattern="^blacklist"))


#####################
# delete handler    #
#####################


async def delete_repost(update, context):
    """Функция удаления сообщения, репостнутой из чата в черном списке."""
    if update.message is None:
        return  # опоздавшее обновление; сообщение уже удалено

    user_name = utils.get_sender_username(update.message)
    user_title = utils.get_sender_title(update.message)

    res = db.has(update.effective_chat.id, user_name, user_title)

    if not res:
        return

    userlist_db.update(user_name, utils.validate(user_title))
    db.con.commit()

    await update.message.delete()

    # проверка: отправлять сообщение только раз в 5 секунд
    if time.time() - context.chat_data.get("block_antispam", 0) > 5:
        await update.effective_chat.send_message(
            f"Репост из {user_title} удален.")
    context.chat_data["block_antispam"] = time.time()


#####################
# /block            #
#####################


async def block_group(update, context):
    """Команда добавления чата в блеклист."""
    if await utils.check_access(update):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Нужно отправить команду ответом на репост из группы.")
        return

    chat_id = update.effective_chat.id
    user_name = utils.get_sender_username(update.message.reply_to_message)
    user_title = utils.get_sender_title(update.message.reply_to_message)

    if db.has(chat_id, user_name, user_title):
        await update.message.reply_text(
            f"{user_title} уже в блеклисте.")
        return

    db.add(chat_id, user_name, user_title)
    userlist_db.update(user_name, user_title)
    db.con.commit()
    await update.message.reply_text(
        f"Репосты из {user_title} добавлены в черный список.")


#####################
# /allow            #
#####################


async def allow_group(update, context):
    """Команда удаления чата из блеклиста."""
    if await utils.check_access(update):
        return

    try:
        index = int(context.args[0]) - 1
        entry = db.by_chat(update.effective_chat.id)[index]
        user_name, user_title = entry[0], entry[1]

        db.delete(update.effective_chat.id, user_name, user_title)
        db.con.commit()

        await update.message.reply_text(
            f"{user_title} удален из черного списка.")

    except Exception:
        await update.message.reply_text(
            "Нужно указать номер чата из списка /blacklist.")


#####################
# /blacklist        #
#####################


async def blacklist_show(update, context):
    """Команда показа списка заблокированных чатов."""

    out_message = _blacklist_show_text(update.effective_chat.id, 0)

    markup = _blacklist_show_keyboard(
        update.effective_chat.id, 0, update.effective_user.id)

    msg = await update.message.reply_text(out_message, reply_markup=markup)

    utils.schedule_delete_message(context, "black_list_delete", msg)


async def blacklist_show_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /blacklist."""
    await kbrd.callback(update, context,
                        _blacklist_show_text,
                        _blacklist_show_keyboard)


def _blacklist_show_text(chat_id, page):
    """Возвращает текст сообщения /blacklist"""
    e = kbrd.get_text(chat_id, page,
                      db.by_chat,
                      "Список заблокированных чатов")
    return e


def _blacklist_show_keyboard(chat_id, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    e = kbrd.show_keyboard(chat_id, page, user_id,
                           db.by_chat,
                           "blacklist")
    return e
