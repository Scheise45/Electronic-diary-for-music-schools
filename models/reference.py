from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))  # Указываем длину


class SchoolYear(Base):
    __tablename__ = "school_years"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))


class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class ProgramSubject(Base):
    __tablename__ = "program_subjects"
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    is_required = Column(Boolean)  # Изменено на Boolean
    semester_hours = Column(Integer)
