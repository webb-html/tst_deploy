from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField

class RedactForm(FlaskForm):
    title = StringField()
    directory = StringField()
    type = StringField()
    textarea = TextAreaField()
    public = BooleanField()
    submit = SubmitField()