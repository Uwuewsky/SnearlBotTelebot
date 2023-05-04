"""
Администраторские функции модуля черного списка.
"""

import json
import snearl.module.blacklist_db as db
from snearl.database import export_dir, import_dir

#############
# Functions #
#############

def export_blacklist():
    """
    Экспорт блокировок из базы данных.
    """
    export_dict = {}
    export_file = export_dir / "blacklist.json"

    for entry in db.get_all():
        chat_id = entry[0]
        user_name = entry[1]

        if not chat_id in export_dict:
            export_dict[chat_id] = []
        export_dict[chat_id].append(user_name)

    export_dir.mkdir(parents=True, exist_ok=True)
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(export_dict, f, ensure_ascii=False, indent="    ")

    print(f"\nУспешно экспортировано в файл {export_file}.")

def import_blacklist():
    """
    Импорт блокировок в базу данных.
    """
    import_file = import_dir / "blacklist.json"

    if not import_file.is_file():
        print(f"Файл импорта не найден:\n{import_file}")
        return

    with open(import_file, "r", encoding="utf-8") as f:
        import_dict = json.load(f)

    db.create_table()
    for chat_id, name_list in import_dict.items():
        for user_name in name_list:
            db.add(chat_id, user_name)
    db.con.commit()

    print("\nУспешно импортировано в базу данных.")
