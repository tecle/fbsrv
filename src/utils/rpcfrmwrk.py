# coding: utf-8

import json
import logging
from functools import wraps, partial
from tornado.httpclient import HTTPRequest
from tornado.web import RequestHandler
import tornado.gen
import tornado.curl_httpclient

ERR_WHEN_RPC_CALL = object()


class RpcHandler(RequestHandler):
    _methods = {}

    def _parse_request(self):
        obj = json.loads(self.request.body)
        func_name = obj['fun']
        args = obj['args']
        kwargs = obj['kwargs']
        logging.debug('RPC: %s(%s, %s)', func_name, args, kwargs)
        return partial(self._methods.get(func_name, None), *args, **kwargs)

    def post(self):
        f = self._parse_request()
        if not f:
            self.set_status(502, 'no func found err')
            return
        result = f()
        self.write(json.dumps({'ret': result}))

    @classmethod
    def inject_rpc(cls, func):
        '''used for inject a function in class to rpc framework.'''
        cls._methods[func.__name__] = partial(func)

    @classmethod
    def rpc(cls, func):
        cls._methods[func.__name__] = func

        @wraps(func)
        def y(*args, **kwargs):
            print args, kwargs
            return func(*args, **kwargs)

        return y


class CoroutineRpcHandler(RpcHandler):
    @tornado.gen.coroutine
    def post(self):
        f = self._parse_request()
        if not f:
            self.set_status(502, 'no func found err')
            return
        result = yield f()
        self.write(json.dumps({'ret': result}))


class RpcClient(object):
    def __init__(self, host):
        self.host = host
        self.max_clients = 32
        self.cli = tornado.curl_httpclient.CurlAsyncHTTPClient(max_clients=self.max_clients)

    def remote_call(self, func, callback, *args, **kwargs):
        req = HTTPRequest(url=self.host, method='POST', body=json.dumps({
            'fun': func.__name__,
            'args': args,
            'kwargs': kwargs
        }))
        self.cli.fetch(req, callback=partial(self.process_rpc_ret, callback))

    def process_rpc_ret(self, cb, response):
        if not response.error:
            obj = json.loads(response.body)
            cb(obj['ret'])
        else:
            logging.warning("receive bad response from remote. code: %s, reason: %s", response.code, response.reason)
            cb(ERR_WHEN_RPC_CALL)
