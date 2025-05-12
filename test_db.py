from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User

engine = create_engine(
    'mysql+mysqlconnector://OttovonBismark:Sf51OmRsNx4@OttovonBismark.mysql.pythonanywhere-services.com/OttovonBismark%24data?charset=utf8mb4',
    echo=True
)
Session = sessionmaker(bind=engine)
session = Session()

try:
    users = session.query(User).limit(5).all()
    for user in users:
        print(f"Login: {user.login}, Password: {user.password}")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    session.close()
