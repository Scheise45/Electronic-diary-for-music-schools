from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Пример обработки данных формы
        username = request.form['username']
        password = request.form['password']
        # Здесь можно добавить проверку логина/пароля
        # Для примера: если данные введены, перенаправляем в меню
        if username and password:
            return redirect(url_for('menu'))
        else:
            # Если данные некорректны, можно показать ошибку
            return render_template('login.html', error="Неверный логин или пароль")
    # Для GET-запроса рендерим форму логина
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
