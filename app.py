from flask import Flask, render_template, redirect, url_for, request, session, flash
from sqlalchemy.orm import sessionmaker
from models import User, Role, Session as DBSession

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Замените на случайный ключ для продакшена

# Проверка авторизации
def is_authenticated():
    return 'user_id' in session

# Главная страница
@app.route('/')
def index():
    if is_authenticated():
        return redirect(url_for('diary'))
    return render_template('index.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_authenticated():
        return redirect(url_for('diary'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Проверка через SQLAlchemy
        db_session = DBSession()
        try:
            user = db_session.query(User).filter_by(login=username, password=password).first()
            if user:
                # Сохраняем данные в сессии
                session['user_id'] = user.id
                session['role_id'] = user.role_id
                session['full_name'] = user.full_name
                role = db_session.query(Role).filter_by(id=user.role_id).first()
                session['role_name'] = role.name if role else 'Неизвестно'
                
                # Проверка role_id
                if user.role_id in [3, 4]:  # Ученик или Родитель
                    return redirect(url_for('diary'))
                else:
                    # TODO: Вернуться к обработке других role_id (1 - Администратор, 2 - Учитель)
                    flash('Функционал для вашей роли пока не реализован.', 'warning')
                    return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Неверный логин или пароль")
        except Exception as e:
            return render_template('login.html', error=f"Ошибка: {str(e)}")
        finally:
            db_session.close()
    
    return render_template('login.html')

# Страница дневника (для Ученика и Родителя)
@app.route('/diary')
def diary():
    if not is_authenticated():
        flash('Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('login'))
    
    if session['role_id'] not in [3, 4]:
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('index'))
    
    # Заглушка для расписания
    schedule = [
        {
            'start_time': '10:00',
            'end_time': '11:00',
            'subject': 'Фортепиано',
            'homework': 'Практика этюда №5',
            'file': 'etude5.pdf',
            'grade': '5',
            'teacher': 'Иванова А.Б.'
        },
        {
            'start_time': '11:30',
            'end_time': '12:30',
            'subject': 'Сольфеджио',
            'homework': 'Решить задания 1-3',
            'file': 'solfeggio.pdf',
            'grade': '4',
            'teacher': 'Петров В.С.'
        }
    ]
    
    current_user = {
        'name': session.get('full_name', 'Неизвестно'),
        'role': session.get('role_name', 'Неизвестно')
    }
    
    return render_template('diary.html', schedule=schedule, current_user=current_user)

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)