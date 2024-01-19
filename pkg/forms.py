from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, BooleanField, DateField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, URL, Length

#file
from flask_wtf.file import FileField, FileAllowed, FileRequired


class BreakoutForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    image = FileField(validators=[FileRequired(),FileAllowed(['jpg','jpeg','png'],"We only allow images")])
    # status = RadioField('Status', choices=['0','1'], validators=[DataRequired()])
    submit = SubmitField('Add Topic!')