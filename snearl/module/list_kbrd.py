"""
Клавиатура, позволяющая пролистывать простой список постранично.
"""

import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def show_keyboard(chat_id, page, user_id, get_list, callback_name):
    """Клавиатура сообщения с кнопками для пролистывания списка."""

    l = get_list(chat_id)
    if not l:
        return None

    page_max = max(0, math.ceil(len(l)/25) - 1)
    if not (0 <= page <= page_max):
        page = 0

    call_data = f"{callback_name} {chat_id} {page} {user_id}"

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

async def callback(update, context,
                   get_reply_text,
                   get_reply_markup):
    """Функция, отвечающая на коллбэки от нажатия кнопок."""

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

    out_message = get_reply_text(call_chat, call_page)
    markup = get_reply_markup(call_chat, call_page, call_user)

    await update.callback_query.edit_message_text(
        out_message, reply_markup=markup)

def get_text(chat_id, page, get_list, list_name):
    """Возвращает текст сообщения."""

    if l := get_list(chat_id):
        s = f"{list_name}:\n\n"
        offset = page * 25

        if not l[offset:offset+25]:
            offset = 0

        for i, e in enumerate(l[offset:offset+25], start=offset+1):
            s += f"{i}) {e[1]}\n"

        return s
    return f"{list_name} пуст."
