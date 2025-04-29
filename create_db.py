import sqlite3

conn = sqlite3.connect("data/data.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Справочники
cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS school_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENTs,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS program_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER,
    subject_id INTEGER,
    is_required INTEGER,
    semester_hours INTEGER,
    FOREIGN KEY (program_id) REFERENCES programs(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
""")

# Основные сущности
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT,
    password TEXT,
    role_id INTEGER,
    full_name TEXT,
    phone TEXT,
    email TEXT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    birth_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    school_year_id INTEGER,
    program_id INTEGER,
    instrument_id INTEGER,
    class_group INTEGER,
    class_letter TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (school_year_id) REFERENCES school_years(id),
    FOREIGN KEY (program_id) REFERENCES programs(id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    department_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_parents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    parent_id INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (parent_id) REFERENCES parents(id)
)
""")

# Оценки и посещаемость
cursor.execute("""
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_year_id INTEGER,
    date DATE,
    subject_id INTEGER,
    lesson_number INTEGER,
    grade TEXT,
    FOREIGN KEY (student_year_id) REFERENCES student_years(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_year_id INTEGER,
    date DATE,
    subject_id INTEGER,
    lesson_number INTEGER,
    is_absent INTEGER,
    FOREIGN KEY (student_year_id) REFERENCES student_years(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
""")

# Расписание и домашка
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_year_id INTEGER,
    day_of_week INTEGER,
    lesson_number INTEGER,
    class_group INTEGER,
    class_letter TEXT,
    subject_id INTEGER,
    teacher_id INTEGER,
    FOREIGN KEY (school_year_id) REFERENCES school_years(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS homework (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_year_id INTEGER,
    date DATE,
    class_group INTEGER,
    class_letter TEXT,
    subject_id INTEGER,
    text TEXT,
    FOREIGN KEY (school_year_id) REFERENCES school_years(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
""")

conn.commit()
conn.close()
