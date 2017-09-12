# coding: utf-8

import json

from data_defines import BaseData, ListWrapper


class SendGiftData(object):
    __slots__ = ['nick', 'level', 'gift', 'time', 'amount']

    def __init__(self):
        self.nick = None
        self.level = 1
        self.gift = None
        self.time = None
        self.amount = 1

    def ParseFromObj(self, obj):
        self.nick = obj['nick']
        self.level = obj['level']
        self.gift = obj['gift']
        self.time = obj['time']
        self.amount = obj['amount']


class DefaultGiftData(object):
    __slots__ = []

    def ParseFromObj(self, obj):
        pass


class LiveRequest(object):
    __slots__ = ['reqId', 'reqType', 'reqData']
    DATA_FACTORY = {
        0: DefaultGiftData,
        1: SendGiftData,
    }

    def __init__(self):
        self.reqId = None
        self.reqType = None
        self.reqData = None

    def ParseFromString(self, s):
        obj = json.loads(s)
        self.reqId = obj['reqId']
        self.reqType = obj['reqType']
        self.reqData = self.DATA_FACTORY.get(self.reqType, DefaultGiftData)()
        self.reqData.ParseFromObj(obj[['reqData']])


class LiveDetail(BaseData):
    class UserInfo(object):
        __slots__ = ['vipLevel', 'gold']

        def __init__(self):
            self.vipLevel = 1
            self.gold = 0

        def SerializeBody(self):
            return {
                "vl": self.vipLevel,
                "gold": self.gold
            }

    class LiveInfo(object):
        __slots__ = ['isLiving', 'vipLevel', 'charm', 'pullUrl', 'chatRoomId', 'gameType']

        def __init__(self):
            self.isLiving = True
            self.vipLevel = 1
            self.charm = 0
            self.pullUrl = ''
            self.chatRoomId = 0
            self.gameType = 0

        def SerializeBody(self):
            return {
                'lving': self.isLiving,
                'vl': self.vipLevel,
                'charm': self.charm,
                'pull': self.pullUrl,
                'rid': self.chatRoomId,
                'gt': self.gameType
            }

    def __init__(self):
        self.user = self.UserInfo()
        self.live = self.LiveInfo()
        self.success = True
        self.errCode = 0
        super(LiveDetail, self).__init__()

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.errCode

    def SerializeBody(self):
        return {
            "user": self.user.SerializeBody(),
            "live": self.live.SerializeBody()
        }


class CurrentLiving(BaseData):
    class LiveDetail(object):
        def __init__(self):
            self.ownerId = None
            self.nick = None
            self.avatar = None
            self.sign = None
            self.born = None
            self.gender = None
            self.location = None
            self.cover = None
            self.title = None
            self.chatRoomId = None
            self.pullUrl = None

        def SerializeBody(self):
            return {
                "oid": self.ownerId,
                "nick": self.nick,
                "at": self.avatar,
                "sign": self.sign,
                "born": self.born,
                "gender": self.gender,
                "site": self.location,
                "cover": self.cover,
                "title": self.title,
                "chatRoom": self.chatRoomId,
                "pullUrl": self.pullUrl
            }

    def __init__(self):
        self.data = ListWrapper(self.LiveDetail)
        super(CurrentLiving, self).__init__()

    def SerializeBody(self):
        return [itr.SerializeBody() for itr in self.data]


class CreateLiveResult(BaseData):
    def __init__(self):
        self.success = None
        self.chatRoomId = None
        self.gold = None
        self.watched = None
        self.charm = None
        self.pushUrl = None
        self.channelId = None
        self.expireTime = None
        super(CreateLiveResult, self).__init__()

    def GetSuccess(self):
        return self.success

    def SerializeBody(self):
        return {
            "rid": self.chatRoomId,
            "gold": self.gold,
            "watched": self.watched,
            "charm": self.charm,
            "push": self.pushUrl,
            "cid": self.channelId,
            "et": self.expireTime
        }

    def InitByJsonBody(self, obj):
        self.chatRoomId = obj["rid"]
        self.gold = obj["gold"]
        self.watched = obj["watched"]
        self.charm = obj["charm"]
        self.pushUrl = obj["push"]
        self.channelId = obj["cid"]
        self.expireTime = obj['et']

    def SetSuccess(self, success):
        self.success = success


class LiveBizData(BaseData):
    def __init__(self):
        self.data_type = None
        self.success = False
        self.err_code = 0
        self.gold = 0
        self.charm = 0
        super(LiveBizData, self).__init__()

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.err_code

    def SerializeBody(self):
        return {
            'gold': self.gold,
            'charm': self.charm,
            'type': self.data_type
        }


class LiveGames(BaseData):
    def __init__(self):
        self.ver = None
        self.games = None
        super(LiveGames, self).__init__()

    def SerializeBody(self):
        return {
            'ver': self.ver,
            'games': self.games
        }


class RankData(BaseData):
    class RankItem(object):
        def __init__(self):
            self.user_id = None
            self.avatar = None
            self.nick_name = None
            self.contribution = None

    def __init__(self):
        self.data = ListWrapper(self.RankItem)
        super(RankData, self).__init__()

    def SerializeBody(self):
        return [{
                    'id': item.user_id,
                    'at': item.avatar,
                    'nick': item.nick_name,
                    'val': item.contribution
                } for item in self.data]
