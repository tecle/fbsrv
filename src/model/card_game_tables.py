# coding:utf-8

from model.table_base import TableBase


class UserInfo(TableBase):
    __primary_key__ = 'uid'

    def __init__(self, **kwargs):
        self.uid = None
        self.openid = None
        self.unionid = None
        self.nick = None
        self.avatar = None
        self.card_num = None
        self.fresh_token = None
        self.last_fresh_time = None
        self.blocked = None
        super(UserInfo, self).__init__(**kwargs)


class Rooms(TableBase):
    __primary_key__ = 'room_id'

    def __init__(self, **kwargs):
        self.room_id = None
        self.owner_id = None
        self.game_type = None
        self.game_conf = None
        self.card_cost = None
        self.open_time = None
        self.stat = None
        super(Rooms, self).__init__(**kwargs)


class NoticeItems(TableBase):
    __primary_key__ = 'notice_id'

    def __init__(self, **kwargs):
        self.notice_id = None
        self.title = None
        self.body = None
        self.summary = None
        super(NoticeItems, self).__init__(**kwargs)


class GameDetail(TableBase):
    __primary_key__ = 'detail_id'

    def __init__(self, **kwargs):
        self.detail_id = None
        self.room_id = None
        self.total_round = None
        self.time_cost = None
        self.credit_info = None
        self.game_log = None
        super(GameDetail, self).__init__(**kwargs)


class UserGameHistory(TableBase):
    __primary_key__ = 'history_id'

    def __init__(self, **kwargs):
        self.history_id = None
        self.uid = None
        self.room_id = None
        self.enter_time = None
        self.game_round = None
        self.credits_got = None
        super(UserGameHistory, self).__init__(**kwargs)
