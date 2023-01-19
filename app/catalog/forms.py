
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length



from flask_wtf import FlaskForm
from wtforms import widgets, RadioField, SelectMultipleField, SubmitField, SelectField






class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class SimpleForm(FlaskForm):
    brand = MultiCheckboxField('label')
    color = MultiCheckboxField('label')
    size = MultiCheckboxField('label')
    minprice = StringField('price')
    maxprice = StringField('price')
    submit_brand = SubmitField('apply')
    submit_color = SubmitField('apply')
    submit_all = SubmitField('apply')
    submit_size = SubmitField('apply')
    submit_price = SubmitField('apply')
    submit_all_filter = SubmitField('Применить')

    cancel = SubmitField('Сброс')


class SortForm(FlaskForm):
    sort = SelectField('sorting', choices=[('Default', 'By popularity'), ('Price.max', 'Ascending prices'), ('Price.min', 'Descending prices'), ('Default', 'Title'), ('Default', 'Rating')])



class ReviewForm(FlaskForm):
    sort = SelectField('sorting', choices=[('5', '5'), ('4', '4'), ('3', '3'), ('2', '2'), ('1', '1')])
    message = TextAreaField('message_review', validators=[DataRequired()])
    rating = RadioField('Label', choices=[('5', ''), ('4', ''), ('3', ''), ('2', ''), ('1', '')])
