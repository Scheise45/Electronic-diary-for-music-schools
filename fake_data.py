import sqlite3
from faker import Faker
import random
from datetime import datetime

# Инициализация Faker для русского языка
fake = Faker("ru_RU")

# Подключение к SQLite
try:
    conn = sqlite3.connect("data/data.db")
    cursor = conn.cursor()
except sqlite3.Error as e:
    print(f"Ошибка подключения к SQLite: {e}")
    exit(1)

school_code = "1234"

# Очистка таблиц
try:
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        try:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при очистке таблиц: {e}")
    conn.close()
    exit(1)

# Данные для таблиц
roles = ['Администратор', 'Учитель', 'Родитель', 'Ученик']
departments = ['Фортепиано', 'Струнные', 'Духовые', 'Вокал', 'Теоретический']
subjects = ['Сольфеджио', 'Музыкальная литература',
            'Инструмент', 'Хор', 'Ансамбль']
years = ['2020/2021', '2021/2022', '2022/2023', '2023/2024', '2024/2025']

try:
    # Вставка ролей
    cursor.executemany("INSERT INTO roles (name) VALUES (?)", [
                       (r,) for r in roles])
    # Вставка отделений
    cursor.executemany("INSERT INTO departments (name) VALUES (?)", [
                       (d,) for d in departments])
    # Вставка предметов
    cursor.executemany("INSERT INTO subjects (name) VALUES (?)", [
                       (s,) for s in subjects])
    # Вставка учебных годов
    cursor.executemany("INSERT INTO school_years (name) VALUES (?)", [
                       (y,) for y in years])
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при вставке начальных данных: {e}")
    conn.close()
    exit(1)

# Получение ID


def get_ids(table):
    cursor.execute(f"SELECT id FROM {table}")
    return [row[0] for row in cursor.fetchall()]


role_ids = {r: i+1 for i, r in enumerate(roles)}
department_ids = get_ids("departments")
subject_ids = get_ids("subjects")
school_year_ids = get_ids("school_years")

# Программы и инструменты
program_ids = []
instrument_ids = []
try:
    for i in range(10):
        dept = random.choice(department_ids)
        # Программа
        cursor.execute(
            "INSERT INTO programs (name, department_id) VALUES (?, ?)", (f"Программа {i+1}", dept))
        pid = cursor.lastrowid
        program_ids.append(pid)
        # Инструмент
        cursor.execute("INSERT INTO instruments (name, department_id) VALUES (?, ?)",
                       (fake.word().capitalize(), dept))
        instrument_ids.append(cursor.lastrowid)
        # Связь программ и предметов
        for subj_id in random.sample(subject_ids, 3):
            cursor.execute(
                "INSERT INTO program_subjects (program_id, subject_id, is_required, semester_hours) VALUES (?, ?, ?, ?)",
                (pid, subj_id, random.randint(0, 1), random.randint(18, 36))
            )
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании программ и инструментов: {e}")
    conn.close()
    exit(1)

# Функция для генерации логина


def generate_login(name, year):
    initials = ''.join([part[0].upper() for part in name.split()[:-1]])
    surname = name.split()[-1].capitalize()
    return f"{school_code}_{initials}{surname}{str(year)[2:]}"


# Администраторы
try:
    for _ in range(10):
        name = fake.name()
        year = random.randint(2010, 2024)
        login = generate_login(name, year)
        cursor.execute(
            "INSERT INTO users (login, password, role_id, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (login, fake.password(),
             role_ids["Администратор"], name, fake.phone_number(), fake.email())
        )
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании администраторов: {e}")
    conn.close()
    exit(1)

# Учителя
teacher_ids = []
try:
    for _ in range(30):
        name = fake.name()
        year = random.randint(2010, 2024)
        login = generate_login(name, year)
        cursor.execute(
            "INSERT INTO users (login, password, role_id, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (login, fake.password(),
             role_ids["Учитель"], name, fake.phone_number(), fake.email())
        )
        uid = cursor.lastrowid
        cursor.execute("INSERT INTO teachers (user_id, department_id) VALUES (?, ?)",
                       (uid, random.choice(department_ids)))
        teacher_ids.append(uid)
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании учителей: {e}")
    conn.close()
    exit(1)

# Ученики
student_records = []
try:
    for _ in range(300):
        name = fake.name()
        year = random.choice([2020, 2021, 2022, 2023])
        login = generate_login(name, year)
        cursor.execute(
            "INSERT INTO users (login, password, role_id, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (login, fake.password(),
             role_ids["Ученик"], name, fake.phone_number(), fake.email())
        )
        uid = cursor.lastrowid
        birth = fake.date_of_birth(minimum_age=7, maximum_age=17).isoformat()
        cursor.execute(
            "INSERT INTO students (user_id, birth_date) VALUES (?, ?)", (uid, birth))
        sid = cursor.lastrowid
        student_records.append((sid, uid, year))
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании студентов: {e}")
    conn.close()
    exit(1)

# Родители
parent_count = 250
student_ids = [s[0] for s in student_records]
random.shuffle(student_ids)

# 200 родителей с 1 ребёнком, 50 с 2–3 детьми
single_kids = student_ids[:200]
multi_kids_pool = student_ids[200:]
used_students = set()

try:
    # Родители с одним ребёнком
    for sid in single_kids:
        name = fake.name()
        year = random.choice([2020, 2021, 2022, 2023])
        login = generate_login(name, year)
        cursor.execute(
            "INSERT INTO users (login, password, role_id, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (login, fake.password(),
             role_ids["Родитель"], name, fake.phone_number(), fake.email())
        )
        uid = cursor.lastrowid
        cursor.execute("INSERT INTO parents (user_id) VALUES (?)", (uid,))
        pid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO student_parents (student_id, parent_id) VALUES (?, ?)", (sid, pid))
        used_students.add(sid)

    # Родители с 2–3 детьми
    for _ in range(50):
        name = fake.name()
        year = random.choice([2020, 2021, 2022, 2023])
        login = generate_login(name, year)
        cursor.execute(
            "INSERT INTO users (login, password, role_id, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (login, fake.password(),
             role_ids["Родитель"], name, fake.phone_number(), fake.email())
        )
        uid = cursor.lastrowid
        cursor.execute("INSERT INTO parents (user_id) VALUES (?)", (uid,))
        pid = cursor.lastrowid
        available = list(set(multi_kids_pool) - used_students)
        if not available:
            break
        num_children = min(random.randint(2, 3), len(available))
        children = random.sample(available, num_children)
        for sid in children:
            cursor.execute(
                "INSERT INTO student_parents (student_id, parent_id) VALUES (?, ?)", (sid, pid))
            used_students.add(sid)
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании родителей: {e}")
    conn.close()
    exit(1)

# Назначение программ, классов и инструментов
try:
    cursor.execute("SELECT id FROM students")
    all_students = [row[0] for row in cursor.fetchall()]
    for sid in all_students:
        cursor.execute(
            """INSERT INTO student_years
            (student_id, school_year_id, program_id, instrument_id, class_group, class_letter)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (sid, random.choice(school_year_ids), random.choice(program_ids),
             random.choice(instrument_ids), random.randint(1, 8), random.choice("АБВГ"))
        )
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при создании student_years: {e}")
    conn.close()
    exit(1)

# Расписание, оценки, посещаемость, домашние задания
try:
    # Расписание
    for _ in range(1000):
        cursor.execute(
            """INSERT INTO schedule
            (school_year_id, day_of_week, lesson_number, class_group, class_letter, subject_id, teacher_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (random.choice(school_year_ids), random.randint(1, 6), random.randint(1, 6),
             random.randint(1, 8), random.choice(
                 "АБВГ"), random.choice(subject_ids),
             random.randint(1, 30))
        )

    # Оценки и посещаемость
    cursor.execute("SELECT id FROM student_years")
    sy_ids = [row[0] for row in cursor.fetchall()]
    for sy_id in sy_ids:
        for _ in range(8):
            date = fake.date_between(
                start_date='-2y', end_date='today').isoformat()
            subject_id = random.choice(subject_ids)
            lesson = random.randint(1, 6)
            cursor.execute(
                "INSERT INTO grades (student_year_id, date, subject_id, lesson_number, grade) VALUES (?, ?, ?, ?, ?)",
                (sy_id, date, subject_id, lesson,
                 random.choice(['5', '4', '3']))
            )
            cursor.execute(
                "INSERT INTO attendance (student_year_id, date, subject_id, lesson_number, is_absent) VALUES (?, ?, ?, ?, ?)",
                (sy_id, date, subject_id, lesson, random.choice([0, 1]))
            )

    # Домашние задания
    for _ in range(300):
        cursor.execute(
            """INSERT INTO homework (school_year_id, date, class_group, class_letter, subject_id, text)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (random.choice(school_year_ids), fake.date_between(start_date='-2y', end_date='today').isoformat(),
             random.randint(1, 8), random.choice("АБВГ"), random.choice(subject_ids), fake.text(max_nb_chars=100))
        )
    conn.commit()
except sqlite3.Error as e:
    print(
        f"Ошибка при создании расписания, оценок, посещаемости или домашних заданий: {e}")
    conn.close()
    exit(1)

# Закрытие соединения
print("База данных SQLite успешно наполнена тестовыми данными.")
conn.close()
