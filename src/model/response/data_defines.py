# coding:utf-8
import json


class BaseData(object):
    def __init__(self):
        self.reqId = '0'

    def SerializeToString(self):
        return json.dumps({
            'status': 'OK' if self.GetSuccess() else 'FAIL',
            'reqId': self.GetReqId(),
            'code': self.GetErrCode() or 0,
            'body': self.SerializeBody() or {}
        }, ensure_ascii=False, indent=2).encode('utf-8')

    def GetReqId(self):
        return self.reqId

    def GetSuccess(self):
        return True

    def GetErrCode(self):
        return 0

    def SetSuccess(self, success):
        pass

    def SetErrCode(self, err_code):
        pass

    def ParseFromString(self, s):
        obj = json.loads(s)
        self.SetSuccess(obj['status'] == 'OK')
        self.SetErrCode(obj['code'])
        self.InitByJsonBody(obj['body'])

    def SerializeBody(self):
        raise NotImplementedError()

    def CopyFrom(self, src):
        for attr_name, attr_val in src.__dict__.items():
            setattr(self, attr_name, attr_val)

    def InitByJsonBody(self, json_obj):
        raise NotImplementedError()


class ListWrapper(list):
    def __init__(self, cls, seq=()):
        self.item_cls = cls
        super(ListWrapper, self).__init__(seq)

    def add(self):
        n = self.item_cls()
        self.append(n)
        return n
