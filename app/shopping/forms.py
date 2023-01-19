
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length


from flask_wtf import FlaskForm
from wtforms import widgets, RadioField, SelectMultipleField, SubmitField, SelectField

class ReviewForm(FlaskForm):
    sort = SelectField('sorting', choices=[('5', '5'), ('4', '4'), ('3', '3'), ('2', '2'), ('1', '1')])
    message = TextAreaField('message_review', validators=[DataRequired()])
    rating = RadioField('Label', choices=[('5', ''), ('4', ''), ('3', ''), ('2', ''), ('1', '')])

class SortForm(FlaskForm):
    sort = SelectField('sorting',  choices=[('Default', 'Умолчанию'), ('Date.max', 'дате по возрастанию'), ('Date.min', 'дате по убыванию'), ('Rating.max', 'оценкам по возрастанию'), ('Rating.min', 'оценкам по убыванию'), ('Useful.min', 'полезности по возрастанию'), ('Useful.max', 'полезности по убыванию')])

class CheckboxForm(FlaskForm):
    photo_stock = BooleanField('C Фото')