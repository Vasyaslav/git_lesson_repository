import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from data import db_session
from data.vks import VkInfo
import random
import schedule
from multiprocessing import Process


class VkTools():
    def __init__(self):
        self.processes = {}
        self.main()

    def main(self):
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        all_bots = db_sess.query(VkInfo).all()
        for bot in all_bots:
            self.processes[str(bot.id)] = Process(target=self.for_bots, args=(bot,))
            self.processes[str(bot.id)].start()
            schedule.every().day.at('20:33').do(self.sub_count, bot=bot)
        while True:
            schedule.run_pending()

    def terminator(self, some_id):
        for i in self.processes:
            if str(some_id) == i:
                self.processes[i][0].terminate()
                self.processes[i][1].terminate()

    def reload(self):
        for i in self.processes:
            self.processes[i].terminate()
        self.main()

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


if __name__ == "__main__":
    VkTools()
