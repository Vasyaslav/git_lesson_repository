from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class BotForm(FlaskForm):
    admin_id = StringField('Введите id одного из администраторов', validators=[DataRequired()])
    group_id = StringField('Введите id группы', validators=[DataRequired()])
    group_token = StringField('Введите токен группы', validators=[DataRequired()])
    greetings = StringField('Введите приветствие для тех, кто напишет сообществу (необязательное поле)')
