from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import User, Role, Student, StudentYear, Schedule, Homework, Grade, Subject, Teacher, Session as DBSession
from models.base import engine
import os
import logging
from datetime import datetime
from jinja2 import TemplateNotFound

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация приложения с абсолютным путём к шаблонам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a1b2c3d4e5f67890abcdef1234567890abcdef123456')

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
        logger.error(f"Ошибка при проверке шаблона {template_name}: {e}")
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
            login_user_obj = LoginUser(
                id=user.id,
                login=user.login,
                role_id=user.role_id,
                full_name=user.full_name,
                role_name=role.name if role else 'Неизвестно'
            )
            logger.info(f"Пользователь {user_id} загружен: login={user.login}, role_id={user.role_id}")
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
                role = db_session.query(Role).filter_by(
                    id=user.role_id).first()
                login_user(LoginUser(
                    id=user.id,
                    login=user.login,
                    role_id=user.role_id,
                    full_name=user.full_name,
                    role_name=role.name if role else 'Неизвестно'
                ))
                logger.info(f"Успешная авторизация: {username}, role_id: {user.role_id}")
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
    logger.info(f"Попытка открыть /admin для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 1:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    if not template_exists('admin.html'):
        logger.error("Шаблон admin.html отсутствует")
        return "Шаблон admin.html не найден", 500

    try:
        logger.info(f"Рендеринг admin.html для пользователя {current_user.login}")
        return render_template('admin.html', current_user=current_user)
    except TemplateNotFound as e:
        logger.error(f"Шаблон admin.html не найден: {e}")
        return "Шаблон admin.html не найден", 500
    except Exception as e:
        logger.error(f"Ошибка рендеринга admin.html: {e}")
        return "Внутренняя ошибка сервера", 500

# Страница расписания преподавателя
@app.route('/tr-schedule')
@login_required
def tr_schedule():
    logger.info(f"Попытка открыть /tr-schedule для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id != 2:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    if not template_exists('teacher_schedule.html'):
        logger.error("Шаблон teacher_schedule.html отсутствует")
        return "Шаблон teacher_schedule.html не найден", 500

    try:
        # Заглушка для расписания
        schedule = []
        selected_date = request.args.get('date')
        if selected_date:
            try:
                datetime.strptime(selected_date, '%Y-%m-%d')
                logger.info(f"Выбрана дата: {selected_date}")
            except ValueError:
                logger.warning(f"Неверный формат даты: {selected_date}")
                flash('Неверный формат даты.', 'danger')
                selected_date = None

        logger.info(f"Рендеринг teacher_schedule.html для пользователя {current_user.login}")
        return render_template(
            'teacher_schedule.html',
            current_user=current_user,
            schedule=schedule,
            selected_date=selected_date
        )
    except TemplateNotFound as e:
        logger.error(f"Шаблон teacher_schedule.html не найден: {e}")
        return "Шаблон teacher_schedule.html не найден", 500
    except Exception as e:
        logger.error(f"Ошибка рендеринга teacher_schedule.html: {e}")
        return "Внутренняя ошибка сервера", 500

# Страница дневника


@app.route('/diary')
@login_required
def diary():
    logger.info(f"Попытка открыть /diary для пользователя {current_user.login}, role_id={current_user.role_id}")
    if current_user.role_id not in [3, 4]:
        logger.warning(f"Доступ запрещён для role_id: {current_user.role_id}")
        logout_user()
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('login'))

    try:
        return render_template('diary.html')
    except TemplateNotFound as e:
        logger.error(f"Шаблон diary.html не найден: {e}")
        return "Шаблон diary.html не найден", 500

    # Проверка подключения к базе
    if not check_db_connection():
        flash('Ошибка подключения к базе данных. Попробуйте позже.', 'danger')
        logger.error("Перенаправление на /index из-за ошибки базы")
        return redirect(url_for('index'))

    # Обработка параметра даты
    selected_date = request.args.get('date')
    try:
        if selected_date:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        else:
            selected_date = datetime.now().date()
    except ValueError:
        logger.warning(f"Неверный формат даты: {selected_date}")
        flash('Неверный формат даты.', 'danger')
        selected_date = datetime.now().date()

    db_session = DBSession()
    try:
        # Находим student_id и student_year для текущего пользователя
        student = db_session.query(Student).filter_by(user_id=current_user.id).first()
        if not student:
            logger.warning(f"Пользователь {current_user.login} не является студентом")
            flash('Расписание недоступно: пользователь не зарегистрирован как студент.', 'danger')
            return redirect(url_for('index'))

        # Находим текущий учебный год (предполагаем последний по ID)
        current_year = db_session.query(SchoolYear).order_by(SchoolYear.id.desc()).first()
        if not current_year:
            logger.error("Текущий учебный год не найден")
            flash('Расписание недоступно: учебный год не задан.', 'danger')
            return redirect(url_for('index'))

        student_year = db_session.query(StudentYear).filter_by(
            student_id=student.id,
            school_year_id=current_year.id
        ).first()
        if not student_year:
            logger.warning(f"Для студента {student.id} не найден учебный год")
            flash('Расписание недоступно: данные об учебном годе отсутствуют.', 'danger')
            return redirect(url_for('index'))

        # Инициализация расписания для всех дней
        schedules = {
            1: [],  # Понедельник
            2: [],  # Вторник
            3: [],  # Среда
            4: [],  # Четверг
            5: [],  # Пятница
            6: [],  # Суббота
            7: []   # Воскресенье
        }

        # Запрос расписания из таблицы schedule
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
        ).all()

        for schedule, subject, teacher_user in schedule_items:
            day = schedule.day_of_week
            if day not in schedules:
                continue

            # Находим домашнее задание
            homework = db_session.query(Homework).filter(
                Homework.school_year_id == current_year.id,
                Homework.date == selected_date,
                Homework.class_group == student_year.class_group,
                Homework.class_letter == student_year.class_letter,
                Homework.subject_id == schedule.subject_id
            ).first()

            # Находим оценку
            grade = db_session.query(Grade).filter(
                Grade.student_year_id == student_year.id,
                Grade.date == selected_date,
                Grade.subject_id == schedule.subject_id,
                Grade.lesson_number == schedule.lesson_number
            ).first()

            schedules[day].append({
                'subject': subject.name,
                'homework': homework.text if homework else 'Нет задания',
                'file': 'no_file.pdf',  # Заглушка, пока нет поля для файла
                'grade': grade.grade if grade else '-',
                'teacher': teacher_user.full_name
            })

        # Формируем расписание для шаблона
        monday_schedule = schedules[1]
        tuesday_schedule = schedules[2]
        wednesday_schedule = schedules[3]
        thursday_schedule = schedules[4]
        friday_schedule = schedules[5]
        saturday_schedule = schedules[6]
        sunday_schedule = schedules[7]

        logger.info(f"Рендеринг diary.html для даты {selected_date}, пользователь: {current_user.login}")
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

    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}")
        flash('Произошла ошибка при загрузке расписания.', 'danger')
        return redirect(url_for('index'))
    finally:
        db_session.close()

# Выход


@app.route('/logout')
def logout():
    logger.info(f"Выход пользователя: {current_user.login if current_user.is_authenticated else 'Неизвестный'}")
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
