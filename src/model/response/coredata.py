# coding: utf-8
import json

from data_defines import BaseData, ListWrapper


class DataShell(BaseData):
    def __init__(self):
        self.data = None
        super(DataShell, self).__init__()
        self.success = True
        self.errCode = 0

    def SerializeBody(self):
        return self.data

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.errCode


class Strings(BaseData):
    def __init__(self):
        self.data = []
        super(Strings, self).__init__()

    def SerializeBody(self):
        return self.data


class AppVersion(BaseData):
    def __init__(self):
        self.version = None
        self.cargo = None
        self.banner = None
        super(AppVersion, self).__init__()

    def SerializeBody(self):
        return {
            'ver': self.version,
            'cargo': self.cargo,
            'banner': self.banner
        }


class Status(BaseData):
    def __init__(self):
        self.data = None
        self.success = True
        self.code = 0
        super(Status, self).__init__()

    def SerializeBody(self):
        return {'data': self.data}

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.code


class LoginInfo(BaseData):
    def __init__(self):
        self.success = True
        self.errCode = 0
        self.userId = None
        self.yxToken = None
        self.sysToken = None
        self.nickname = None
        self.avatar = None
        self.sign = None
        self.born = None
        self.hobbies = None
        self.gender = None
        self.pics = None
        super(LoginInfo, self).__init__()

    def GetSuccess(self):
        return self.success

    def SerializeBody(self):
        return {
            "id": self.userId,
            "yx": self.yxToken,
            "tkn": self.sysToken,
            "nick": self.nickname,
            "avatar": self.avatar,
            "sign": self.sign,
            "born": self.born,
            "hobbies": self.hobbies,
            "gender": self.gender,
            "pics": self.pics
        }

    def GetErrCode(self):
        return self.errCode


class WxLoginInfo(BaseData):
    def __init__(self):
        self.success = None
        self.userId = None
        self.yxToken = None
        self.errCode = 0
        self.sysToken = None
        self.avatar = None
        self.nickname = None
        super(WxLoginInfo, self).__init__()

    def GetSuccess(self):
        return self.success

    def SerializeBody(self):
        return {
            "id": self.userId,
            "yx": self.yxToken,
            "tkn": self.sysToken,
            "at": self.avatar,
            "nick": self.nickname
        }

    def GetErrCode(self):
        return self.errCode


class HobbyList(BaseData):
    class Status(object):
        __slots__ = ['success', 'code']

        def __init__(self):
            self.success = False
            self.code = 0

    def __init__(self):
        self.data = []
        self.status = self.Status()
        super(HobbyList, self).__init__()

    def SerializeBody(self):
        return {'hobbies': self.data}

    def GetErrCode(self):
        return self.status.code

    def GetSuccess(self):
        return self.status.success


class UserMetaInfo(BaseData):
    def __init__(self):
        self.id = None  # int
        self.avatar = ''
        self.vipLevel = 1  # int
        self.isMale = False  # bool or int
        self.nickName = ''
        self.third = ''
        self.signature = ''
        self.status = ''
        super(UserMetaInfo, self).__init__()

    def SerializeBody(self):
        return {
            'id': self.id,
            'at': self.avatar,
            'vl': self.vipLevel,
            'sex': 1 if self.isMale else 0,
            'nick': self.nickName,
            '3rd': self.third,
            'sign': self.signature,
            'st': self.status
        }

    def InitByJsonBody(self, json_obj):
        self.id = json_obj['id']
        self.avatar = json_obj['at']
        self.vipLevel = json_obj['vl']
        self.isMale = json_obj['sex'] > 0
        self.nickName = json_obj['nick']
        self.third = json_obj['3rd']
        self.signature = json_obj['sign']
        self.status = json_obj['st']


class UsersMetaInfo(BaseData):
    def __init__(self):
        self.users = ListWrapper(UserMetaInfo)
        super(UsersMetaInfo, self).__init__()

    def add(self):
        n = UserMetaInfo()
        self.users.append(n)
        return n

    def SerializeBody(self):
        return {'users': [item.SerializeBody() for item in self.users]}

    def InitByJsonBody(self, obj):
        for item in obj['users']:
            tmp = self.add()
            tmp.InitByJsonBody(item)

    def ParseFromString(self, s):
        obj = json.loads(s)
        self.InitByJsonBody(obj['body'])


class UserDetail(BaseData):
    def __init__(self):
        self.id = None
        self.avatar = ''
        self.nickName = ''
        self.sign = ''
        self.isMale = True
        self.born = ''
        self.star = 0
        self.hobbies = []
        self.pics = ''
        self.location = ''
        self.isAnchor = False
        self.isLiving = False
        self.raw_pics = None
        self.gold = 0
        super(UserDetail, self).__init__()

    def SerializeBody(self):
        return {
            'id': self.id,
            'at': self.avatar,
            'nik': self.nickName,
            'sn': self.sign,
            'sex': 1 if self.isMale else 0,
            'brt': self.born,
            'star': self.star,
            'hby': self.hobbies,
            'pics': self.pics,
            'raw_pics': self.raw_pics,
            'loc': self.location,
            'ach': self.isAnchor,
            'lvn': self.isLiving,
            'gd': self.gold
        }

    def InitByJsonBody(self, json_obj):
        self.id = json_obj['id']
        self.avatar = json_obj['at']
        self.nickName = json_obj['nik']
        self.sign = json_obj['sn']
        self.isMale = json_obj['sex'] > 0
        self.born = json_obj['brt']
        self.star = json_obj['star']
        self.hobbies = json_obj['hby']
        self.pics = json_obj['pics']
        self.raw_pics = json_obj['raw_pics']
        self.location = json_obj['loc']
        self.isAnchor = json_obj['ach']
        self.isLiving = json_obj['lvn']
        self.gold = json_obj['gd']


class UserVisitors(BaseData):
    class VisitInfo(object):
        def __init__(self):
            self.userId = None
            self.visitTime = None
            self.nickname = None
            self.sign = None
            self.birthday = None
            self.location = None
            self.sex = None
            self.avatar = None
            self.isLiving = None
            self.star = None

    def __init__(self):
        self.visitors = []
        super(UserVisitors, self).__init__()

    def add(self):
        n = self.VisitInfo()
        self.visitors.append(n)
        return n

    def SerializeBody(self):
        return {'vs': [
            {
                'id': item.userId,
                'time': item.visitTime,
                'nick': item.nickname,
                'sign': item.sign,
                'born': item.birthday,
                'site': item.location,
                'sex': item.sex,
                'at': item.avatar,
                'lving': item.isLiving,
                'star': item.star
            } for item in self.visitors]}


class RecommendUsers(BaseData):
    class UserItem(object):
        __slots__ = ['userId', 'vipLevel', 'longitude', 'latitude', 'nickname', 'status', 'avatar', 'birth', 'gender',
                     'sign', 'site', 'star']

        def __init__(self):
            self.userId = None
            self.vipLevel = None
            self.longitude = None
            self.latitude = None
            self.nickname = None
            self.status = None
            self.avatar = None
            self.birth = None
            self.gender = None
            self.sign = None
            self.site = None
            self.star = None

        def SerializeBody(self):
            return {
                "uid": self.userId,
                "vl": self.vipLevel,
                "lon": self.longitude,
                "lat": self.latitude,
                "nick": self.nickname,
                "st": self.status,
                "at": self.avatar,
                "birth": self.birth,
                "sex": self.gender,
                "sign": self.sign,
                "site": self.site,
                "star": self.star
            }

        def InitByJsonBody(self, obj):
            self.userId = obj["uid"]
            self.vipLevel = obj["vl"]
            self.longitude = obj["lon"]
            self.latitude = obj["lat"]
            self.nickname = obj["nick"]
            self.status = obj["st"]
            self.avatar = obj["at"]
            self.birth = obj["birth"]
            self.gender = obj["sex"]
            self.sign = obj["sign"]
            self.site = obj['site']
            self.star = obj['star']

    def __init__(self):
        self.success = False
        self.code = 0
        self.users = ListWrapper(self.UserItem)
        super(RecommendUsers, self).__init__()

    def add(self):
        n = self.UserItem()
        self.users.append(n)
        return n

    def SerializeBody(self):
        return {'users': [item.SerializeBody() for item in self.users]}

    def InitByJsonBody(self, json_obj):
        for item in json_obj['users']:
            n = self.add()
            n.InitByJsonBody(item)


class QiNiuUploadData(BaseData):
    def __init__(self):
        self.files = []
        self.success = True
        self.err_code = 0
        super(QiNiuUploadData, self).__init__()

    def GetErrCode(self):
        return self.err_code

    def GetSuccess(self):
        return self.success

    def add_pair(self, src, tar, token):
        self.files.append({
            'from': src,
            'to': tar,
            'token': token
        })

    def reset(self):
        self.files = {}

    def SerializeBody(self):
        return self.files


class QiNiuDownloadData(BaseData):
    def __init__(self):
        self.files = []
        super(QiNiuDownloadData, self).__init__()

    def add_url(self, url):
        self.files.append(url)

    def SerializeBody(self):
        return {
            'urls': self.files
        }


class PayOrderData(BaseData):
    def __init__(self):
        self.order_no = None
        self.pay_str = None
        self.sign = None
        self.time = None
        super(PayOrderData, self).__init__()

    def SerializeBody(self):
        return {
            'order_no': self.order_no,
            'pay_str': self.pay_str,
            'sign': self.sign,
            'time': self.time
        }


class HistoryOrders(BaseData):
    def __init__(self):
        self.orders = []
        self.success = True
        self.errCode = 0
        super(HistoryOrders, self).__init__()

    def SerializeBody(self):
        return [
            {'T': order[0], 'P': order[1]} for order in self.orders
            ]

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.errCode
