# coding: utf-8

import unittest
from functools import wraps


def fake_async(func):
    @wraps(func)
    def f(*args, **kwargs):
        func(*args, **kwargs)
    return f


class A(object):
    def __init__(self):
        self.params = {}
        self.headers = {}
        self.body = None


class FakeHandler(object):
    def __init__(self):
        self.request = A()
        self.settings = {}
        self.result = None
        self.done = False
        self.status_info = None
        self.param = {}

    def post(self):
        pass

    def get(self):
        pass

    def set_request_body(self, body):
        self.request.body = body

    def set_request_params(self, params):
        self.request.params = params

    def add_param_to_request(self, key, val):
        self.param[key] = val

    def add_attr_to_request(self, name, val):
        setattr(self.request, name, val)

    def get_argument(self, name, default=None):
        if name not in self.request.params:
            if default is not None:
                return default
            raise Exception('%s not exist.' % name)
        return self.request.params[name]

    def write(self, info):
        self.result = info

    def finish(self):
        self.done = True

    def set_status(self, code, reason):
        self.status_info = (code, reason)


import base64


class HandlerTestBase(unittest.TestCase):
    def create_handler(self, cls, params={}, body=None, db=None, redis=None, **kwargs):
        handler = cls()
        handler.set_request_body(body)
        if params:
            handler.set_request_params(params)
        handler.settings['db'] = db
        handler.settings['redis_inst'] = redis
        for k, v in kwargs.items():
            handler.settings[k] = v
        return handler

    def encode_pb_body(self, body, encode_type=16):
        if encode_type == 64:
            return base64.b64encode(body)
        elif encode_type == 16:
            return body.encode('hex')
        return None


def patch_tornado():
    import tornado.web
    tornado.web.asynchronous = fake_async
    tornado.web.RequestHandler = FakeHandler

