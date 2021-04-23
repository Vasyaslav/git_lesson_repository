import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from data import db_session
from data.vks import VkInfo
import random
import schedule
from multiprocessing import Process, freeze_support


class VkTools():
    def __init__(self):
        processes = {}
        self.main()

    def sub_count(self, bot, dbsess, vksess, adm_id):
        vk = vksess.get_api()
        vk.messages.send(user_id=adm_id,
                     message=f'''Кол-во новых подписок на сообщество: {bot.plus_sub_count}\n
                                 Кол-во отписок: {bot.minus_sub_count}''',
                     random_id=random.randint(0, 2 ** 64))
        bot.plus_sub_count = 0
        bot.minus_sub_count = 0
        dbsess.commit()

    def for_bots(self, bot, sess):
        vk_session = vk_api.VkApi(token=bot.gr_token)
        longpoll = VkBotLongPoll(vk_session, bot.gr_id)
        admin_id = bot.admin_id
        schedule.every().day.at('21:52').do(sub_count, vksess=vk_session, bot=bot, adm_id=admin_id, dbsess=sess)

        for event in longpoll.listen():
            if event.type == VkBotEventType.GROUP_JOIN:
                bot.plus_sub_count += 1
                sess.commit()
            if event.type == VkBotEventType.GROUP_LEAVE:
                bot.minus_sub_count += 1
                sess.commit()
            if event.type == VkBotEventType.MESSAGE_NEW:
                vk = vk_session.get_api()
                vk.messages.send(user_id=event.obj.message['from_id'],
                             message=f"{bot.greetings}",
                             random_id=random.randint(0, 2 ** 64))

    def main(self):
        db_session.global_init('db/storage.db')
        db_sess = db_session.create_session()
        all_bots = db_sess.query(VkInfo).all()
        for bot in all_bots:
            b = Process(target=for_bots, args=(bot, db_sess))
            b.start()


if __name__ == "__main__":
    freeze_support()
    VkTools()
