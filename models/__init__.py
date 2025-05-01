from .base import Base, engine, Session
from .reference import (
    Role, SchoolYear, Department, Instrument, Program, Subject, ProgramSubject
)
from .users import User, Student, Teacher, Parent, StudentParent
from .school import StudentYear, Grade, Attendance, Schedule, Homework
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.mysql import dialect as mysql_dialect
import datetime

session = Session()


def create_all():
    Base.metadata.create_all(bind=engine)


def export_to_mysql(sqlite_db_path="data/data.db", output_file="dump_mysql.sql"):
    # Временное подключение к SQLite
    sqlite_engine = create_engine(f"sqlite:///{sqlite_db_path}", echo=False)

    # Функция для преобразования SQLite-типов в MySQL
    def sqlite_to_mysql_type(col_type):
        if str(col_type).startswith("INTEGER"):
            return "INT"
        elif str(col_type).startswith("STRING"):
            length = getattr(col_type, "length", 255)
            return f"VARCHAR({length})"
        elif str(col_type).startswith("DATE"):
            return "DATE"
        elif str(col_type).startswith("TEXT"):
            return "TEXT"
        elif str(col_type).startswith("BOOLEAN"):
            return "TINYINT(1)"
        return str(col_type)

    # Функция для получения MySQL DDL
    def get_mysql_ddl(table, inspector):
        columns = inspector.get_columns(table.name)
        mysql_columns = []

        for col in columns:
            col_type = sqlite_to_mysql_type(col['type'])
            col_name = col['name']
            nullable = "" if not col['nullable'] else " NULL"
            primary_key = " PRIMARY KEY" if col.get('primary_key') else ""
            default = f" DEFAULT {col['default']}" if col.get('default') else ""
            mysql_columns.append(f"`{col_name}` {col_type}{primary_key}{nullable}{default}")

        # Добавляем внешние ключи
        foreign_keys = inspector.get_foreign_keys(table.name)
        for fk in foreign_keys:
            for column, ref_table, ref_column in zip(fk['constrained_columns'], [fk['referred_table']] * len(fk['constrained_columns']), fk['referred_columns']):
                mysql_columns.append(
                    f"FOREIGN KEY (`{column}`) REFERENCES `{ref_table}` (`{ref_column}`) ON DELETE CASCADE"
                )

        return f"CREATE TABLE `{table.name}` (\n  " + ",\n  ".join(mysql_columns) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n"

    # Открываем файл для записи
    with open(output_file, "w", encoding="utf-8") as f:
        # Настройки MySQL
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

        # Получаем инспектор для SQLite
        inspector = inspect(sqlite_engine)

        # Экспорт структуры таблиц
        for table in Base.metadata.sorted_tables:
            f.write(get_mysql_ddl(table, inspector))
            f.write("\n")

            # Экспорт данных
            with sqlite_engine.connect() as conn:
                result = conn.execute(table.select())
                rows = result.fetchall()

                if rows:
                    columns = result.keys()
                    for row in rows:
                        values = []
                        for v in row:
                            if v is None:
                                values.append("NULL")
                            elif isinstance(v, datetime.date):
                                values.append(f"'{v}'")
                            elif isinstance(v, str):
                                values.append(f"'{v.replace('\'', '\\\'')}'")
                            else:
                                values.append(str(v))
                        insert_query = f"INSERT INTO `{table.name}` ({','.join([f'`{col}`' for col in columns])}) VALUES ({','.join(values)});\n"
                        f.write(insert_query)
                    f.write("\n")

        # Восстанавливаем FOREIGN_KEY_CHECKS
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    print(f"SQL-дамп создан в файле {output_file}")
