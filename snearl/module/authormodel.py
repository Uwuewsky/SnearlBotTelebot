"""
Прототип authormodel определяет некоторые функции,
и базу данных для построения на его основе иных модулей,
которым требуется хранить в базе данных данные в таблице вида:
|---------+---------+-------------+-----------+-----------+------|
| chat_id | file_id | file_author | file_desc | file_blob | type |
|---------+---------+-------------+-----------+-----------+------|
"""

import snearl.database as db
from snearl.module import utils

####################
# /entry_delete    #
####################

async def entry_delete(update, context,
                       db_get_authors,   # функ. все авторы чата
                       db_get_by_author, # функ. все записи автора
                       db_delete,        # функ. удаление записи по id
                       list_name, list_name_fun): # названия списков
    """Команда удаления через бота."""
    if await utils.check_access(update):
        return

    try:
        chat_id = update.effective_chat.id

        num_author = int(context.args[0]) - 1
        num_file = int(context.args[1]) - 1

        # найти автора по номеру в команде
        file_author = db_get_authors(chat_id)[num_author]

        # найти запись по номеру в команде
        entry = db_get_by_author(chat_id, file_author)[num_file]

        file_id, file_desc = entry[1], entry[3]

        db_delete(file_id)
        db.con.commit()

    except Exception:
        await update.message.reply_markdown_v2(
            "Нужно указать номера автора и войса из "\
            f"/{list_name}list, например:\n"\
            f"`/{list_name}_delete 2 15`")
        return

    await update.message.reply_text(
            f"Из {list_name_fun} {file_author} успешно удален {file_desc}")
    return file_author, file_desc
