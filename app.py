from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy.orm import sessionmaker
from models import User, Session as DBSession

app = Flask(__name__)

# Главная страница


@app.route('/')
def index():
    return render_template('index.html')

# Страница входа


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверка через SQLAlchemy
        db_session = DBSession()
        try:
            user = db_session.query(User).filter_by(
                login=username, password=password).first()
            if user:
                # Успешная авторизация
                return redirect(url_for('menu'))
            else:
                # Неверный логин или пароль
                return render_template('login.html', error="Неверный логин или пароль")
        except Exception as e:
            return render_template('login.html', error=f"Ошибка: {str(e)}")
        finally:
            db_session.close()

    # Для GET-запроса рендерим форму логина
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
