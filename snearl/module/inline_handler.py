"""
Модуль с инлайн-обработчиком.
Использует данные БД других модулей
и выдает общий их список.
"""

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

import snearl.database as db
from snearl.instance import app
from snearl.module.voicelist import voice_query_result, voice_search
from snearl.module.quotelist import quote_query_result, quote_search

def main():
    app.add_handler(InlineQueryHandler(global_inline_query))

async def global_inline_query(update, context):
    """
    Глобальная инлайн-функция.
    """
    query = update.inline_query.query
    offset = update.inline_query.offset
    offset = int(offset) if offset else 0
    limit = 50
    results = []

    if query:
        query_type, _, query_part = query.partition(" ")
        if query_type == "в":
            search_results = voice_search(query_part, offset, limit)
        elif query_type == "ц":
            search_results = quote_search(query_part, offset, limit)
        else:
            search_results = global_search(query, offset, limit)
    else:
        search_results = global_search(query, offset, limit)

    for i, e in enumerate(search_results):
        # проверяем колонку type
        if e[5] == "voice":
            # создаем InlineQueryResult на основе типа
            results.append(voice_query_result(i, e))
        elif e[5] == "quote":
            results.append(quote_query_result(i, e))

    if not results and not offset:
        # иначе выдаем сообщение что ничего не найдено
        # not offset чтобы это сообщение не выдавало в конце списка
        s = f"По запросу {query} ничего не найдено"
        results = [
            InlineQueryResultArticle(
                id = "0",
                title = s,
                input_message_content = InputTextMessageContent(s))
        ]

    try:
        await update.inline_query.answer(results, next_offset=offset+50)
    except Exception as e:
        # выдаем в инлайн сообщение об ошибке
        s = f"Во время запроса {query} произошла ошибка"
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id = "0",
                title = s,
                description = str(e),
                input_message_content = InputTextMessageContent(
                    f"{s}:\n{str(e)}"))
        ])

def global_search(query, offset, limit):
    query = f"%{query}%".lower()
    res = db.cur.execute("SELECT chat_id, file_id, "\
                         "user_title, user_nick, file_desc, type "\
                         "FROM Voicelist "\
                         "JOIN Userlist "\
                         "ON Userlist.id = Voicelist.user_id "\
                         "WHERE LOWER(user_title) LIKE :query "\
                         "OR LOWER(user_nick) LIKE :query "\
                         "OR LOWER(file_desc) LIKE :query "\

                         "UNION ALL "\

                         "SELECT chat_id, file_id, "\
                         "user_title, user_nick, file_desc, type "\
                         "FROM Quotelist "\
                         "JOIN Userlist "\
                         "ON Userlist.id = Quotelist.user_id "\
                         "WHERE LOWER(user_title) LIKE :query "\
                         "OR LOWER(user_nick) LIKE :query "\
                         "OR LOWER(file_desc) LIKE :query "\

                         "ORDER BY type DESC, user_nick, user_title "\
                         "LIMIT :limit "\
                         "OFFSET :offset",
                         {"query": query, "limit": limit, "offset": offset})
    return res.fetchall()
