"""
Администраторские функции модуля черного списка.
"""

import csv
import snearl.module.blacklist_db as db
from snearl.database import export_dir, import_dir


#############
# Functions #
#############


def export_blacklist():
    """Экспорт блокировок из базы данных."""

    export_file = export_dir / "blacklist.csv"

    export_dir.mkdir(parents=True, exist_ok=True)

    with open(export_file, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(db.get_all())

    print(f"\nУспешно экспортировано в файл {export_file}.")


def import_blacklist():
    """Импорт блокировок в базу данных."""

    import_file = import_dir / "blacklist.csv"

    if not import_file.is_file():
        print(f"\nФайл импорта не найден:\n{import_file}")
        return

    with open(import_file, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            db.add(*row)
        db.con.commit()

    print("\nУспешно импортировано в базу данных.")
