from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField

class RedactForm(FlaskForm): # форма для редактирования заметок
    title = StringField()
    directory = StringField()
    type = StringField()
    textarea = TextAreaField()
    public = BooleanField()
    submit = SubmitField()