from models import session
from models.reference import (Role, SchoolYear, Department, Instrument,
                              Program, Subject, ProgramSubject)
from models.users import User, Student, Parent, StudentParent, Teacher
from models.school import StudentYear
from datetime import date

# Роли
roles = ["Ученик", "Родитель", "Учитель", "Администрация"]
session.add_all([Role(name=r) for r in roles])

# Учебные годы
years = ["2023/2024", "2024/2025"]
session.add_all([SchoolYear(name=y) for y in years])

# Отделение
department = Department(name="Фортепианное")
session.add(department)
session.flush()  # чтобы получить department.id

# Инструменты
instruments = [
    Instrument(name="Фортепиано", department_id=department.id),
    Instrument(name="Синтезатор", department_id=department.id),
]
session.add_all(instruments)
session.flush()

# Программы
programs = [
    Program(name="Предпрофессиональная программа",
            department_id=department.id),
    Program(name="Общеразвивающая программа", department_id=department.id),
]
session.add_all(programs)
session.flush()

# Предметы
subjects = [
    Subject(name="Сольфеджио"),
    Subject(name="Музыкальная литература"),
    Subject(name="Специальность"),
]
session.add_all(subjects)
session.flush()

# Связь программ и предметов
for program in programs:
    for subject in subjects:
        ps = ProgramSubject(
            program_id=program.id,
            subject_id=subject.id,
            is_required=True,
            semester_hours=34
        )
        session.add(ps)

# Функции для добавления


def add_user(login, password, role_id, full_name, phone, email):
    user = User(login=login, password=password, role_id=role_id,
                full_name=full_name, phone=phone, email=email)
    session.add(user)
    session.flush()
    return user.id


def add_student(full_name, birth_date, phone, email, year_id, program_id,
                instrument_id):
    user_id = add_user(f"{full_name}_login", "pass",
                       1, full_name, phone, email)
    student = Student(user_id=user_id, birth_date=birth_date)
    session.add(student)
    session.flush()
    sy = StudentYear(
        student_id=student.id,
        school_year_id=year_id,
        program_id=program_id,
        instrument_id=instrument_id,
        class_group=1,
        class_letter="А"
    )
    session.add(sy)
    return student.id


def add_parent(full_name, phone, email):
    user_id = add_user(f"{full_name}_login", "pass",
                       2, full_name, phone, email)
    parent = Parent(user_id=user_id)
    session.add(parent)
    session.flush()
    return parent.id


def link_student_parent(student_id, parent_id):
    sp = StudentParent(student_id=student_id, parent_id=parent_id)
    session.add(sp)


# Ученики и родители
instrument_ids = [inst.id for inst in instruments]
year = session.query(SchoolYear).filter_by(name="2024/2025").first()

for program in programs:
    for i in range(3):
        student_name = f"Ученик_{program.id}_{i}"
        parent_name = f"Родитель_{program.id}_{i}"
        sid = add_student(student_name, date(2010, 5, 10), "89990001122",
                          f"{student_name}@mail.ru", year.id, program.id, instrument_ids[i % len(instrument_ids)])
        pid = add_parent(parent_name, "89991112233", f"{parent_name}@mail.ru")
        link_student_parent(sid, pid)

# Учителя
teacher1_id = add_user("teacher1", "pass", 3, "Петров Петр",
                       "89992223344", "petrov@mail.ru")
teacher2_id = add_user("teacher2", "pass", 3,
                       "Сидоров Сидор", "89993334455", "sidorov@mail.ru")
session.add(Teacher(user_id=teacher1_id, department_id=department.id))
session.add(Teacher(user_id=teacher2_id, department_id=department.id))

# Сохранение
session.commit()
