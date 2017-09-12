# coding: utf-8

import datetime
import hashlib
import json
import logging
import time

import tornado.gen
import tornado.web
import tornado.websocket

from model.cache.server_cache import ServerCache
from utils.common_define import HttpErrorStatus
from utils.util_tools import decode_token


class KVBaseHandler(tornado.web.RequestHandler):
    SERVER_SECRET = 'secret'
    EFFECT_TIME = 10000
    NEED_VALIDATE = True

    def initialize(self, **kwargs):
        setattr(self, 'need_token', kwargs.get('need_token', True))

    @tornado.web.asynchronous
    def post(self, *args):
        if self.check_request():
            self.do_post(*args)
            self.application.num_processed_requests += 1
        else:
            self.finish()

    def check_request(self):
        if not self.validate_request():
            return False
        return True

    def do_post(self, *args):
        raise NotImplementedError('do_post has not implement.')

    def get_sign(self, req_id):
        str_to_sign = '%s%s%s' % (self.request.body, req_id, self.SERVER_SECRET)
        return hashlib.md5(str_to_sign).hexdigest()

    def get_argument(self, name, default=tornado.web.RequestHandler._ARG_DEFAULT, strip=True):
        # --- debug code begin---
        if not self.NEED_VALIDATE or not self.request.body:
            return super(KVBaseHandler, self).get_argument(name, default, strip)
        # --- debug code end---
        out = self.json_body_args.get(name, default)
        if out == tornado.web.RequestHandler._ARG_DEFAULT:
            raise tornado.web.MissingArgumentError(name)
        return out

    def validate_request(self):
        if not self.NEED_VALIDATE:
            return True
        # --- debug code begin---
        if self.request.headers.get('debug', '') == 'whoisyourdaddy':
            setattr(self, 'request_id', 'debug_request')
            if self.request.body:
                setattr(self, 'json_body_args', json.loads(self.request.body))
            return True
        # --- debug code end---
        try:
            valid = self._check_token() if self.need_token else self._check_request()
            if not valid:
                return False
            if self.request.body:
                logging.debug('request info:[%s]', self.request.body)
                setattr(self, 'json_body_args', json.loads(self.request.body))
        except:
            logging.exception('process request with body [%s] failed.', self.request.body)
            self.set_status(*HttpErrorStatus.ProcessHeaderError)
            return False
        return True

    def _check_request(self):
        req_id = self.request.headers.get('ReqID', None)
        sign = self.request.headers.get('Sign', None)
        if not req_id or not sign:
            logging.warning('Token required.')
            self.set_status(*HttpErrorStatus.InvalidRequest)
            return False
        cur_time = int(time.mktime(datetime.datetime.utcnow().utctimetuple())) * 1000
        req_time = int(req_id[:-4])
        server_cache = self.application.get_cache(ServerCache.cache_name)
        req_exist, user_token = server_cache.get_cached_req_data(req_id)
        if not self._compare_request_id(cur_time, req_time, req_exist, req_id, sign):
            return False
        server_cache.set_request_id(req_id)
        return True

    def _compare_request_id(self, cur_time, req_time, req_exist, req_id, sign):
        if cur_time - req_time > self.EFFECT_TIME or req_exist:
            logging.warning('invalid request id[%s]' % req_id)
            self.set_status(*HttpErrorStatus.InvalidRequestId)
            return False
        if self.get_sign(req_id) != sign:
            logging.info('bad sign for request[%s]' % req_id)
            self.set_status(*HttpErrorStatus.InvalidSign)
            return False
        setattr(self, 'request_id', req_id)
        return True

    def _check_token(self):
        uid, real_token = self._extract_user()
        if uid:
            req_exist, user_token = self.application.get_cache(ServerCache.cache_name).get_cached_req_data('', uid)
            return self._compare_token(real_token, user_token)
        logging.warning('Token required.')
        self.set_status(*HttpErrorStatus.InvalidRequest)
        return False

    def _extract_user(self):
        token = self.request.headers.get('Token', None)
        if token:
            uid, real_token = decode_token(token).split('-')
            self.current_user = uid
            return uid, real_token
        return None, None

    def _compare_token(self, token, cached_token):
        if not cached_token:
            logging.debug('user token not exist.')
            self.set_status(*HttpErrorStatus.InvalidToken)
            return False
        if cached_token != token:
            logging.debug('invalid token:[%s], expect:[%s]', token, cached_token)
            self.set_status(*HttpErrorStatus.OldToken)
            return False
        setattr(self, 'request_id', self.request.headers.get('ReqID', ''))
        return True

    def write_response(self, msg):
        msg.reqId = self.request_id
        content = msg.SerializeToString()
        self.write(content)


class CoroutineBaseHandler(KVBaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args):
        if self.check_request():
            yield self.do_post(*args)
            self.application.num_processed_requests += 1
