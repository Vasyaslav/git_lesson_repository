from flask import Flask, jsonify, render_template, redirect, request
from flask_jwt_simple import JWTManager
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from datetime import timedelta
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'some really secret key'
app.config["JWT_SECRET_KEY"] = 'ultra_very_super_secret'
app.config["JWT_EXPIRES"] = timedelta(hours=24)
app.config["JWT_IDENTITY_CLAIM"] = 'user'
app.config["JWT_HEADER_NAME"] = 'authorization'
app.jwt = JWTManager(app)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start_page():
    db_sess = db_session.create_session()
    return render_template('based.html', title='Начальная страница')


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if form.password.data != form.password.repeat.data:
            return render_template('regs.html', title='Регистрация', form=form, message='Пароли не совпадают.')
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('regs.html', title='Регистрация', form=form,
                                   message='Пользователь с такой почтой уже существует.')
        user = User(surname=form.surname.data,
                    name=form.name.data,
                    email=form.email.data)
        user.hashing_password(form.password.data)
        db_sess.commit()
        return jsonify({'Успех': 'Но шаблоны ещё не созданы...'})
    return render_template('regs.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return jsonify({'Успех': 'вы залогинились.'})
    return render_template('login.html', title='Авторизация', form=form)


def main():
    db_session.global_init('db/storage.db')
    app.run()


if __name__ == '__main__':
    main()
