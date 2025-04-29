import sqlite3 as s


class DB:
    def __init__(self):
        self.conn = s.connect("data/data.db")
        self.self.cursor = self.conn.self.cursor()
        self.first_start()

    def first_start(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_years(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS instruments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(id)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects(
                id INTEGER PRIMARY KEY AUTOINCERMENT,
                name TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_subjects(
                id INTEGER PRIMARY KEY AUTOINCERMENT,
                program_id INTEGER,
                subject_id INTEGER,
                FOREIGN KEY (program_id) REFERENCES programs(id),
                FOREIGN KEY (subject_id) REFRENCES subject(id),
                is_required ???????,
                semester_hours INTEGER
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCERMENT,
                login TEXT
                password TEXT,
                role_id INTEGER,
                FOREIGN KEY (role_id) REFRENCES roles(id),
                full_name TEXT,
                phone TEXT,
                email TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
                id INTEGER PRIMARY KEY AUTOINCERMENT,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFRENCES users(id),
                birth_date DATE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_years(
                id INTEGER PRIMARY KEY AUTOINCERMENT,
                student_if
        )
        """)

        def db_yandex_saver(self пользователь списко_изминений):
            тут сейвер пл ключу
