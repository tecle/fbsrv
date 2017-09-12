# coding: utf-8

from __future__ import absolute_import, unicode_literals
import logging
import requests


class DingTalkRobot(object):
    def __init__(self, api_url, access_token):
        self.url = '%s?access_token=%s' % (api_url, access_token)

    def send_text_msg(self, content, at_all=False):
        msg = {
            'msgtype': 'text',
            'text': {
                'content': content
            },
            'at': {
                'atMobiles': [],
                'isAtAll': at_all
            }
        }
        r = requests.post(self.url, json=msg, headers={'Content-Type': 'application/json'})
        if r.status_code != 200:
            logging.warning('send message(%s) to robot(%s) failed, reason:%s'.format(msg, self.url, r.content))


if __name__ == '__main__':
    DingTalkRobot(
        'https://oapi.dingtalk.com/robot/send',
        'access_token=2cf60c33e6366015226539c6a510696825ef79f65ddac60b9563cb6861ac2588').send_text_msg(
        '测试消息', False)
