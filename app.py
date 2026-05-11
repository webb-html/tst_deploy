from flask import Flask, redirect, render_template, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask import request as flask_request

from requests import get, post, put, delete

from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.redact_note_form import RedactForm
from forms.delete_note_form import DeleteForm

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
        type_list = [note['type'] for note in notes_json['note'] if note['user_id'] == current_user.id]
        dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id]
        dict_notes = dict()
        for dir in dir_list:
            dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                               note['directory'] == dir][::-1]
        return render_template('note_list_template.html', title='Главная',
                               dir_list=sorted(list(set(dir_list))), dict_notes=dict_notes,
                               type_list=sorted(list(set(type_list)))[1:])
    return render_template('please_register_template.html', title='Главная')

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

@app.route('/user/<user_name>/<int:note_id>', methods=['GET', 'POST'])
def open_note(user_name, note_id):
    notes_json = get(f'{APP_URL}/api/notes').json()
    form = RedactForm()
    current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]
    if form.validate_on_submit():
        put(f'{APP_URL}/api/notes/{note_id}', json={'title': form.title.data, 'content': form.textarea.data,
                                               'directory': form.directory.data, 'type': form.type.data,
                                               'public': form.public.data, 'user_id': current_note['user_id']})
        notes_json = get(f'{APP_URL}/api/notes').json()
        current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]
    if current_user.is_authenticated:
        if current_user.id == current_note['user_id']:
            form.public.data = current_note['public']
            form.textarea.data = current_note['content']
            return render_template('redact_note_template.html', form=form,
                                   title=current_note['title'], directory=current_note['directory'],
                                   type=current_note['type'], user_name=user_name, note_id=note_id)
    if current_note['public']:
        return render_template('view_note_template.html', title=current_note['title'],
                               directory=current_note['directory'], type=current_note['type'],
                               textarea=current_note['content'])
    else:
        return render_template("don't_have_permission.html")

@app.route('/user/<user_name>/<int:note_id>/delete', methods=['GET', 'POST'])
def delete_note(user_name, note_id):
    notes_json = get(f'{APP_URL}/api/notes').json()
    form = DeleteForm()
    current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]
    if form.validate_on_submit():
        delete(f'{APP_URL}/api/notes/{note_id}')
        return redirect('/')
    if current_user.is_authenticated:
        if current_user.id == current_note['user_id']:
            return render_template('delete_note_template.html', form=form, user_name=user_name,
                                   note_id=note_id)
    return render_template("don't_have_permission.html")

@app.route('/add_note')
def add_note():
    post(f'{APP_URL}/api/notes', json={'title': 'Новая заметка', 'content': '', 'directory': '',
                                       'type': 'НОВАЯ ЗАМЕТКА', 'public': False, 'user_id': current_user.id})
    return redirect('/')

@app.route('/search')
def search():
    query = flask_request.args.get('search-request')
    notes_json = get(f'{APP_URL}/api/notes').json()
    dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id
                and (query.lower() in note['title'].lower() or query.lower() in note['content'].lower())]
    dict_notes = dict()
    for dir in dir_list:
            dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                               note['directory'] == dir and (query.lower() in note['title'].lower()
                               or query.lower() in note['content'].lower())][::-1]
    return render_template('search_result.html', title='Главная',
                                    dir_list=sorted(list(set(dir_list))), dict_notes=dict_notes)

@app.route('/filter')
def _filter():
    query = flask_request.args.get('filter-request')
    notes_json = get(f'{APP_URL}/api/notes').json()
    dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id
                and query.lower() in note['type'].lower()]
    dict_notes = dict()
    for dir in dir_list:
        dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                           note['directory'] == dir and query.lower() in note['type'].lower()][::-1]
    return render_template('search_result.html', title='Главная',
                           dir_list=sorted(list(set(dir_list))), dict_notes=dict_notes)

if __name__ == '__main__':
    db_session.global_init("db/data.db")
    app.run(port=8080, host='127.0.0.1')