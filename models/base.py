from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Подключение к MySQL базе на PythonAnywhere
engine = create_engine(
    "mysql+mysqlconnector://OttovonBismark:your_password@OttovonBismark.mysql.pythonanywhere-services.com/OttovonBismark$data?charset=utf8mb4",
    echo=False
)

Session = sessionmaker(bind=engine)

Base = declarative_base()
