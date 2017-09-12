# coding: utf-8

import time
import json
import logging
import hashlib
import requests
from threading import Lock

TOKEN_AFFECTIVE_TIME = 23 * 3600


class GeTuiAPI(object):
    def __init__(self, host, app_id, app_key, app_secret, master_secret):
        self.app_id = app_id
        self.app_key = app_key
        self.app_secret = app_secret
        self.master_secret = master_secret
        self.host = host
        self._push_single_url = '{}/v1/{}/push_single'.format(self.host, self.app_id)
        self._auth_token = None
        self._token_expire_time = None
        self._token_lock = Lock()

    @property
    def token(self):
        with self._token_lock:
            if time.time() < self._token_expire_time:
                return self._auth_token
            logging.info('auth token expire.')
            token = self._get_auth_token()
            if token:
                self._auth_token = token
                self._token_expire_time = time.time() + TOKEN_AFFECTIVE_TIME
                return self._auth_token
        return None

    def _get_auth_token(self):
        headers = {
            'Content-Type': 'application/json'
        }
        url = '{}/v1/{}/auth_sign'.format(self.host, self.app_id)
        timestamp = int(time.time() * 1000)
        sign = hashlib.sha256('{}{}{}'.format(self.app_key, timestamp, self.master_secret)).hexdigest()
        body = json.dumps({
            'sign': sign,
            'timestamp': timestamp,
            'appkey': self.app_key
        })
        r = None
        try:
            r = requests.post(url, data=body, headers=headers)
            obj = json.loads(r.content)
            if obj['result'] != 'ok':
                return None
            return obj['auth_token']
        except Exception:
            if r:
                logging.exception('code:%s, reason:%s, body:%s', r.status_code, r.reason, r.content)
            else:
                logging.exception('unknown error.')
        return None

    def push_to_one(self, client_id, app_msg):
        token = self.token
        if not token:
            logging.warning('push msg to [%s] with content [%s] failed.', client_id, app_msg)
            return False
        headers = {
            'Content-Type': 'application/json',
            'authtoken': self.token
        }
        body = json.dumps({
            "message": {
                "appkey": self.app_key,
                "is_offline": True,
                "offline_expire_time": 10000000,
                "msgtype": "transmission"  # "transmission"  #
            },
            "transmission": {
                "transmission_type": True,
                "transmission_content": app_msg,
                "duration_end": "2099-12-31 23:59:59"
            },
            "alias": client_id,  # 使用别名的方式定位用户
            "requestid": str(int(time.time() * 1000))
        })
        try:
            r = requests.post(self._push_single_url, data=body, headers=headers)
            obj = json.loads(r.content)
            if obj['result'] != 'ok':
                logging.warning('push msg to [%s] with content [%s] failed. Reason:[%s]', client_id, app_msg, r.content)
                return False
            return True
        except Exception:
            logging.exception('net error.')
        return False
