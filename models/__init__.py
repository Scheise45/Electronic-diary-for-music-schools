from .base import Base, engine, Session
from .reference import (
    Role, SchoolYear, Department, Instrument, Program, Subject, ProgramSubject
)
from .users import User, Student, Teacher, Parent, StudentParent
from .school import StudentYear, Grade, Attendance, Schedule, Homework


session = Session()


def create_all():
    Base.metadata.create_all(bind=engine)
