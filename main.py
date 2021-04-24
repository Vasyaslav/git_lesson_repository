from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from data import db_session
from data.users import User
from data.vks import VkInfo
from forms.user import RegisterForm, LoginForm
from vk import VkTools

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some really secret key'
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile')
@login_required
def profile():
    db_sess = db_session.create_session()
    bots = db_sess.query(VkInfo).filter(VkInfo.user_id == current_user.id)
    for i in bots:
        print(i.gr_id)
    return render_template('profile.html', title='Профиль', bots=bots)


@app.route('/bot_delete/<int:bot_id>')
@login_required
def deletor(bot_id):
    db_sess = db_session.create_session()
    bot = db_sess.query(VkInfo).get(bot_id)
    if bot:
        db_sess.delete(bot)
        db_sess.commit()
    return redirect('/profile')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start_page():
    return render_template('based.html', title='Начальная страница')


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if form.password.data != form.password_repeat.data:
            return render_template('regs.html', title='Регистрация', form=form, message='Пароли не совпадают.')
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('regs.html', title='Регистрация', form=form,
                                   message='Пользователь с такой почтой уже существует.')
        user = User(name=form.name.data,
                    email=form.email.data)
        user.hashing_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('regs.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f'/profile')
        return render_template('login.html', title='Авторизация', form=form, message='Неверный пароль')
    return render_template('login.html', title='Авторизация', form=form)


def main():
    db_session.global_init('db/storage.db')
    app.run()


if __name__ == '__main__':
    main()
