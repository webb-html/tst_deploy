from flask import Flask, redirect, render_template

from forms.login_form import LoginForm
from forms.register_form import RegisterForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'jprB?VYVYOn4_6qm$kEsDo@pB5[_0E^gD%zC'

@app.route('/')
@app.route('/index')
def index():
    return 'ok'

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('login_template.html', title='Авторизация', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_repeat.data:
            return render_template('register_template.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        return redirect('/')
    return render_template('register_template.html', title='Регистрация', form=form)

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')