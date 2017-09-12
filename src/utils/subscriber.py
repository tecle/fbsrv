# coding: utf-8

import json
import logging
import threading
import tornado.ioloop
from functools import wraps


def publish_receiver(routing_key):
    def outf(func):
        setattr(func, 'routing_key', routing_key)

        @wraps(func)
        def innerf(*args, **kwargs):
            return func(*args, **kwargs)

        return innerf

    return outf


class SubscriberThread(threading.Thread):
    '''处理需要动态修改的配置，配置从redis上监听'''

    def __init__(self, pubsub, channel_name, ioloop=None):
        self.pubsub = pubsub
        self.channel = channel_name
        self.stopped = True
        self.stdout = []
        self.handlers = {}
        self.ioloop = ioloop or tornado.ioloop.IOLoop.current()
        super(SubscriberThread, self).__init__()

    def run(self):
        self.pubsub.subscribe(self.channel)
        self.stopped = False
        for msg in self.pubsub.listen():
            # msg = {'pattern': None, 'type':'subscribe|message|unsubscribe', 'channel':'xxx', 'data':''}
            if msg['type'] == 'subscribe':
                continue
            elif msg['type'] == 'unsubscribe':
                break
            else:
                self.process_message(msg['data'])

    def process_message(self, content):
        try:
            obj = json.loads(content)
            routing_key = obj['key']
            for func in self.handlers.get(routing_key, tuple()):
                if func:
                    self.ioloop.add_callback(func, obj['data'])
        except:
            logging.exception('process message [{}] failed.'.format(content))

    def add_handler(self, routing_key, handler_func):
        self.handlers.setdefault(routing_key, []).append(handler_func)

    def ez_add_handler(self, func):
        self.handlers.setdefault(func.routing_key, []).append(func)

    def status(self):
        return self.pubsub.subscribed

    def join(self, timeout=None):
        self.stop()
        super(SubscriberThread, self).join(timeout)

    def stop(self):
        if not self.stopped:
            self.pubsub.unsubscribe(self.channel)
            self.stopped = True

    def __del__(self):
        self.stop()


def make_pub_message(routing_key, data):
    return {'key': routing_key, 'data': data}
