# coding: utf-8
import json

from data_defines import BaseData, ListWrapper


class Topic(BaseData):
    def __init__(self):
        self.topicId = None
        self.title = None
        self.detail = None
        self.visible = None
        self.views = None  # 当前参与人数
        self.activeNum = None
        self.weight = None
        self.pics = None
        self.participants = None
        super(Topic, self).__init__()

    def SerializeBody(self):
        return {
            "tid": self.topicId,
            "title": self.title,
            "info": self.detail,
            "views": self.views,
            "aNum": self.activeNum,
            "pic": self.pics,
            "uIn": self.participants
        }


class Topics(BaseData):
    def __init__(self):
        self.topics = ListWrapper(Topic)
        super(Topics, self).__init__()

    def SerializeBody(self):
        return [item.SerializeBody() for item in self.topics]

    def clear(self):
        self.topics = ListWrapper(Topic)


class NewActiveInfo(object):
    def __init__(self):
        self.activeId = None
        self.ownerId = None
        self.topicId = None
        self.content = None
        self.pictures = None
        self.location = None
        self.longitude = None
        self.latitude = None
        super(NewActiveInfo, self).__init__()

    def parseFromString(self, s):
        obj = json.loads(s)
        self.ownerId = obj['ownerId']
        self.topicId = obj['topicId']
        self.content = obj['content']
        self.pictures = obj['pictures']
        self.location = obj['location']
        self.longitude = obj['longitude']
        self.latitude = obj['latitude']


class Active(BaseData):
    def __init__(self):
        self.viewNum = None
        self.commentNum = None
        self.likeNum = None
        self.activeId = None
        self.ownerId = None
        self.topicId = None
        self.content = None
        self.pictures = None
        self.location = None
        self.publishTime = None
        super(Active, self).__init__()

    def SerializeBody(self):
        return {
            "vNum": self.viewNum,
            "cNum": self.commentNum,
            "lNum": self.likeNum,
            "aid": self.activeId,
            "oid": self.ownerId,
            "tid": self.topicId,
            "text": self.content,
            "pics": self.pictures,
            "site": self.location,
            "time": self.publishTime,
        }

    def InitByJsonBody(self, obj):
        self.viewNum = obj["vNum"]
        self.commentNum = obj["cNum"]
        self.likeNum = obj["lNum"]
        self.activeId = obj["aid"]
        self.ownerId = obj["oid"]
        self.topicId = obj["tid"]
        self.content = obj["text"]
        self.pictures = obj["pics"]
        self.location = obj["site"]
        self.publishTime = obj["time"]


class Actives(BaseData):
    class ActiveItem(object):
        # __slots__ = ['active', 'isLiked', 'distanceToUser']

        def __init__(self):
            self.viewNum = None
            self.commentNum = None
            self.likeNum = None
            self.activeId = None
            self.ownerId = None
            self.topicId = None
            self.content = None
            self.pictures = None
            self.location = None
            self.publishTime = None

            self.nickName = None
            self.avatar = None

            self.isLiked = None

        def SerializeBody(self):
            return {
                "vNum": self.viewNum,
                "cNum": self.commentNum,
                "lNum": self.likeNum,
                "aid": self.activeId,
                "oid": self.ownerId,
                "tid": self.topicId,
                "text": self.content,
                "pics": self.pictures,
                "site": self.location,
                "time": self.publishTime,
                "liked": self.isLiked,
                "nick": self.nickName,
                "at": self.avatar
            }

    def __init__(self):
        self.actives = ListWrapper(self.ActiveItem)
        super(Actives, self).__init__()

    def SerializeBody(self):
        return [item.SerializeBody() for item in self.actives]


class ActiveItem(BaseData):
    def __init__(self):
        self.detail = Active()
        self.isLiked = False
        self.success = True
        self.errCode = 0
        super(ActiveItem, self).__init__()

    def SerializeBody(self):
        return {
            "info": self.detail.SerializeBody(),
            "liked": self.isLiked,
        }

    def InitByJsonBody(self, obj):
        self.detail.InitByJsonBody(obj["info"])
        self.isLiked = obj["liked"]

    def GetSuccess(self):
        return self.success

    def GetErrCode(self):
        return self.errCode


class ActivesStatistics(BaseData):
    class STtem(object):
        __slots__ = ['viewNum', 'commentNum', 'likeNum', 'id']

        def __init__(self):
            self.id = None
            self.viewNum = 0
            self.commentNum = 0
            self.likeNum = 0

        def SerializeBody(self):
            return {'vNum': self.viewNum, 'cNum': self.commentNum, 'lNum': self.likeNum, 'aid': self.id}

        def InitByJsonBody(self, obj):
            self.viewNum = obj['vNum']
            self.commentNum = obj['cNum']
            self.likeNum = obj['lNum']
            self.id = obj['aid']

    def __init__(self):
        self.data = ListWrapper(self.STtem)
        super(ActivesStatistics, self).__init__()

    def InitByJsonBody(self, json_obj):
        for item in json_obj['acts']:
            n = self.data.add()
            n.InitByJsonBody(item)

    def SerializeBody(self):
        return {
            'acts': [item.SerializeBody() for item in self.data]
        }


class Comment(BaseData):
    def __init__(self):
        self.commentId = None
        self.ownerId = None
        self.ownerAvatar = None
        self.ownerNickname = None
        self.activeId = None
        self.targetId = None
        self.targetUserId = None
        self.targetNickname = None
        self.targetContent = None
        self.content = None
        self.publishTime = None
        super(Comment, self).__init__()

    def SerializeBody(self):
        return {
            "cid": self.commentId,
            "oid": self.ownerId,
            "oat": self.ownerAvatar,
            "onick": self.ownerNickname,
            "aid": self.activeId,
            "tid": self.targetId,
            "tnick": self.targetNickname,
            "tuid": self.targetUserId,
            "tc": self.targetContent,
            "text": self.content,
            "time": self.publishTime,
        }


class Comments(BaseData):
    def __init__(self):
        self.comments = ListWrapper(Comment)
        super(Comments, self).__init__()

    def InitByJsonBody(self, json_obj):
        for item in json_obj['cms']:
            self.comments.add().InitByJsonBody(item)

    def SerializeBody(self):
        return [item.SerializeBody() for item in self.comments]


class ActivesMeta(BaseData):
    def __init__(self):
        self.acts = {}
        super(ActivesMeta, self).__init__()

    def add_active(self, aid, txt, pics):
        self.acts[aid] = {
            'txt': txt,
            'pics': pics
        }

    def InitByJsonBody(self, json_obj):
        self.acts = json_obj

    def SerializeBody(self):
        return self.acts

    def Extend(self, other):
        self.acts.update(other.acts)
