# coding: utf-8


import logging
import time
import tornado.ioloop
import model.messgemodel as MsgModel

from functools import partial
from utils.subscriber import publish_receiver

st_Normal = 0
st_WaitReconnect = 1
st_ReadyToClose = 2
st_WaitGameOver = 3
st_Closed = 4

debug_mapping = [
    'Normal',
    'WaitReconnect',
    'ReadyToClose',
    'WaitGameOver',
    'Closed'
]


class HostConn(object):
    def __init__(self, host_conn):
        self.status = st_Normal
        self.timer = None
        self.max_timeout = 30
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.conn = host_conn
        self.host_id = host_conn.current_user
        self.close_event_handlers = []

    def _reset_timer(self):
        logging.debug('%s>> reset timer', self.host_id)
        if self.timer:
            self.ioloop.remove_timeout(self.timer)
        self.timer = self.ioloop.add_timeout(time.time() + self.max_timeout, self._connect_timeout)

    def _connect_timeout(self):
        logging.debug('%s>> current status:%s', self.host_id, debug_mapping[self.status])
        if self.status == st_WaitReconnect:
            logging.debug('%s>> WaitReconnect -> WaitGameOver', self.host_id)
            self.status = st_Closed
            self._shutdown()

    def _shutdown(self):
        logging.debug('%s>> clear watchers.', self.host_id)
        for handler in self.close_event_handlers:
            logging.debug('%s>> run close handler:%s', self.host_id, handler.__name__)
            handler()

    def add_close_handler(self, handler):
        self.close_event_handlers.append(handler)

    def disconnect(self):
        self.status = st_WaitReconnect
        logging.debug('%s>> host disconnect, status to:%s', self.host_id, debug_mapping[self.status])
        self._reset_timer()

    def reconnect(self, host_conn):
        self.conn = host_conn
        self.host_id = host_conn.current_user
        logging.debug('%s>> host reconnected', self.host_id)
        if self.status != st_Closed:
            self.status = st_Normal
            logging.debug('%s>> current status:%s', self.host_id, debug_mapping[self.status])
            if self.timer:
                self.ioloop.remove_timeout(self.timer)
                self.timer = None

    def broadcast(self, message):
        if self.conn.ws_connection:
            self.conn.write_message(message)

    @property
    def closed(self):
        return self.status == st_Closed


class HostController(object):
    def __init__(self, live_cache, ioloop=None):
        self.hosts = {}
        self.ioloop = ioloop or tornado.ioloop.IOLoop.instance()
        self.live_cache = live_cache
        self.wait_game_over_set = set()

    def new_host(self, host_conn):
        host_id = host_conn.current_user
        exist_item = self.hosts.get(host_id, None)
        exist = exist_item and not exist_item.closed
        if exist:
            exist_item.reconnect(host_conn)
        else:
            self.process_start_room(host_id, host_conn)
        host_conn.add_close_event(exist_item.disconnect)
        return exist

    def process_start_room(self, host_id, host_conn):
        exist_item = HostConn(host_conn)
        exist_item.add_close_handler(partial(self.on_room_closed, host_id))
        self.hosts[host_id] = exist_item
        self.live_cache.add_room_biz(host_id)

    def on_room_closed(self, host_id):
        '''
        1. 房间已经开启游戏:
        房间关闭时，游戏进行到下一局，不广播房间关闭通知, 直到收到游戏结束通知
        2. 房间并没有开启游戏:
        直接广播房间关闭
        '''
        on_game, on_live = self.live_cache.stop_room_biz(host_id)
        if on_game:
            self.wait_game_over_set.add(host_id)
        else:
            self.live_cache.publish_room_closed(host_id)

    @publish_receiver(MsgModel.GAME_OVER_MSG_ROUTING_KEY)
    def on_game_over(self, data):
        '''
        游戏结束:
        1. 广播房间关闭
        2. 广播游戏关闭
        '''
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        if host_id in self.wait_game_over_set:
            self.live_cache.publish_room_closed(host_id)
            self.wait_game_over_set.remove(host_id)
        else:
            self.live_cache.publish_game_closed(host_id)

    @publish_receiver(MsgModel.GAME_NOTIFY_MSG_ROUTING_KEY)
    def on_game_notification(self, data):
        msg = data[MsgModel.MSG_ROOM_DATA_KEY]
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        item = self.hosts.get(host_id)
        if item:
            item.broadcast(msg)
