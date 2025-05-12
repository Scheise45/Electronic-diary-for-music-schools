from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from .base import Base, engine, Session
from .reference import Role, SchoolYear, Department, Instrument, Program, Subject, ProgramSubject
from .users import User, Student, Teacher, Parent, StudentParent
from .school import StudentYear, Grade, Attendance, Schedule, Homework
import datetime
import os

session = Session()


def create_all():
    Base.metadata.create_all(bind=engine)


def export_to_mysql(sqlite_db_path="data/data.db", output_file="dump_mysql.sql"):
    try:
        # Проверка существования SQLite базы
        if not os.path.exists(sqlite_db_path):
            raise FileNotFoundError(f"SQLite файл {sqlite_db_path} не найден.")

        # Подключение к SQLite
        sqlite_engine = create_engine(
            f"sqlite:///{sqlite_db_path}", echo=False)
        sqlite_inspector = inspect(sqlite_engine)
        expected_tables = [
            'roles', 'school_years', 'departments', 'instruments', 'programs', 'subjects',
            'program_subjects', 'users', 'students', 'teachers', 'parents', 'student_parents',
            'student_years', 'schedule', 'grades', 'attendance', 'homework'
        ]
        missing_tables = [
            t for t in expected_tables if not sqlite_inspector.has_table(t)]
        if missing_tables:
            raise ValueError(
                f"В SQLite отсутствуют таблицы: {', '.join(missing_tables)}.")

        # Функция для преобразования SQLite-типов в MySQL
        def sqlite_to_mysql_type(col_type):
            col_type_str = str(col_type).upper()
            if col_type_str.startswith("INTEGER"):
                return "INT"
            elif col_type_str.startswith("STRING"):
                length = getattr(col_type, "length", 255)
                return f"VARCHAR({length})"
            elif col_type_str.startswith("DATE"):
                return "DATE"
            elif col_type_str.startswith("TEXT"):
                return "TEXT"
            elif col_type_str.startswith("BOOLEAN"):
                return "TINYINT(1)"
            elif col_type_str.startswith("DATETIME"):
                return "DATETIME"
            else:
                return col_type_str

        # Функция для получения MySQL DDL
        def get_mysql_ddl(table, inspector):
            columns = inspector.get_columns(table.name)
            mysql_columns = []

            for col in columns:
                col_type = sqlite_to_mysql_type(col['type'])
                col_name = col['name']
                nullable = "" if not col['nullable'] else " NULL"
                primary_key = " PRIMARY KEY" if col.get('primary_key') else ""
                default = f" DEFAULT {col['default']}" if col.get(
                    'default') and col['default'] != 'NULL' else ""
                auto_increment = " AUTO_INCREMENT" if col.get(
                    'primary_key') and col_type == "INT" else ""
                mysql_columns.append(
                    f"`{col_name}` {col_type}{auto_increment}{primary_key}{nullable}{default}")

            # Добавляем внешние ключи
            foreign_keys = inspector.get_foreign_keys(table.name)
            for fk in foreign_keys:
                for column, ref_table, ref_column in zip(fk['constrained_columns'], [fk['referred_table']] * len(fk['constrained_columns']), fk['referred_columns']):
                    mysql_columns.append(
                        f"FOREIGN KEY (`{column}`) REFERENCES `{ref_table}` (`{ref_column}`) ON DELETE CASCADE"
                    )

            return f"CREATE TABLE `{table.name}` (\n  " + ",\n  ".join(mysql_columns) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n"

        # Открываем файл для записи
        print(f"Создание SQL-дампа в {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            # Настройки MySQL
            f.write("SET NAMES utf8mb4;\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            # Экспорт структуры таблиц
            for table in Base.metadata.sorted_tables:
                f.write(f"-- Структура таблицы {table.name}\n")
                f.write(get_mysql_ddl(table, sqlite_inspector))
                f.write("\n")

                # Экспорт данных пакетами
                f.write(f"-- Данные для таблицы {table.name}\n")
                with sqlite_engine.connect() as conn:
                    result = conn.execute(table.select())
                    columns = result.keys()
                    rows = result.fetchall()

                    if rows:
                        batch_size = 1000  # Пакетная вставка по 1000 записей
                        for i in range(0, len(rows), batch_size):
                            batch = rows[i:i + batch_size]
                            values = []
                            for row in batch:
                                row_values = []
                                for v in row:
                                    if v is None:
                                        row_values.append("NULL")
                                    elif isinstance(v, datetime.date):
                                        row_values.append(f"'{v}'")
                                    elif isinstance(v, str):
                                        row_values.append(
                                            f"'{v.replace('\'', '\\\'')}'")
                                    elif isinstance(v, bool):
                                        row_values.append("1" if v else "0")
                                    else:
                                        row_values.append(str(v))
                                values.append(f"({','.join(row_values)})")
                            insert_query = (
                                f"INSERT INTO `{table.name}` ({','.join([f'`{col}`' for col in columns])}) "
                                f"VALUES {','.join(values)};\n"
                            )
                            f.write(insert_query)
                        print(
                            f"Перенесено {len(rows)} записей для таблицы {table.name}.")
                    else:
                        print(
                            f"Таблица {table.name} пуста, данные не экспортированы.")
                    f.write("\n")

            # Восстанавливаем FOREIGN_KEY_CHECKS
            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")

        print(f"SQL-дамп успешно создан в файле {output_file}.")

    except SQLAlchemyError as e:
        print(f"Ошибка SQLAlchemy: {e}")
    except FileNotFoundError as e:
        print(f"Ошибка файла: {e}")
    except ValueError as e:
        print(f"Ошибка данных: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        # Закрытие соединения SQLite
        if 'sqlite_engine' in locals():
            sqlite_engine.dispose()


if __name__ == "__main__":
    export_to_mysql()
