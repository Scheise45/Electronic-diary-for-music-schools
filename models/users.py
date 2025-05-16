from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    login = Column(String(50))  # Указываем длину
    password = Column(String(255))  # Для хэшей паролей
    role_id = Column(Integer, ForeignKey("roles.id"))
    full_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    birth_date = Column(Date)


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    user = relationship("User", backref="teacher")

class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))


class StudentParent(Base):
    __tablename__ = "student_parents"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    parent_id = Column(Integer, ForeignKey("parents.id"))
