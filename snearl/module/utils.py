"""
Модуль с разными полезными функциями.
"""

import re
import textwrap
import hashlib

from telegram import Chat
from telegram.constants import ChatMemberStatus

import snearl.database as db

####################
# Функции проверки #
####################

async def check_access(update):
    """Возвращает True если доступ к команде запрещен."""
    # проверить если включен локальный режим
    if e := db.settings_get("local_mode"):
        if e == str(update.effective_chat.id):
            return False
        await update.message.reply_text(
            "Команды редактирования запрещены для этого чата.")
        return True

    # разрешить доступ в приватном чате с ботом
    if update.effective_chat.type == Chat.PRIVATE:
        return False

    # проверить статус пользователя в чате
    status = (await update.effective_chat.get_member(
        update.effective_user.id)).status

    if status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return False

    await update.message.reply_text(
        "У тебя нет прав использовать админскую команду.")
    return True

####################
# /автоудаление    #
####################

def schedule_delete_message(context, name, msg):
    """Запланировать удаление сообщения."""
    context.job_queue.run_once(delete_message, 5 * 60,
                               name=f"{name}-{msg.id}",
                               data=msg)

async def delete_message(context):
    """Удаляет сообщение по истечении минуты."""
    try:
        await context.job.data.delete()
    except Exception:
        pass


######################
# Методы для Message #
######################

# Строковые
############

def md5(s):
    if s:
        return hashlib.md5(s.encode()).hexdigest()
    return None

def get_full_description(message):
    """Возвращает текст сообщения."""
    text = message.text or message.caption
    return text if text else None

def get_description(message):
    """Возвращает сокращенный текст сообщения."""
    if not (text := get_full_description(message)):
        return None

    res = []
    width = 35
    max_lines = 50

    for s in text.splitlines():
        if len(s) > width:
            res += textwrap.wrap(s, width=width,
                                 replace_whitespace=False)
        else:
            res.append(s)
    return "\n".join(res[:max_lines])

def get_sender_title_short(message):
    s = get_sender_title(message)
    return textwrap.shorten(s, width=35, placeholder="...")

def get_sender_id(message):
    """Возвращает id отправителя."""
    s = None
    if message.forward_from:
        s = message.forward_from.id
    elif message.forward_sender_name:
        s = None
    elif message.forward_from_chat:
        s = message.forward_from_chat.id
    elif message.from_user:
        s = message.from_user.id
    return s

def get_sender_title(message):
    """Возвращает имя отправителя."""
    s = None
    if message.forward_from:
        s = message.forward_from.full_name
    elif message.forward_sender_name:
        s = message.forward_sender_name
    elif message.forward_from_chat:
        s = message.forward_from_chat.effective_name
    elif message.from_user:
        s = message.from_user.full_name
    return s

def get_sender_username(message):
    """Возвращает @тег_пользователя"""
    s = None
    if message.forward_from:
        s = message.forward_from.username
    elif message.forward_sender_name:
        s = None
    elif message.forward_from_chat:
        s = message.forward_from_chat.username
    elif message.from_user:
        s = message.from_user.username
    return s

def validate(text):
    """Убирает из имени все символы кроме букв, цифр и подчеркивания."""
    if text:
        s = re.sub(r"[^\w ]*", "", text)
        if s:
            return textwrap.shorten(s, width=35, placeholder="")
    return None
