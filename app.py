from flask import Flask, render_template, redirect, url_for, request, flash, session, Response, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError
from models.reference import SchoolYear, Subject
from models.users import User, Student, Teacher
from models.school import StudentYear, Schedule, Homework, Grade
from models import Session as DBSession
from models.base import engine
import os
import logging
from datetime import datetime
from jinja2 import TemplateNotFound
import random
import string
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация приложения с абсолютным путём к шаблонам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.getenv(
    'FLASK_SECRET_KEY', 'a1b2c3d4e5f67890abcdef1234567890abcdef123456')

# Отладка пути к шаблонам
logger.info(f"Путь к директории шаблонов: {TEMPLATE_DIR}")
if os.path.exists(TEMPLATE_DIR):
    logger.info(f"Директория шаблонов существует: {TEMPLATE_DIR}")
    logger.info(f"Содержимое /templates/: {os.listdir(TEMPLATE_DIR)}")
else:
    logger.error(f"Директория шаблонов не найдена: {TEMPLATE_DIR}")

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

# Проверка существования шаблона


def template_exists(template_name):
    try:
        app.jinja_env.get_template(template_name)
        logger.info(f"Шаблон {template_name} найден")
        return True
    except TemplateNotFound as e:
        logger.error(f"Шаблон {template_name} не найден: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверки шаблона {template_name}: {e}")
        return False

# Класс пользователя для Flask-Login


class LoginUser(UserMixin):
    def __init__(self, id, login, role_id, full_name, role_name, email, phone):
        self.id = id
        self.login = login
        self.role_id = role_id
        self.full_name = full_name
        self.role_name = role_name
        self.email = email
        self.phone = phone

    def get_id(self):
        return str(self.id)

# Функция для определения имени роли по role_id


def get_role_name(role_id):
    role_map = {
        1: 'Администратор',
        2: 'Учитель',
        3: 'Родитель',
        4: 'Ученик'
    }
    return role_map.get(role_id, 'Неизвестно')

# Генерация логина: XXXX_FirstNameInitialMiddleNameInitialLastNameYear


def generate_login(full_name, enrollment_year, db_session):
    # Парсинг full_name: "Фамилия Имя Отчество" или "Фамилия Имя"
    parts = full_name.strip().split()
    if len(parts) < 2:
        raise ValueError(
            "Полное имя должно содержать как минимум фамилию и имя")

    last_name = parts[0]
    first_name = parts[1]
    middle_name = parts[2] if len(parts) > 2 else ""

    # Первая буква имени и отчества (если есть)
    first_initial = first_name[0].upper() if first_name else ""
    middle_initial = middle_name[0].upper() if middle_name else ""

    # 4 случайные цифры
    digits = ''.join(random.choices(string.digits, k=4))

    # Формируем логин
    login = f"{digits}_{first_initial}{middle_initial}{last_name}{enrollment_year}"

    # Проверяем длину (макс. 50 символов)
    if len(login) > 50:
        # Обрезаем last_name, чтобы уложиться
        max_last_name_len = 50 - \
            len(digits) - 1 - len(first_initial) - \
            len(middle_initial) - len(enrollment_year)
        last_name = last_name[:max_last_name_len]
        login = f"{digits}_{first_initial}{middle_initial}{last_name}{enrollment_year}"

    # Проверяем уникальность
    attempt = 0
    original_login = login
    while db_session.query(User).filter_by(login=login).first():
        attempt += 1
        # Добавляем суффикс, если логин занят
        login = f"{original_login}_{attempt}"
        if len(login) > 50:
            # Укорачиваем last_name ещё
            max_last_name_len = 50 - len(digits) - 1 - len(first_initial) - len(
                middle_initial) - len(enrollment_year) - len(f"_{attempt}")
            last_name = last_name[:max_last_name_len]
            login = f"{digits}_{first_initial}{middle_initial}{last_name}{enrollment_year}_{attempt}"

    return login

# Генерация пароля: 10 случайных символов (латиница, цифры, спецсимволы)


def generate_password():
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choices(characters, k=10))

# Валидация номера телефона (+7 и 10 цифр)


def validate_phone(phone):
    pattern = r'^\+7[0-9]{10}$'
    return bool(re.match(pattern, phone))

# Загрузка пользователя


@login_manager.user_loader
def load_user(user_id):
    db_session = DBSession()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if user:
            role_name = get_role_name(user.role_id)
            login_user_obj = LoginUser(
                id=user.id,
                login=user.login,
                role_id=user.role_id,
                full_name=user.full_name,
                role_name=role_name,
                email=user.email,
                phone=user.phone
            )
            logger.info(
                f"Пользователь {user_id} загружен: login={user.login}, role_id={user.role_id}")
            return login_user_obj
        logger.warning(f"Пользователь {user_id} не найден")
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователя {user_id}: {e}")
        return None
    finally:
        db_session.close()

# Проверка подключения к базе


def check_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Подключение к базе данных успешно")
        return True
    except OperationalError as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False

# Главная страница


@app.route('/')
def index():
    logout_user()
    try:
        return render_template('index.html')
    except TemplateNotFound as e:
        logger.error(f"Шаблон index.html не найден: {e}")
        return "Шаблон index.html не найден", 500

# Тестовый маршрут для проверки шаблона


@app.route('/test')
def test():
    logger.info("Попытка рендеринга test с login.html")
    try:
        return render_template('login.html')
    except TemplateNotFound as e:
        logger.error(f"Не удалось рендерить login.html в /test: {e}")
        return "Шаблон login.html не найден", 500
    except Exception as e:
        logger.error(f"Ошибка при рендеринге login.html в /test: {e}")
        return "Ошибка рендеринга шаблона", 500

# Страница входа


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role_id == 1:
            return redirect(url_for('admin'))
        elif current_user.role_id == 2:
            return redirect(url_for('tr_schedule'))
        elif current_user.role_id in [3, 4]:
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
                role_name = get_role_name(user.role_id)
                login_user(LoginUser(
                    id=user.id,
                    login=user.login,
                    role_id=user.role_id,
                    full_name=user.full_name,
                    role_name=role_name,
                    email=user.email,
                    phone=user.phone
                ))
                logger.info(
                    f"Успешная авторизация: {username}, role_id: {user.role_id}")
                if user.role_id == 1:
                    return redirect(url_for('admin'))
                elif user.role_id == 2:
                    return redirect(url_for('tr_schedule'))
                elif user.role_id in [3, 4]:
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

# Страница администратора


@app.route('/admin')
@login_required
def admin():
    logger.info(
        f"Попытка открыть /admin для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    if not template_exists('admin.html'):
        logger.error("Шаблон admin.html отсутствует")
        return "Шаблон admin.html не найден", 500

    try:
        logger.info(
            f"Рендеринг admin.html для пользователя {current_user.login}")
        return render_template('admin.html', current_user=current_user)
    except TemplateNotFound as e:
        logger.error(f"Шаблон admin.html не найден: {e}")
        return "Шаблон admin.html не найден", 500
    except Exception as e:
        logger.error(f"Ошибка рендеринга admin.html: {e}")
        return "Внутренняя ошибка сервера", 500

# Управление пользователями


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    logger.info(
        f"Попытка открыть /admin/users для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    if not template_exists('admin-users.html'):
        logger.error("Шаблон admin-users.html отсутствует")
        return "Шаблон admin-users.html не найден", 500

    db_session = DBSession()
    try:
        search_query = request.form.get(
            'search', '') if request.method == 'POST' else ''
        if search_query:
            # Поиск по full_name, регистронезависимый, частичное совпадение
            users = db_session.query(User).filter(
                User.full_name.ilike(f'%{search_query}%')).all()
            logger.info(
                f"Поиск пользователей по запросу: {search_query}, найдено: {len(users)}")
        else:
            users = db_session.query(User).all()
            logger.info(f"Загрузка всех пользователей: {len(users)}")

        return render_template(
            'admin-users.html',
            current_user=current_user,
            users=users,
            search_query=search_query
        )
    except Exception as e:
        logger.error(f"Ошибка рендеринга admin-users.html: {e}")
        flash('Ошибка при загрузке данных пользователей.', 'danger')
        return redirect(url_for('admin'))
    finally:
        db_session.close()

# Добавление пользователя


@app.route('/admin/users/add', methods=['POST'])
@login_required
def admin_users_add():
    logger.info(
        f"Попытка добавить пользователя от {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    role_id = request.form.get('role_id')
    enrollment_year = request.form.get('enrollment_year')

    if not all([full_name, email, phone, role_id, enrollment_year]):
        logger.warning("Недостаточно данных для добавления пользователя")
        flash('Заполните все поля.', 'danger')
        return redirect(url_for('admin_users'))

    # Валидация
    try:
        role_id = int(role_id)
        if role_id not in [1, 2, 3, 4]:
            logger.warning(f"Недопустимая роль: {role_id}")
            flash('Выбранная роль недопустима.', 'danger')
            return redirect(url_for('admin_users'))
    except ValueError:
        logger.warning(f"Недопустимое значение role_id: {role_id}")
        flash('Недопустимая роль.', 'danger')
        return redirect(url_for('admin_users'))

    if not validate_phone(phone):
        logger.warning(f"Недопустимый номер телефона: {phone}")
        flash('Номер телефона должен быть в формате +7XXXXXXXXXX.', 'danger')
        return redirect(url_for('admin_users'))

    try:
        enrollment_year = int(enrollment_year)
        if not (2000 <= enrollment_year <= 2030):
            logger.warning(f"Недопустимый год зачисления: {enrollment_year}")
            flash('Год зачисления должен быть между 2000 и 2030.', 'danger')
            return redirect(url_for('admin_users'))
    except ValueError:
        logger.warning(
            f"Недопустимое значение года зачисления: {enrollment_year}")
        flash('Год зачисления должен быть числом.', 'danger')
        return redirect(url_for('admin_users'))

    db_session = DBSession()
    try:
        # Проверка уникальности email
        if db_session.query(User).filter_by(email=email).first():
            logger.warning(f"Email {email} уже существует")
            flash('Пользователь с таким email уже существует.', 'danger')
            return redirect(url_for('admin_users'))

        # Генерация логина
        try:
            login = generate_login(full_name, str(enrollment_year), db_session)
        except ValueError as e:
            logger.warning(f"Ошибка генерации логина: {e}")
            flash(str(e), 'danger')
            return redirect(url_for('admin_users'))

        # Генерация пароля
        password = generate_password()

        new_user = User(
            login=login,
            password=password,
            full_name=full_name,
            email=email,
            phone=phone,
            role_id=role_id
        )
        db_session.add(new_user)
        db_session.commit()
        logger.info(
            f"Пользователь добавлен: login={login}, email={email}, phone={phone}, role_id={role_id}")
        flash(
            f'Пользователь успешно добавлен. Логин: {login}, Пароль: {password}', 'success')
    except IntegrityError as e:
        db_session.rollback()
        logger.error(f"Ошибка уникальности при добавлении пользователя: {e}")
        flash('Ошибка: email или логин уже используются.', 'danger')
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при добавлении пользователя: {e}")
        flash('Произошла ошибка при добавлении пользователя.', 'danger')
    finally:
        db_session.close()

    return redirect(url_for('admin_users'))

# Редактирование пользователя


@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
def admin_users_edit(user_id):
    logger.info(
        f"Попытка редактировать пользователя {user_id} от {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        return jsonify({'success': False, 'message': 'Доступ запрещён.'}), 403

    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    role_id = data.get('role_id')

    if not all([full_name, email, phone, role_id]):
        logger.warning("Недостаточно данных для редактирования пользователя")
        return jsonify({'success': False, 'message': 'Заполните все поля.'}), 400

    try:
        role_id = int(role_id)
        if role_id not in [1, 2, 3, 4]:
            logger.warning(f"Недопустимая роль: {role_id}")
            return jsonify({'success': False, 'message': 'Выбранная роль недопустима.'}), 400
    except ValueError:
        logger.warning(f"Недопустимое значение role_id: {role_id}")
        return jsonify({'success': False, 'message': 'Недопустимая роль.'}), 400

    if not validate_phone(phone):
        logger.warning(f"Недопустимый номер телефона: {phone}")
        return jsonify({'success': False, 'message': 'Номер телефона должен быть в формате +7XXXXXXXXXX.'}), 400

    db_session = DBSession()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"Пользователь {user_id} не найден")
            return jsonify({'success': False, 'message': 'Пользователь не найден.'}), 404

        # Проверка уникальности email
        existing_user = db_session.query(User).filter(
            User.email == email, User.id != user_id).first()
        if existing_user:
            logger.warning(
                f"Email {email} уже используется другим пользователем")
            return jsonify({'success': False, 'message': 'Email уже используется.'}), 400

        user.full_name = full_name
        user.email = email
        user.phone = phone
        user.role_id = role_id
        db_session.commit()

        logger.info(
            f"Пользователь {user_id} обновлён: full_name={full_name}, email={email}, phone={phone}, role_id={role_id}")
        return jsonify({
            'success': True,
            'role_name': get_role_name(role_id),
            'phone': phone
        })
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при редактировании пользователя {user_id}: {e}")
        return jsonify({'success': False, 'message': 'Произошла ошибка при сохранении.'}), 500
    finally:
        db_session.close()

# Удаление пользователя


@app.route('/admin/users/delete/<int:user_id>')
@login_required
def admin_users_delete(user_id):
    logger.info(
        f"Попытка удалить пользователя {user_id} от {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    db_session = DBSession()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"Пользователь {user_id} не найден")
            flash('Пользователь не найден.', 'danger')
            return redirect(url_for('admin_users'))

        db_session.delete(user)
        db_session.commit()
        logger.info(f"Пользователь {user_id} удалён")
        flash('Пользователь успешно удалён.', 'success')
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
        flash('Произошла ошибка при удалении пользователя.', 'danger')
    finally:
        db_session.close()

    return redirect(url_for('admin_users'))

# Управление расписанием (заглушка с пуш-уведомлением)


@app.route('/admin/schedule')
@login_required
def admin_schedule():
    logger.info(
        f"Попытка открыть /admin/schedule для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    logger.info("Отправка пуш-уведомления для /admin/schedule")
    js_code = """
    <script>
        if (Notification.permission === 'granted') {
            new Notification('Функционал пока не реализован', {
                body: 'Управление расписанием находится в разработке.',
                icon: '/static/favicon.ico'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification('Функционал пока не реализован', {
                        body: 'Управление расписанием находится в разработке.',
                        icon: '/static/favicon.ico'
                    });
                }
            });
        }
        window.history.back();
    </script>
    """
    return Response(js_code, mimetype='text/html')

# Страница расписания преподавателя


@app.route('/tr-schedule')
@login_required
def tr_schedule():
    logger.info(f"Попытка открыть /tr-schedule для пользователя {current_user.login}, role_id={current_user.role_id}")

    # Установка role_name
    try:
        role = DBSession().query(Role).filter_by(id=current_user.role_id).first()
        current_user.role_name = role.name if role else 'Неизвестно'
        logger.debug(f"Установлен role_name: {current_user.role_name}")
    except Exception as e:
        logger.error(f"Ошибка получения role_name: {str(e)}")
        current_user.role_name = 'Неизвестно'

    # Проверка прав доступа
    if current_user.role_id != 2:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    # Проверка шаблона
    if not template_exists('teacher_schedule.html'):
        logger.error("Шаблон teacher_schedule.html отсутствует")
        return "Шаблон teacher_schedule.html не найден", 500

    db_session = DBSession()
    try:
        # Обработка даты
        selected_date = request.args.get('date')
        if selected_date:
            try:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                logger.info(f"Выбрана дата: {selected_date}")
            except ValueError:
                logger.warning(f"Неверный формат даты: {selected_date}")
                flash('Неверный формат даты.', 'warning')
                selected_date = datetime.now().date()
        else:
            selected_date = datetime.now().date()

        # Проверка учебного года
        current_year = db_session.query(SchoolYear).order_by(SchoolYear.id.desc()).first()
        if not current_year:
            logger.error("Текущий учебный год не найден")
            flash('Учебный год не задан.', 'danger')
            return render_template(
                'teacher_schedule.html',
                current_user=current_user,
                schedule=[],
                selected_date=selected_date.strftime('%Y-%m-%d')
            )

        # Получение teacher_id
        teacher = db_session.query(Teacher).filter_by(user_id=current_user.id).first()
        if not teacher:
            logger.error(f"Пользователь {current_user.login} (user_id={current_user.id}) не является учителем")
            flash('Вы не зарегистрированы как преподаватель.', 'danger')
            return render_template(
                'teacher_schedule.html',
                current_user=current_user,
                schedule=[],
                selected_date=selected_date.strftime('%Y-%m-%d')
            )

        # Получение расписания
        schedule_items = db_session.query(Schedule, Subject).join(
            Subject, Schedule.subject_id == Subject.id
        ).filter(
            Schedule.school_year_id == current_year.id,
            Schedule.teacher_id == teacher.id,
            Schedule.day_of_week == selected_date.weekday()  # 0=понедельник, 6=воскресенье
        ).order_by(Schedule.lesson_number).all()

        logger.debug(f"Найдено {len(schedule_items)} записей в расписании для teacher_id={teacher.id}")

        schedule = []
        for s, sub in schedule_items:
            schedule.append({
                'id': s.id,
                'student_or_group': f"{s.class_group}{s.class_letter}",
                'subject': sub.name
            })

        logger.info(f"Рендеринг teacher_schedule.html для пользователя {current_user.login}")
        return render_template(
            'teacher_schedule.html',
            current_user=current_user,
            schedule=schedule,
            selected_date=selected_date.strftime('%Y-%m-%d')
        )

    except TemplateNotFound as e:
        logger.error(f"Шаблон teacher_schedule.html не найден: {e}")
        return "Шаблон teacher_schedule.html не найден", 500
    except Exception as e:
        logger.error(f"Ошибка рендеринга teacher_schedule.html: {e}", exc_info=True)
        flash('Произошла ошибка при загрузке расписания.', 'danger')
        return render_template(
            'teacher_schedule.html',
            current_user=current_user,
            schedule=[],
            selected_date=selected_date.strftime('%Y-%m-%d')
        )
    finally:
        db_session.close()


# Страница дневника
@app.route('/diary')
@login_required
def diary():
    logger.info(f"Попытка открыть /diary для пользователя {current_user.login}, role_id={current_user.role_id}")

    # Временное решение для role_name
    try:
        role = DBSession().query(Role).filter_by(id=current_user.role_id).first()
        current_user.role_name = role.name if role else 'Неизвестно'
    except Exception as e:
        logger.error(f"Ошибка получения role_name: {str(e)}")
        current_user.role_name = 'Неизвестно'

    # Проверка прав доступа
    error_message = None
    if current_user.role_id not in [3, 4]:
        error_message = 'Доступ разрешён только ученикам и родителям.'
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        flash(error_message, 'danger')

    # Обработка даты
    selected_date = request.args.get('date')
    logger.debug(f"Получен параметр date: {selected_date}")
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date() if selected_date else datetime.now().date()
    except ValueError:
        logger.warning(f"Неверный формат даты: {selected_date}")
        selected_date = datetime.now().date()
        flash('Неверный формат даты.', 'warning')

    # Инициализация расписания
    schedules = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
    db_session = DBSession()
    try:
        # Проверка студента
        student = db_session.query(Student).filter_by(user_id=current_user.id).first()
        if not student:
            error_message = 'Вы не зарегистрированы как студент.'
            logger.error(f"Пользователь {current_user.login} (user_id={current_user.id}) не является студентом")
            flash(error_message, 'danger')
            return render_template(
                'diary.html',
                monday_schedule=schedules[1], tuesday_schedule=schedules[2], wednesday_schedule=schedules[3],
                thursday_schedule=schedules[4], friday_schedule=schedules[5], saturday_schedule=schedules[6],
                sunday_schedule=schedules[7], current_user=current_user, selected_date=selected_date,
                selected_date_str=selected_date.strftime('%Y-%m-%d'), error_message=error_message
            )

        # Проверка учебного года
        current_year = db_session.query(SchoolYear).order_by(SchoolYear.id.desc()).first()
        if not current_year:
            error_message = 'Учебный год не задан.'
            logger.error("Текущий учебный год не найден")
            flash(error_message, 'danger')
            return render_template(
                'diary.html',
                monday_schedule=schedules[1], tuesday_schedule=schedules[2], wednesday_schedule=schedules[3],
                thursday_schedule=schedules[4], friday_schedule=schedules[5], saturday_schedule=schedules[6],
                sunday_schedule=schedules[7], current_user=current_user, selected_date=selected_date,
                selected_date_str=selected_date.strftime('%Y-%m-%d'), error_message=error_message
            )

        # Проверка student_years
        student_year = db_session.query(StudentYear).filter_by(
            student_id=student.id, school_year_id=current_year.id
        ).first()
        if not student_year:
            error_message = 'Данные об учебном годе отсутствуют.'
            logger.error(f"Для студента {student.id} не найден учебный год school_year_id={current_year.id}")
            flash(error_message, 'danger')
            return render_template(
                'diary.html',
                monday_schedule=schedules[1], tuesday_schedule=schedules[2], wednesday_schedule=schedules[3],
                thursday_schedule=schedules[4], friday_schedule=schedules[5], saturday_schedule=schedules[6],
                sunday_schedule=schedules[7], current_user=current_user, selected_date=selected_date,
                selected_date_str=selected_date.strftime('%Y-%m-%d'), error_message=error_message
            )

        # Получение расписания
        schedule_items = db_session.query(Schedule, Subject, User).join(
            Subject, Schedule.subject_id == Subject.id
        ).join(
            Teacher, Schedule.teacher_id == Teacher.id
        ).join(
            User, Teacher.user_id == User.id
        ).filter(
            Schedule.school_year_id == current_year.id,
            Schedule.class_group == student_year.class_group,
            Schedule.class_letter == student_year.class_letter
        ).order_by(Schedule.day_of_week, Schedule.lesson_number).all()

        logger.debug(f"Найдено {len(schedule_items)} записей в расписании")

        for schedule, subject, teacher_user in schedule_items:
            day = schedule.day_of_week
            if day not in schedules:
                logger.warning(f"Недопустимый day_of_week: {day}")
                continue

            homework = db_session.query(Homework).filter(
                Homework.school_year_id == current_year.id,
                Homework.date == selected_date,
                Homework.class_group == student_year.class_group,
                Homework.class_letter == student_year.class_letter,
                Homework.subject_id == schedule.subject_id
            ).first()

            grade = db_session.query(Grade).filter(
                Grade.student_year_id == student_year.id,
                Grade.date == selected_date,
                Grade.subject_id == schedule.subject_id,
                Grade.lesson_number == schedule.lesson_number
            ).first()

            schedules[day].append({
                'subject': subject.name,
                'homework': homework.text if homework else 'Нет задания',
                'file': 'no_file.pdf',  # Заглушка для колонки "Файл"
                'grade': grade.grade if grade else '-',
                'teacher': teacher_user.full_name
            })

    except Exception as e:
        logger.error(f"Ошибка в функции diary: {str(e)}", exc_info=True)
        error_message = 'Произошла ошибка при загрузке расписания.'
        flash(error_message, 'danger')

    finally:
        db_session.close()

    return render_template(
        'diary.html',
        monday_schedule=schedules[1], tuesday_schedule=schedules[2], wednesday_schedule=schedules[3],
        thursday_schedule=schedules[4], friday_schedule=schedules[5], saturday_schedule=schedules[6],
        sunday_schedule=schedules[7], current_user=current_user, selected_date=selected_date,
        selected_date_str=selected_date.strftime('%Y-%m-%d'), error_message=error_message
    )
# Выход


@app.route('/logout')
def logout():
    logger.info(
        f"Выход пользователя: {current_user.login if current_user.is_authenticated else 'Неизвестный'}")
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
