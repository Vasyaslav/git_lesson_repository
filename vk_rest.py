from flask_restful import reqparse, abort, Api, Resource
from data import db_session
from data.users import User
from data.vks import VkInfo

db_session.global_init('db/storage.db')


class Bot_Resource(Resource):
    def get(self, bot_id):
        db_sess = db_session.create_session()
        bot = db_sess.query(VkInfo).get(bot_id)
        return bot
