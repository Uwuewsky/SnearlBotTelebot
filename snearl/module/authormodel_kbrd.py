"""
Клавиатура модели authormodel,
позволяющая пролистывать списки
постранично для каждого автора
"""

import math
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup
)


#############
# Keyboard  #
#############


def show_keyboard(chat_id, author_num, page, user_id,
                  get_authors_list, get_by_author,
                  callback_name, author_name):
    """Клавиатура сообщения с кнопками для пролистывания списка."""
    al = get_authors_list(chat_id)
    if not al:
        return None

    ##################################
    # Клавиатура перехода по авторам #

    # ищем имя автора по номеру
    index_max = len(al) - 1

    # либо сразу берем автора по переданному имени
    if author_name in al:
        file_author = author_name
        author_num = al.index(file_author)
    elif 0 <= author_num <= index_max:
        file_author = al[author_num]
    else:
        file_author = al[0]
        author_num = 0

    # используем автора чтобы получить его список
    # и последнюю страницу для пролистывания их списка
    page_max = 0
    if pl := get_by_author(chat_id, file_author):
        page_max = max(0, math.ceil(len(pl)/25) - 1)
    if not (0 <= page <= page_max):
        page = 0

    # данные, передающиеся в коллбека при нажатии на кнопку
    call_data = f"{callback_name} {chat_id} {author_num} {page} {user_id}"

    # Имена авторов для кнопок перехода
    author_name_next = ""
    author_name_back = ""
    if 0 == author_num < index_max:
        author_name_next = al[author_num + 1]
    elif index_max == author_num != 0:
        author_name_back = al[author_num - 1]
    elif 0 < author_num < index_max:
        author_name_next = al[author_num + 1]
        author_name_back = al[author_num - 1]

    # Сами кнопки
    btn_author_back = InlineKeyboardButton(
        f"< [{author_num}] {author_name_back}",
        callback_data=f"{call_data} authorback")

    btn_author_info = InlineKeyboardButton(
        f"[{author_num+1}] {file_author}",
        callback_data=f"{call_data} authorinfo")

    btn_author_next = InlineKeyboardButton(
        f"[{author_num+2}] {author_name_next} >",
        callback_data=f"{call_data} authornext")

    # Добавление этих кнопок в ряд клавиатуры
    keyboard = []
    keyboard_author = []

    if 0 == author_num < index_max:
        keyboard_author += [btn_author_info, btn_author_next]
    elif index_max == author_num != 0:
        keyboard_author += [btn_author_back, btn_author_info]
    elif 0 < author_num < index_max:
        keyboard_author += [
            btn_author_back, btn_author_info, btn_author_next
        ]
    else:
        keyboard_author += [btn_author_info]

    keyboard.append(keyboard_author)

    ####################################
    # Клавиатура перехода по страницам #

    # Кнопки
    btn_page_back = InlineKeyboardButton(
        "< Назад",
        callback_data=f"{call_data} pageback")

    btn_page_info = InlineKeyboardButton(
        f"{page+1}/{page_max+1}",
        callback_data=f"{call_data} pageinfo")

    btn_page_next = InlineKeyboardButton(
        "Вперед >",
        callback_data=f"{call_data} pagenext")

    # Добавление этих кнопок во второй ряд клавиатуры
    keyboard_page = []
    if 0 == page < page_max:
        keyboard_page += [btn_page_info, btn_page_next]
    elif page_max == page != 0:
        keyboard_page += [btn_page_back, btn_page_info]
    elif 0 < page < page_max:
        keyboard_page += [btn_page_back, btn_page_info, btn_page_next]
    else:
        keyboard_page += [btn_page_info]
    keyboard.append(keyboard_page)

    # Составление клавиатуры
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


#############
# Callback  #
#############


async def callback(update, context,
                   get_reply_text,
                   get_reply_markup):
    """Функция, отвечающая на коллбэки от нажатия кнопок."""
    call_data = update.callback_query.data.split()
    call_chat = call_data[1]
    call_author = int(call_data[2])
    call_page = int(call_data[3])
    call_user = call_data[4]
    call_type = call_data[5]

    if call_user != str(update.callback_query.from_user.id):
        await update.callback_query.answer(
            "Вы можете листать только отправленный Вам список.")
        return
    if call_type == "pageinfo":
        await update.callback_query.answer(f"Страница #{call_page+1}")
        return
    if call_type == "authorinfo":
        await update.callback_query.answer(f"Автор #{call_author+1}")
        return

    if call_type == "pageback":
        call_page -= 1
    if call_type == "pagenext":
        call_page += 1

    if "author" in call_type:
        call_page = 0
    if call_type == "authorback":
        call_author -= 1
    if call_type == "authornext":
        call_author += 1

    out_message = get_reply_text(
        call_chat, call_author, call_page)
    markup = get_reply_markup(
        call_chat, call_author, call_page, call_user)
    await update.callback_query.edit_message_text(
        out_message, reply_markup=markup)


##############
# List text  #
##############


def get_text(chat_id, author_num, page,
             get_authors_list, get_by_author,
             list_name, author_name=None):
    """Возвращает текст сообщения"""

    if al := get_authors_list(chat_id):
        # найти автора по номеру из списка всех авторов чата
        if author_name in al:
            # либо взять автора сразу по переданному имени
            file_author = author_name
        elif 0 <= author_num < len(al):
            file_author = al[author_num]
        else:
            file_author = al[0]

        # список всех войсов автора для составления текста
        vl = get_by_author(chat_id, file_author)
        s = f"{list_name}:\n\n"
        offset = page * 25

        # сформатировать текст в виде списка цитат
        # с постраничным отступом и нумерацией
        if not vl[offset:offset+25]:
            offset = 0
        for i, e in enumerate(vl[offset:offset+25], start=offset+1):
            s += f"{i}) {e[4] or e[3]}\n"

        return s
    return f"{list_name} пуст."
