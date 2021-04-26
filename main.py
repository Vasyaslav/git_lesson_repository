from flask import Flask, render_template, redirect
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from data import db_session
from data.users import User
from data.vks import VkInfo
from forms.user import RegisterForm, LoginForm
from forms.vk_form import BotForm
from multiprocessing import Process
import schedule
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


class VkTools():
    """Невозможно использовать multiprocessing без конструкции
    if __name__ == '__main__' """

    def __init__(self):
        self.processes = [{}, []]
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        all_bots = db_sess.query(VkInfo).all()
        for i in all_bots:
            self.processes[1].append(str(i.id))
        self.main_start()

    def main_start(self, bot_id=('del', -15)):
        if bot_id != ('del', -15):
            if bot_id[0] == 'up':
                self.processes.append([str(bot_id[1])])
        self.main_proc = Process(target=self.main, args=(self.processes,))
        self.main_proc.start()

    def main(self, process):
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        all_bots = db_sess.query(VkInfo).all()
        for bot in all_bots:
            if str(bot.id) in self.processes[-1]:
                self.processes[0][str(bot.id)] = (Process(target=self.for_bots, args=(bot,)), bot.id)
                self.processes[0][str(bot.id)][0].start()
                print(bot.id)
                schedule.every().day.at('12:00').do(self.sub_count, bot=bot)
        while True:
            schedule.run_pending()

    def sub_count(self, bot):
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        vk_session = vk_api.VkApi(token=bot.gr_token)
        vk = vk_session.get_api()
        vk.messages.send(user_id=bot.admin_id,
                         message=f'''Кол-во новых подписок на сообщество: {bot.plus_sub_count}\n
                                 Кол-во отписок: {bot.minus_sub_count}''',
                         random_id=random.randint(0, 2 ** 64))
        bot.plus_sub_count = 0
        bot.minus_sub_count = 0
        db_sess.commit()

    def for_bots(self, bot):
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        try:
            vk_session = vk_api.VkApi(token=bot.gr_token)
            longpoll = VkBotLongPoll(vk_session, bot.gr_id)
            admin_id = bot.admin_id
            schedule.every(5).seconds.do(self.sub_count, vksess=vk_session, bot=bot, adm_id=admin_id)
            for event in longpoll.listen():
                if event.type == VkBotEventType.GROUP_JOIN:
                    bot.plus_sub_count += 1
                    db_sess.commit()
                if event.type == VkBotEventType.GROUP_LEAVE:
                    bot.minus_sub_count += 1
                    db_sess.commit()
                if event.type == VkBotEventType.MESSAGE_NEW:
                    vk = vk_session.get_api()
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=f"{bot.greetings}",
                                     random_id=random.randint(0, 2 ** 64))
        except vk_api.exceptions.ApiError:
            false_bot = db_sess.query(VkInfo).filter(VkInfo.gr_token == bot.gr_token).first()
            db_sess.delete(false_bot)
            db_sess.commit()
            return redirect(f'/bot_delete/{str(false_bot)}')


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
    print(bot_api.processes)
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


@app.route('/new_form', methods=['GET', 'POST'])
def new_form():
    form = BotForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(VkInfo).filter(VkInfo.gr_id == int(form.group_id.data)).first():
            return render_template('bot.html', title='Создание бота', form=form,
                                   message='Сообщество с таким id уже есть')
        bot = VkInfo(admin_id=int(form.admin_id.data),
                     gr_id=int(form.group_id.data),
                     gr_token=form.group_token.data,
                     greetings=form.greetings.data,
                     user_id=current_user.id)
        db_sess.add(bot)
        db_sess.commit()
        bot_api.main_start(bot_id=('up', bot.id))
        return redirect('/profile')
    return render_template('bot.html', title='Создание бота', form=form)


def main():
    db_session.global_init('db/storage.db')
    app.run()


if __name__ == '__main__':
    bot_api = VkTools()
    main()
