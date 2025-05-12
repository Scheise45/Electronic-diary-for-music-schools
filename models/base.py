from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Подключение к MySQL базе на PythonAnywhere (mysqlconnector)
engine = create_engine(
    'mysql+mysqlconnector://OttovonBismark:Sf51OmRsNx4@OttovonBismark.mysql.pythonanywhere-services.com/OttovonBismark$data?charset=utf8mb4',
    echo=True
)

Session = sessionmaker(bind=engine)
Base = declarative_base()
