from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class SchoolYear(Base):
    __tablename__ = "school_years"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))


class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class ProgramSubject(Base):
    __tablename__ = "program_subjects"
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    is_required = Column(Integer)  # 0 или 1
    semester_hours = Column(Integer)
