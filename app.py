from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api

from requests import get

from forms.login_form import LoginForm
from forms.register_form import RegisterForm

from data import db_session
from data.users import User

from nt_api import  NoteResource, NoteListResource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jprB?VYVYOn4_6qm$kEsDo@pB5[_0E^gD%zC'
api = Api(app)

api.add_resource(NoteListResource, '/api/notes')
api.add_resource(NoteResource, '/api/notes/<int:id>')

login_manager = LoginManager()
login_manager.init_app(app)

APP_URL = 'http://127.0.0.1:8080'

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        notes_json = get(f'{APP_URL}/api/notes').json()
        dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id]
        dict_notes = dict()
        for dir in dir_list:
            dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                               note['directory'] == dir]
        return render_template('note_list.html', title='Главная',
                               dir_list=sorted(list(set(dir_list))), dict_notes=dict_notes)
    return render_template('base.html', title='Главная')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login_template.html', title='Авторизация', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_repeat.data:
            return render_template('register_template.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register_template.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register_template.html', title='Регистрация', form=form)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User,user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    db_session.global_init("db/data.db")
    app.run(port=8080, host='127.0.0.1')