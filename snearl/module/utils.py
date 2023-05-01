from telegram import Chat
from telegram.constants import ChatMemberStatus

import snearl.database as db

####################
# Проверка доступа #
####################

async def check_access(update):
    """Возвращает True если доступ к команде запрещен."""
    # проверить если включен локальный режим
    if e := db.settings_get("local_mode"):
        if e == str(update.effective_chat.id):
            return False
        else:
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
    else:
        await update.message.reply_text(
            "У тебя нет прав использовать админскую команду.")
        return True
