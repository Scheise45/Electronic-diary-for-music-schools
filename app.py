from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import sessionmaker
from models import User, Role, Session as DBSession
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация приложения
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv(
    'FLASK_SECRET_KEY', 'a1b2c3d4e5f67890abcdef1234567890abcdef123456')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Проверка существования шаблона


def template_exists(template_name):
    try:
        app.jinja_env.get_template(template_name)
        logger.info(f"Шаблон {template_name} найден")
        return True
    except Exception as e:
        logger.error(f"Шаблон {template_name} не найден: {e}")
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

# Загрузка пользователя


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
        logger.error(f"Ошибка загрузки пользователя {user_id}: {e}")
        return None
    finally:
        db_session.close()

# Главная страница


@app.route('/')
def index():
    logout_user()
    if not template_exists('index.html'):
        logger.error("Шаблон index.html отсутствует")
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
        logger.error("Шаблон login.html отсутствует")
        return "Шаблон login.html не найден", 500

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            logger.warning("Попытка входа без логина или пароля")
            flash('Введите логин и пароль.', 'danger')
            return render_template('login.html')

        db_session = DBSession()
        try:
            user = db_session.query(User).filter_by(login=username).first()
            if user and user.password == password:  # Проверка без хеширования
                role = db_session.query(Role).filter_by(
                    id=user.role_id).first()
                login_user(LoginUser(
                    id=user.id,
                    login=user.login,
                    role_id=user.role_id,
                    full_name=user.full_name,
                    role_name=role.name if role else 'Неизвестно'
                ))
                logger.info(
                    f"Успешная авторизация: {username}, role_id: {user.role_id}")
                if user.role_id in [3, 4]:
                    return redirect(url_for('diary'))
                logout_user()
                flash('Функционал для вашей роли пока не реализован.', 'warning')
                return redirect(url_for('login'))
            else:
                logger.warning(f"Неверный логин или пароль: {username}")
                flash('Неверный логин или пароль.', 'danger')
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            flash('Произошла ошибка. Попробуйте снова.', 'danger')
        finally:
            db_session.close()

    return render_template('login.html')

# Страница дневника


@app.route('/diary')
@login_required
def diary():
    logger.info(
        f"Попытка открыть /diary для пользователя {current_user.login}, role_id: {current_user.role_id}")
    if current_user.role_id not in [3, 4]:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    if not template_exists('diary.html'):
        logger.error("Шаблон diary.html отсутствует")
        return "Шаблон diary.html не найден", 500

    # Обработка параметра даты
    selected_date = request.args.get('date')
    try:
        if selected_date:
            datetime.strptime(selected_date, '%Y-%m-%d')
        else:
            selected_date = datetime.now().strftime('%Y-%m-%d')
    except ValueError:
        logger.warning(f"Неверный формат даты: {selected_date}")
        flash('Неверный формат даты.', 'danger')
        selected_date = datetime.now().strftime('%Y-%m-%d')

    # Пример расписания (заменить на запрос к базе)
    monday_schedule = [
        {
            'subject': 'Фортепиано',
            'homework': 'Практика этюда №5',
            'file': 'etude5.pdf',
            'grade': '5',
            'teacher': 'Иванова А.Б.'
        }
    ] if '2025-05-12' in selected_date else []
    tuesday_schedule = [
        {
            'subject': 'Сольфеджио',
            'homework': 'Решить задания 1-3',
            'file': 'solfeggio.pdf',
            'grade': '4',
            'teacher': 'Петров В.С.'
        }
    ] if '2025-05-13' in selected_date else []
    wednesday_schedule = [
        {
            'subject': 'Вокал',
            'homework': 'Разучить песню',
            'file': 'song.pdf',
            'grade': '5',
            'teacher': 'Сидорова Е.В.'
        }
    ] if '2025-05-14' in selected_date else []
    thursday_schedule = [
        {
            'subject': 'Скрипка',
            'homework': 'Практика гамм',
            'file': 'scales.pdf',
            'grade': '4',
            'teacher': 'Козлов Д.А.'
        }
    ] if '2025-05-15' in selected_date else []
    friday_schedule = [
        {
            'subject': 'Теория музыки',
            'homework': 'Прочитать главу 3',
            'file': 'theory.pdf',
            'grade': '5',
            'teacher': 'Михайлова О.П.'
        }
    ] if '2025-05-16' in selected_date else []
    saturday_schedule = [
        {
            'subject': 'Ансамбль',
            'homework': 'Подготовить партию',
            'file': 'ensemble.pdf',
            'grade': '4',
            'teacher': 'Лебедев С.Н.'
        }
    ] if '2025-05-17' in selected_date else []
    sunday_schedule = []  # Воскресенье без уроков

    logger.info(f"Рендеринг diary.html для даты {selected_date}")
    return render_template(
        'diary.html',
        monday_schedule=monday_schedule,
        tuesday_schedule=tuesday_schedule,
        wednesday_schedule=wednesday_schedule,
        thursday_schedule=thursday_schedule,
        friday_schedule=friday_schedule,
        saturday_schedule=saturday_schedule,
        sunday_schedule=sunday_schedule,
        current_user=current_user
    )

# Выход


@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Обработка ошибок


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Ошибка 500: {error}")
    return "Внутренняя ошибка сервера", 500


@app.errorhandler(404)
def not_found(error):
    logger.error(f"Ошибка 404: {error}")
    return "Страница не найдена", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
