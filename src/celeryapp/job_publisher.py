# encoding: utf-8

from __future__ import absolute_import, unicode_literals, print_function
from .funboxapp import app, init_celery_app
from .tasks import send_gift
import time
# import tcelery

# tcelery.setup_nonblocking_producer(celery_app=app)


def run():
    init_celery_app('redis://:Xdi@so(32_4848@120.26.223.159:6489/15')
    for i in range(100):
        send_gift.delay('1', i, '2', i * 100, 1)
        time.sleep(0.01)

if __name__ == '__main__':
    run()
