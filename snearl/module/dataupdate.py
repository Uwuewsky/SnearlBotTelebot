from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ChatMemberHandler, MessageHandler, filters)

import snearl.module.blacklist_db as db_b
import snearl.module.voicelist_db as db_v

#####################
# main              #
#####################

def main():
    # миграция и автоудаление
    from snearl.instance import app

    app.add_handler(
        MessageHandler(filters.StatusUpdate.MIGRATE, chat_migration))
    app.add_handler(
        ChatMemberHandler(bot_status_changed, ChatMemberHandler.MY_CHAT_MEMBER))

    return

async def chat_migration(update, context):
    """Заменяет ID чата на актуальный когда тип группы меняется."""
    old_chat = update.message.migrate_from_chat_id
    new_chat = update.message.migrate_to_chat_id
    chat_migrate(old_chat, new_chat)
    return

def chat_migrate(old_chat, new_chat):
    db_v.voicelist_migration(old_chat, new_chat)
    db_b.blacklist_migration(old_chat, new_chat)
    db_b.con.commit()
    return

async def bot_status_changed(update, context):
    """Удаляет все записи чата из базы данных, когда бот из него выходит"""
    status = update.my_chat_member.new_chat_member.status

    if status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
        db_b.blacklist_clear_by_chat(update.effective_chat.id)
        db_v.voicelist_clear_by_chat(update.effective_chat.id)
        db_b.con.commit()
    return
