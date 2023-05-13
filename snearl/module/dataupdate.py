"""
Модуль с функциями автоматического и ручного
обновления данных в БД при миграции чата
или при выходе бота из чата
"""

from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ChatMemberHandler, MessageHandler, filters)

import snearl.module.blacklist_db as db_b
from snearl.module.voicelist_db import db as db_v
from snearl.module.quotelist_db import db as db_q

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

async def chat_migration(update, context):
    """Заменяет ID чата на актуальный когда тип группы меняется."""
    context.application.migrate_chat_data(message=update.message)
    old_chat = update.message.migrate_from_chat_id
    new_chat = update.message.migrate_to_chat_id
    chat_migrate(old_chat, new_chat)

def chat_migrate(old_chat, new_chat):
    db_b.migration(old_chat, new_chat)
    db_v.migration(old_chat, new_chat)
    db_q.migration(old_chat, new_chat)
    db_b.con.commit()

async def bot_status_changed(update, context):
    """Удаляет все записи чата из базы данных, когда бот из него выходит"""
    status = update.my_chat_member.new_chat_member.status

    if status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
        context.chat_data.clear()
        db_b.clear_by_chat(update.effective_chat.id)
        db_v.clear_by_chat(update.effective_chat.id)
        db_q.clear_by_chat(update.effective_chat.id)
        db_b.con.commit()
