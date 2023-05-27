"""
Модуль черного списка.
Позволяет блокировать группу или пользователя,
чтобы бот автоматически удалял репосты.
"""

import math, time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    MessageHandler, CommandHandler, CallbackQueryHandler, filters)

from snearl.instance import app, help_messages
from snearl.module import utils
import snearl.module.blacklist_db as db
from snearl.module import userlist_db

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
    app.add_handler(CommandHandler("blacklist", show_blacklist))

    app.add_handler(MessageHandler(filters.FORWARDED, delete_repost), group=5)
    app.add_handler(CallbackQueryHandler(
        show_blacklist_callback,
        pattern="^blacklist"))

#####################
# delete handler    #
#####################

async def delete_repost(update, context):
    """Функция удаления сообщения, репостнутой из чата в черном списке."""
    if update.message is None:
        return # опоздавшее обновление; сообщение уже удалено

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

    db.create_table()
    db.add(chat_id, user_name, user_title)
    userlist_db.update(user_name, utils.validate(user_title))
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

async def show_blacklist(update, context):
    """Команда показа списка заблокированных чатов."""
    out_message = _show_blacklist_text(update.effective_chat.id, 0)
    markup = _show_blacklist_keyboard(
        update.effective_chat.id, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)

async def show_blacklist_callback(update, context):
    """Функция, отвечающая на коллбэки от нажатия кнопок /blacklist."""
    call_data = update.callback_query.data.split()
    call_chat = call_data[1]
    call_page = int(call_data[2])
    call_user = call_data[3]
    call_type = call_data[4]

    if call_user != str(update.callback_query.from_user.id):
        await update.callback_query.answer(
            "Вы можете листать только отправленный Вам список.")
        return
    if call_type == "pageinfo":
        await update.callback_query.answer(f"Страница #{call_page+1}")
        return

    if call_type == "pageback":
        call_page -= 1
    if call_type == "pagenext":
        call_page += 1

    out_message = _show_blacklist_text(call_chat, call_page)
    markup = _show_blacklist_keyboard(call_chat, call_page, call_user)

    await update.callback_query.edit_message_text(
        out_message, reply_markup=markup)

def _show_blacklist_keyboard(chat_id, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    bl = db.by_chat(chat_id)
    if not bl:
        return None

    page_max = max(0, math.ceil(len(bl)/25) - 1)
    if page > page_max or page < 0:
        page = 0

    call_data = f"blacklist {chat_id} {page} {user_id}"

    btn_back = InlineKeyboardButton("< Назад",
                                    callback_data=f"{call_data} pageback")
    btn_info = InlineKeyboardButton(f"{page+1}/{page_max+1}",
                                    callback_data=f"{call_data} pageinfo")
    btn_next = InlineKeyboardButton("Вперед >",
                                    callback_data=f"{call_data} pagenext")

    keyboard = []
    if 0 == page < page_max:
        keyboard += [btn_info, btn_next]
    elif page_max == page != 0:
        keyboard += [btn_back, btn_info]
    elif 0 < page < page_max:
        keyboard += [btn_back, btn_info, btn_next]
    else:
        keyboard += [btn_info]

    reply_markup = InlineKeyboardMarkup([keyboard])

    return reply_markup

def _show_blacklist_text(chat_id, page):
    """Функция, возвращающая текст сообщения с постраничной клавиатурой."""
    if bl := db.by_chat(chat_id):
        s = "Список заблокированных чатов:\n\n"
        offset = page * 25

        if not bl[offset:offset+25]:
            offset = 0

        for i, e in enumerate(bl[offset:offset+25], start=offset+1):
            s += f"{i}) {e[1]}\n"

        return s
    return "Список заблокированных чатов пуст."
