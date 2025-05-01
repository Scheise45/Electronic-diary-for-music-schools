from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Text
from .base import Base


class StudentYear(Base):
    __tablename__ = "student_years"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    school_year_id = Column(Integer, ForeignKey("school_years.id"))
    program_id = Column(Integer, ForeignKey("programs.id"))
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    class_group = Column(Integer)
    class_letter = Column(String(10))  # Например, "А", "Б"


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True)
    student_year_id = Column(Integer, ForeignKey("student_years.id"))
    date = Column(Date)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    lesson_number = Column(Integer)
    grade = Column(String(10))  # Уточняем длину для оценок


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    student_year_id = Column(Integer, ForeignKey("student_years.id"))
    date = Column(Date)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    lesson_number = Column(Integer)
    is_absent = Column(Boolean)  # Изменено на Boolean


class Schedule(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True)
    school_year_id = Column(Integer, ForeignKey("school_years.id"))
    day_of_week = Column(Integer)
    lesson_number = Column(Integer)
    class_group = Column(Integer)
    class_letter = Column(String(10))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))


class Homework(Base):
    __tablename__ = "homework"
    id = Column(Integer, primary_key=True)
    school_year_id = Column(Integer, ForeignKey("school_years.id"))
    date = Column(Date)
    class_group = Column(Integer)
    class_letter = Column(String(10))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    text = Column(Text)  # Изменено на Text для длинных текстов
