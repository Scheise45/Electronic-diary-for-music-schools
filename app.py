from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import sessionmaker
from models import User, Role, Session as DBSession
import os

# Явно указываем папку шаблонов
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv(
    'FLASK_SECRET_KEY', 'a1b2c3d4e5f67890abcdef1234567890abcdef123456')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Проверка шаблонов


def template_exists(template_name):
    try:
        app.jinja_env.get_template(template_name)
        print(f"Шаблон {template_name} найден")
        return True
    except Exception as e:
        print(f"Ошибка: Шаблон {template_name} не найден: {e}")
        return False

# Класс пользователя для Flask-Login


class LoginUser(UserMixin):
    def __init__(self, id, login, role_id, full_name, role_name):
        self.id = id
        self.login = login
        self.role_id = role_id
        self.full_name = full_name
        self.role_name = role_name

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False


@login_manager.user_loader
def load_user(user_id):
    db_session = DBSession()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if user:
            role = db_session.query(Role).filter_by(id=user.role_id).first()
            return LoginUser(
                id=user.id,
                login=user.login,
                role_id=user.role_id,
                full_name=user.full_name,
                role_name=role.name if role else 'Неизвестно'
            )
        return None
    except Exception as e:
        print(f"Ошибка в load_user: {e}")
        return None
    finally:
        db_session.close()

# Главная страница


@app.route('/')
def index():
    logout_user()
    if not template_exists('index.html'):
        return "Шаблон index.html не найден", 500
    logout_user()
    if not template_exists('index.html'):
        return "Шаблон index.html не найден", 500
    return render_template('index.html')

# Страница входа


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role_id in [3, 4]:
            return redirect(url_for('diary'))
        logout_user()
        flash('Функционал для вашей роли пока не реализован.', 'warning')

    if not template_exists('login.html'):
        return "Шаблон login.html не найден", 500

    if current_user.is_authenticated:
        if current_user.role_id in [3, 4]:
            return redirect(url_for('diary'))
        logout_user()
        flash('Функционал для вашей роли пока не реализован.', 'warning')

    if not template_exists('login.html'):
        return "Шаблон login.html не найден", 500

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверка через SQLAlchemy
        db_session = DBSession()
        try:
            user = db_session.query(User).filter_by(login=username).first()
            if user and user.password == password:
                role = db_session.query(Role).filter_by(
                    id=user.role_id).first()
                login_user(LoginUser(
                    id=user.id,
                    login=user.login,
                    role_id=user.role_id,
                    full_name=user.full_name,
                    role_name=role.name if role else 'Неизвестно'
                ))
                db_session.commit()

                print(
                    f"Успешная авторизация: {username}, role_id: {user.role_id}")

                if user.role_id in [3, 4]:
                    return redirect(url_for('diary'))
                else:
                    # TODO: Вернуться к обработке других role_id (1 - Администратор, 2 - Учитель)
                    logout_user()
                    flash('Функционал для вашей роли пока не реализован.', 'warning')
                    return redirect(url_for('login'))
            else:
                print(f"Неверный логин или пароль: {username}")
                print(f"Неверный логин или пароль: {username}")
                return render_template('login.html', error="Неверный логин или пароль")
        except Exception as e:
            db_session.rollback()
            print(f"Ошибка в login: {e}")
            db_session.rollback()
            print(f"Ошибка в login: {e}")
            return render_template('login.html', error=f"Ошибка: {str(e)}")
        finally:
            db_session.close()

    # Для GET-запроса рендерим форму логина
    return render_template('login.html')

# Страница дневника


@app.route('/diary')
@login_required
def diary():
    # if current_user.role_id not in [3, 4]:
    #     logout_user()
    #     flash('Доступ запрещён.', 'danger')
    #     return redirect(url_for('login'))

    # if not template_exists('diary.html'):
    #     return "Шаблон diary.html не найден", 500

    # schedule = [
    #     {
    #         'start_time': '10:00',
    #         'end_time': '11:00',
    #         'subject': 'Фортепиано',
    #         'homework': 'Практика этюда №5',
    #         'file': 'etude5.pdf',
    #         'grade': '5',
    #         'teacher': 'Иванова А.Б.'
    #     },
    #     {
    #         'start_time': '11:30',
    #         'end_time': '12:30',
    #         'subject': 'Сольфеджио',
    #         'homework': 'Решить задания 1-3',
    #         'file': 'solfeggio.pdf',
    #         'grade': '4',
    #         'teacher': 'Петров В.С.'
    #     }
    # ]

    return render_template('diary.html')

# Выход


@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Обработка ошибок 500


@app.errorhandler(500)
def internal_error(error):
    print(f"Ошибка 500: {error}")
    return "Внутренняя ошибка сервера", 500


if __name__ == '__main__':
    app.run(debug=True)
