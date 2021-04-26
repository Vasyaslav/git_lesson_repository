import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class VkInfo(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'vk_info'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    admin_id = sqlalchemy.Column(sqlalchemy.Integer)
    gr_id = sqlalchemy.Column(sqlalchemy.Integer)
    gr_token = sqlalchemy.Column(sqlalchemy.String)
    greetings = sqlalchemy.Column(sqlalchemy.String)
    plus_sub_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    minus_sub_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
