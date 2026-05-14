from flask import Flask, redirect, render_template, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask import request as flask_request

from requests import get, post, put, delete

from io import BytesIO # необходимо для загрузки заметки в файле без его создания

import os

from waitress import serve # для запуска сервера

from forms.login_form import LoginForm # импортирование форм
from forms.register_form import RegisterForm
from forms.redact_note_form import RedactForm
from forms.delete_note_form import DeleteForm

from data import db_session
from data.users import User

from nt_api import  NoteResource, NoteListResource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jprB?VYVYOn4_6qm$kEsDo@pB5[_0E^gD%zC'
api = Api(app)

api.add_resource(NoteListResource, '/api/notes') # api
api.add_resource(NoteResource, '/api/notes/<int:id>')

login_manager = LoginManager() # инициализация менеджера для управления текущим пользователем
login_manager.init_app(app)

APP_URL = 'http://127.0.0.1:5000'

@app.route('/')
@app.route('/index')
def index(): # главная страница
    if current_user.is_authenticated:
        notes_json = get(f'{APP_URL}/api/notes').json()

        # списки всех заметок и всех папок
        dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id]
        dict_notes = dict()
        for dir in dir_list:
            dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                               note['directory'] == dir][::-1]

        return render_template('note_list_template.html',
                               dir_list=sorted(list(set(dir_list))),
                               dict_notes=dict_notes)
    # просьба зайти если не зашел
    return render_template('notification_template.html',
                           content='Пожалуйста, зарегистрируйтесь или войдите',
                           type='rg')

@app.route('/login', methods=['GET', 'POST'])
def login(): # вход
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data) # выполнение входы
            return redirect("/") # переадресация на главную
        # если что-то неверно
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login_template.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register(): # регистрация
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_repeat.data: # если не совпадают пароли
            return render_template('register_template.html',
                                   form=form,
                                   message="Пароли не совпадают")

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first(): # пользователь уже существует
            return render_template('register_template.html',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # добавление нового пользователя
        user = User(name=form.name.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login') # переадресация на страницу для входа
    return render_template('register_template.html', form=form)

@login_manager.user_loader
def load_user(user_id): # загрузить пользователя
    db_sess = db_session.create_session()
    return db_sess.get(User,user_id)

@app.route('/logout')
@login_required
def logout(): # выход пользователя
    logout_user()
    return redirect("/")

# <user_name> нигде не используется и служит больше как маркер автора заметки
@app.route('/user/<user_name>/<int:note_id>', methods=['GET', 'POST'])
def open_note(user_name, note_id): # открытие записки
    notes_json = get(f'{APP_URL}/api/notes').json()
    form = RedactForm()

    try:
        current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0] # получение текущей заметки
    except Exception:
        return render_template('notification_template.html',
                               content='Эта страница не найдена',
                               type='nf') # заметки не существует

    if form.validate_on_submit(): # сохранение заметки
        put(f'{APP_URL}/api/notes/{note_id}', json={'title': form.title.data,
                                                    'content': form.textarea.data,
                                                    'directory': form.directory.data,
                                                    'type': form.type.data,
                                                    'public': form.public.data,
                                                    'user_id': current_note['user_id']})

        notes_json = get(f'{APP_URL}/api/notes').json() # обновление информации для получения уже измененной заметки
        current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]

    if current_user.is_authenticated:
        if current_user.id == current_note['user_id']: # загрузка редактирования заметки
            form.public.data = current_note['public']
            form.textarea.data = current_note['content']
            return render_template('redact_note_template.html',
                                   form=form,
                                   title=current_note['title'],
                                   directory=current_note['directory'],
                                   type=current_note['type'],
                                   user_name=user_name,
                                   note_id=note_id)

    if current_note['public']: # если открыта для просмотра
        return render_template('view_note_template.html',
                               title=current_note['title'],
                               directory=current_note['directory'],
                               type=current_note['type'],
                               textarea=current_note['content'],
                               user_name=user_name,
                               note_id=note_id)
    else: # иначе ошибка нет доступа
        return render_template("notification_template.html",
                               content='Вы не имеете доступа к этой странице',
                               type='pr')

@app.route('/user/<user_name>/<int:note_id>/delete', methods=['GET', 'POST'])
def delete_note(user_name, note_id): # удаление заметки
    notes_json = get(f'{APP_URL}/api/notes').json()
    form = DeleteForm()
    current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]

    if form.validate_on_submit():
        delete(f'{APP_URL}/api/notes/{note_id}') # собственно удаление
        return redirect('/')

    if current_user.is_authenticated:
        if current_user.id == current_note['user_id']: # если создатель страницы
            return render_template('delete_note_template.html',
                                   form=form,
                                   user_name=user_name,
                                   note_id=note_id)
    # остальные не могут получить доступ к странице
    return render_template("notification_template.html",
                           content='Вы не имеете доступа к этой странице',
                           type='pr')

@app.route('/add_note')
def add_note(): # добавление заметки
    post(f'{APP_URL}/api/notes', json={'title': 'Новая заметка',
                                       'content': '',
                                       'directory': '',
                                       'type': 'НОВАЯ ЗАМЕТКА',
                                       'public': False,
                                       'user_id': current_user.id})
    return redirect('/')

@app.route('/search')
def search(): # поиск
    query = flask_request.args.get('search-request') # получение информации от HTMX
    notes_json = get(f'{APP_URL}/api/notes').json()
    # списки подходящих папок и заметок в них
    dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id
                and (query.lower() in note['title'].lower() or query.lower() in note['content'].lower())]
    dict_notes = dict()
    for dir in dir_list:
            dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                               note['directory'] == dir and (query.lower() in note['title'].lower()
                               or query.lower() in note['content'].lower())][::-1]

    return render_template('search_result.html',
                           dir_list=sorted(list(set(dir_list))),
                           dict_notes=dict_notes)

@app.route('/filter') # фильтр
def _filter(): # фильтр по темам
    query = flask_request.args.get('filter-request') # получение информации от HTMX
    notes_json = get(f'{APP_URL}/api/notes').json()
    # списки подходящих папок и заметок
    dir_list = [note['directory'] for note in notes_json['note'] if note['user_id'] == current_user.id
                and query == note['type']]
    dict_notes = dict()
    for dir in dir_list:
        dict_notes[dir] = [note for note in notes_json['note'] if note['user_id'] == current_user.id and
                           note['directory'] == dir and query == note['type']][::-1]

    return render_template('search_result.html',
                           dir_list=sorted(list(set(dir_list))),
                           dict_notes=dict_notes)

@app.route('/user/<user_name>/<int:note_id>/download')
def download_note(user_name, note_id): # скачивание файла
    notes_json = get(f'{APP_URL}/api/notes').json()
    current_note = list(filter(lambda x: x['id'] == note_id, notes_json['note']))[0]

    if current_user.is_authenticated:
        if current_user.id == current_note['user_id']: # если автор
            return send_file(BytesIO(current_note['content'].encode('utf-8')),
                             download_name=current_note['title'] + '.txt',
                             as_attachment=True) # начало загрузки файла
    if current_note['public']: # если публичный
        return send_file(BytesIO(current_note['content'].encode('utf-8')),
                         download_name=current_note['title'] + '.txt',
                         as_attachment=True)

if __name__ == '__main__':
    db_session.global_init("db/data.db")
    print(f'server is running {APP_URL}')
    serve(app, port=os.environ.get("PORT", 5000), host='0.0.0.0')