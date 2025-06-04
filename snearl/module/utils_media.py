"""
Модуль с функциями для скачивания.
"""

import io

from telegram import MessageOrigin

from snearl.instance import app
from snearl.module import utils
from snearl.module import userlist_db


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
    except Exception:
        pass

    return picture


async def get_avatar(message):

    # попробовать загрузить из бд
    user_id = userlist_db.find_id(
        utils.get_sender_username(message),
        utils.get_sender_title(message))
    res = userlist_db.get_avatar(user_id)
    if res:
        return io.BytesIO(res)

    # загрузить из телеграма
    avatar = None

    try:
        avatar_file = None
        pl = None

        if origin := message.forward_origin:
            if origin.type == MessageOrigin.USER:
                pl = await origin.sender_user.get_profile_photos(limit=1)
                if pl and pl.total_count > 0:
                    avatar_file = pl.photos[0][0]
            if origin.type == MessageOrigin.HIDDEN_USER:
                raise Exception
            if origin.type == MessageOrigin.CHAT:
                chat = await app.bot.get_chat(origin.sender_chat.id)
                if chat.photo:
                    avatar_file = chat.photo.small_file_id
            if origin.type == MessageOrigin.CHANNEL:
                chat = await app.bot.get_chat(origin.chat.id)
                if chat.photo:
                    avatar_file = chat.photo.small_file_id
        elif message.from_user:
            pl = await message.from_user.get_profile_photos(limit=1)
            if pl and pl.total_count > 0:
                avatar_file = pl.photos[0][0]

        if avatar_file:
            avatar = await download_file(avatar_file)
    except Exception:
        pass

    return avatar


async def download_file(file_id):
    file_bytes = io.BytesIO()
    f = await app.bot.get_file(file_id)
    await f.download_to_memory(file_bytes)
    return file_bytes
