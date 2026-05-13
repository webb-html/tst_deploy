from flask_wtf import FlaskForm
from wtforms import SubmitField

class DeleteForm(FlaskForm): # форма для удаления заметки
    submit = SubmitField('Удалить')