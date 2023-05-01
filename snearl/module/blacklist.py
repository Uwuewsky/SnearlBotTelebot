"""
Модуль черного списка.
Позволяет блокировать группу, чтобы бот
автоматически удалял репосты из нее.
"""

import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    MessageHandler, CommandHandler, CallbackQueryHandler, filters)

from snearl.instance import app, help_messages
import snearl.module.blacklist_db as db
import snearl.module.utils as utils

#####################
# main              #
#####################

def main():
    db.blacklist_create_table()
    db.con.commit()

    help_messages.append("""
*Удалять репосты из заблокированных чатов*
  a\. Заблокировать чат: /block;
  b\. Разблокировать чат: /allow;
  c\. Список блокировок: /blacklist;
""")

    app.add_handler(CommandHandler("block", block_group))
    app.add_handler(CommandHandler("allow", allow_group))
    app.add_handler(CommandHandler("blacklist", show_blacklist))

    app.add_handler(MessageHandler(filters.FORWARDED, delete_repost))
    app.add_handler(CallbackQueryHandler(
        show_blacklist_callback,
        pattern="^blacklist"))

    return

#####################
# delete handler    #
#####################

async def delete_repost(update, context):
    """Функция удаления сообщения, репостнутой из чата в черном списке."""
    if update.message.forward_from_chat is None:
        return

    group_id = update.message.forward_from_chat.id
    group_desc = update.message.forward_from_chat.effective_name

    if db.blacklist_get(update.effective_chat.id, group_id):
        await update.message.delete()
        await update.effective_chat.send_message(
            f"Репост из {group_desc} удален.")
        return
    return

#####################
# /block            #
#####################

async def block_group(update, context):
    """Команда добавления чата в блеклист."""
    if await utils.check_access(update):
        return

    if update.message.reply_to_message is None:
        await update.message.reply_text(
            "Нужно отправить команду ответом на репост из группы.")
        return 

    if update.message.reply_to_message.forward_from_chat is None:
        await update.message.reply_text("Это не репост из группы.")
        return

    chat_id = update.effective_chat.id
    group_id = update.message.reply_to_message.forward_from_chat.id
    group_desc = update.message.reply_to_message.forward_from_chat.effective_name

    if db.blacklist_get(chat_id, group_id):
        await update.message.reply_text(f"{group_desc} уже в блеклисте.")
        return
    else:
        db.blacklist_create_table()
        db.blacklist_add(chat_id, group_id, group_desc)
        db.con.commit()
        await update.message.reply_text(
            f"Репосты из {group_desc} добавлены в черный список.")
    return

#####################
# /allow            #
#####################

async def allow_group(update, context):
    """Команда удаления чата из блеклиста."""
    if await utils.check_access(update):
        return

    try:
        index = int(context.args[0]) - 1
        entry = db.blacklist_by_chat(update.effective_chat.id)[index]
        group_id, group_desc = entry[1], entry[2]

        db.blacklist_delete(update.effective_chat.id, group_id)
        db.con.commit()

        await update.message.reply_text(
            f"{group_desc} удален из черного списка.")

    except Exception:
        await update.message.reply_text(
            "Нужно указать номер чата из списка /blacklist.")
    return

#####################
# /blacklist        #
#####################

async def show_blacklist(update, context):
    """Команда показа списка заблокированных чатов."""
    out_message = _show_blacklist_text(update.effective_chat.id, 0)
    markup = _show_blacklist_keyboard(
        update.effective_chat.id, 0, update.effective_user.id)
    await update.message.reply_text(out_message, reply_markup=markup)
    return

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
    return

def _show_blacklist_keyboard(chat_id, page, user_id):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    bl = db.blacklist_by_chat(chat_id)
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
    if page == 0 and page < page_max:
        keyboard += [btn_info, btn_next]
    elif page == page_max and page != 0:
        keyboard += [btn_back, btn_info]
    elif page > 0 and page < page_max:
        keyboard += [btn_back, btn_info, btn_next]
    else:
        keyboard += [btn_info]

    reply_markup = InlineKeyboardMarkup([keyboard])

    return reply_markup

def _show_blacklist_text(chat_id, page):
    """Функция, возвращающая текст сообщения с постраничной клавиатурой."""
    if bl := db.blacklist_by_chat(chat_id):
        s = "Список заблокированных чатов:\n\n"
        offset = page * 25

        if not bl[offset:offset+25]:
            offset = 0

        for i, e in enumerate(bl[offset:offset+25], start=offset+1):
            s += f"{i}) {e[2]}\n"

        return s
    return "Список заблокированных чатов пуст."
