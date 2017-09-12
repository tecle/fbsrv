# coding: utf-8

import os
import sys
import time

import tornado.ioloop
import tornado.web

from utils.rpcfrmwrk import RpcClient, RpcHandler

CUR_PATH = os.getcwd()
ROOT_PATH = CUR_PATH
sys.path.append(os.path.join(ROOT_PATH, 'src'))
sys.path.append(os.path.join(ROOT_PATH, 'libs'))

MAX_REQUEST_COUNT = 100

processed = 0


@RpcHandler.rpc
def process_bet(index, *args, **kwargs):
    global processed
    processed += 1
    if processed >= MAX_REQUEST_COUNT:
        tornado.ioloop.IOLoop.current().add_timeout(time.time() + 1, tornado.ioloop.IOLoop.current().stop)
    return index


class RpcFuncInCls(object):
    def __init__(self):
        self.counter = 0

    def process_bet(self, index, *args, **kwargs):
        self.counter += 1
        print 'counter:', self.counter
        if self.counter >= MAX_REQUEST_COUNT:
            print 'sys prepare to exit.'
            tornado.ioloop.IOLoop.current().add_timeout(time.time() + 1, tornado.ioloop.IOLoop.current().stop)
        return index


def printf(data):
    global processed
    processed += 1
    if processed >= MAX_REQUEST_COUNT:
        print 'over      :', time.time()
        tornado.ioloop.IOLoop.current().stop()


def start_srv():
    app = tornado.web.Application(
        handlers=[(r'/rpc', RpcHandler)]
    )
    app.listen(9999)
    rfic = RpcFuncInCls()
    RpcHandler.inject_rpc(rfic.process_bet)
    tornado.ioloop.IOLoop.current().start()


def start_cli():
    cli = RpcClient('http://localhost:9999/rpc')
    rfic = RpcFuncInCls()

    def sync_code():
        for i in range(MAX_REQUEST_COUNT):
            cli.remote_call(rfic.process_bet, printf, i, 2, 3, a='z')

    print 'add   task:', time.time()
    sync_code()
    print 'start loop:', time.time()
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    if sys.argv[1] == 'srv':
        # profile.run('start_srv()')
        start_srv()
    else:
        start_cli()
