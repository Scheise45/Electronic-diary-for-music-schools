import sqlite3 as s

conn = s.connect("data/data.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Роли
roles = [("Ученик",), ("Родитель",), ("Учитель",), ("Администрация",)]
cursor.executemany("INSERT INTO roles (name) VALUES (?)", roles)

# Учебные года
school_years = [("2023/2024",), ("2024/2025",)]
cursor.executemany("INSERT INTO school_years (name) VALUES (?)", school_years)

# Отделение
cursor.execute("INSERT INTO departments (name) VALUES (?)", ("Фортепианное",))
department_id = cursor.lastrowid

# Инструменты
instruments = [("Фортепиано", department_id), ("Синтезатор", department_id)]
cursor.executemany(
    "INSERT INTO instruments (name, department_id) VALUES (?, ?)", instruments)

# Программы
programs = [("Предпрофессиональная программа", department_id),
            ("Общеразвивающая программа", department_id)]
cursor.executemany(
    "INSERT INTO programs (name, department_id) VALUES (?, ?)", programs)

# Предметы
subjects = [("Сольфеджио",), ("Музыкальная литература",), ("Специальность",)]
cursor.executemany("INSERT INTO subjects (name) VALUES (?)", subjects)

# Связь программ с предметами
program_ids = [row[0] for row in cursor.execute("SELECT id FROM programs")]
subject_ids = [row[0] for row in cursor.execute("SELECT id FROM subjects")]
for pid in program_ids:
    for sid in subject_ids:
        cursor.execute("""
        INSERT INTO program_subjects (program_id, subject_id, is_required, semester_hours)
        VALUES (?, ?, ?, ?)
        """, (pid, sid, 1, 34))

# Функции для добавления пользователей, студентов, родителей


def add_user(login, password, role_id, full_name, phone, email):
    cursor.execute("""
    INSERT INTO users (login, password, role_id, full_name, phone, email)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (login, password, role_id, full_name, phone, email))
    return cursor.lastrowid


def add_student(full_name, birth_date, phone, email, year_id, program_id, instrument_id):
    user_id = add_user(f"{full_name}_login", "pass",
                       1, full_name, phone, email)
    cursor.execute(
        "INSERT INTO students (user_id, birth_date) VALUES (?, ?)", (user_id, birth_date))
    student_id = cursor.lastrowid
    cursor.execute("""
    INSERT INTO student_years (student_id, school_year_id, program_id, instrument_id, class_group, class_letter)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, year_id, program_id, instrument_id, 1, "А"))
    return student_id


def add_parent(full_name, phone, email):
    user_id = add_user(f"{full_name}_login", "pass",
                       2, full_name, phone, email)
    cursor.execute("INSERT INTO parents (user_id) VALUES (?)", (user_id,))
    return cursor.lastrowid


def link_student_parent(student_id, parent_id):
    cursor.execute(
        "INSERT INTO student_parents (student_id, parent_id) VALUES (?, ?)", (student_id, parent_id))


# Добавление учеников и родителей
instrument_ids = [row[0]
                  for row in cursor.execute("SELECT id FROM instruments")]
year_id = cursor.execute(
    "SELECT id FROM school_years WHERE name = '2024/2025'").fetchone()[0]

for pid in program_ids:
    for i in range(3):
        student = f"Ученик_{pid}_{i}"
        parent = f"Родитель_{pid}_{i}"
        sid = add_student(student, "2010-05-10", "89990001122",
                          f"{student}@mail.ru", year_id, pid, instrument_ids[i % len(instrument_ids)])
        pid_ = add_parent(parent, "89991112233", f"{parent}@mail.ru")
        link_student_parent(sid, pid_)

# Учителя
teacher1_id = add_user("teacher1", "pass", 3, "Петров Петр",
                       "89992223344", "petrov@mail.ru")
teacher2_id = add_user("teacher2", "pass", 3,
                       "Сидоров Сидор", "89993334455", "sidorov@mail.ru")
cursor.execute("INSERT INTO teachers (user_id, department_id) VALUES (?, ?)",
               (teacher1_id, department_id))
cursor.execute("INSERT INTO teachers (user_id, department_id) VALUES (?, ?)",
               (teacher2_id, department_id))

conn.commit()
conn.close()
