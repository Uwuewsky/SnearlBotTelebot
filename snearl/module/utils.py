"""
Модуль с разными полезными функциями.
"""

import io, re, textwrap

from telegram import Chat
from telegram.constants import ChatMemberStatus

import snearl.database as db
from snearl.instance import app
from snearl.module import userlist_db

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

######################
# Методы для Message #
######################

# Строковые
############

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

# Медиа функции
################

async def get_picture(message):
    picture = None
    file_id = None

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        if message.sticker:
            file_id = message.sticker.file_id

        if file_id:
            picture = await download_file(file_id)
    except:
        pass

    return picture

async def get_avatar(message):

    # попробовать загрузить из бд
    user_id = userlist_db.find_id(
        get_sender_username(message),
        get_sender_title(message))
    res = userlist_db.get_avatar(user_id)
    if res:
        return io.BytesIO(res)

    # загрузить из телеграма
    avatar = None

    try:
        avatar_file = None
        pl = None

        if message.forward_from:
            pl = await message.forward_from.get_profile_photos(limit=1)
            if pl and pl.total_count > 0:
                avatar_file = pl.photos[0][0]

        elif message.forward_from_chat:
            chat = await app.bot.get_chat(message.forward_from_chat.id)
            if chat.photo:
                avatar_file = chat.photo.small_file_id

        elif message.forward_sender_name:
            raise Exception

        elif message.from_user:
            pl = await message.from_user.get_profile_photos(limit=1)
            if pl and pl.total_count > 0:
                avatar_file = pl.photos[0][0]

        if avatar_file:
            avatar = await download_file(avatar_file)
    except:
        pass

    return avatar

async def download_file(file_id):
    file_bytes = io.BytesIO()
    f = await app.bot.get_file(file_id)
    await f.download_to_memory(file_bytes)
    return file_bytes
