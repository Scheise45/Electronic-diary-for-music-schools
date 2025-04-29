from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return "<h2>Меню (пока заглушка)</h2>"


if __name__ == '__main__':
    app.run(debug=True)
