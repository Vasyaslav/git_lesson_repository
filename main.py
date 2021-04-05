from flask import Flask, jsonify, render_template, redirect, request
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'some really secret key'
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

    return render_template('base.html', title='Начальная страница')


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if form.password.data != form.password.repeat.data:
            return jsonify({'Ошибка': 'Пароли не совпадают.'})
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return jsonify({'Ошибка': 'Пользователь с такой почтой уже существует.'})
        user = User(surname=form.surname.data,
                    name=form.name.data,
                    email=form.email.data)
        user.hashing_password(form.password.data)
        db_sess.commit()
        return jsonify({'Успех': 'Но шаблоны ещё не созданы...'})
    return jsonify({'Ошибка': 'Не все поля заполнены.'})


@app.route('/login', methods=['GET'])
def login():
    form = LoginForm
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return jsonify({'Успех': 'вы залогинились.'})
    return jsonify({'Ошибка': 'Неправильный email или пароль.'})


def main():
    db_session.global_init('db/storage.db')
    app.run()


if __name__ == '__main__':
    main()
