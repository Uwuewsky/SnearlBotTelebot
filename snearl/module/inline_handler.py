from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

import snearl.database as db
from snearl.instance import app
from snearl.module.voicelist import voice_inline_query
from snearl.module.quotelist import quote_inline_query

def main():
    app.add_handler(InlineQueryHandler(global_inline_query))
    return

async def global_inline_query(update, context):
    query = update.inline_query.query
    offset = update.inline_query.offset
    offset = int(offset) if offset else 0
    limit = 50
    results = []

    search_results = global_search(query, offset, limit)

    for i, e in enumerate(search_results):
        # проверяем колонку type
        if e[4] == "voice":
            # создаем InlineQueryResult на основе типа
            results.append(voice_inline_query(i, e))
        elif e[4] == "quote":
            results.append(quote_inline_query(i, e))

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
    return

def global_search(query, offset, limit):
    query = f"%{query}%".lower()
    res = db.cur.execute("SELECT chat_id, file_id, file_author, file_desc, type "\
                         "FROM Voicelist "\
                         "WHERE LOWER(file_author) LIKE :query "\
                         "OR LOWER(file_desc) LIKE :query "\

                         "UNION ALL "\

                         "SELECT chat_id, file_id, file_author, file_desc, type "\
                         "FROM Quotelist "\
                         "WHERE LOWER(file_author) LIKE :query "\
                         "OR LOWER(file_desc) LIKE :query "\

                         "ORDER BY type DESC, file_author "\
                         "LIMIT :limit "\
                         "OFFSET :offset",
                         {"query": query, "limit": limit, "offset": offset})
    return res.fetchall()
