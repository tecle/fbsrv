# coding: utf-8
import logging

import model.messgemodel as MsgModel
import model.roommessage as MsgFormatter
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


class WatcherConns(object):
    '''
    host: 主播, tornado.websocket.WebSocketHandler
    watcher: 观众, tornado.websocket.WebSocketHandler
    '''

    def __init__(self, host_id):
        self.watchers = {}
        self.close_event_handlers = []
        self.host_id = host_id

    def add_close_handler(self, handler):
        self.close_event_handlers.append(handler)

    def new_watcher(self, watcher_id, watcher_conn):
        logging.debug('new watcher %s in.', watcher_id)
        old_conn = self.watchers.get(watcher_id, None)
        if old_conn:
            old_conn.close_silent()
        self.watchers[watcher_id] = watcher_conn
        watcher_conn.add_close_event(lambda user_id: self.watchers.pop(user_id, None))

    def clear(self):
        for conn in self.watchers.itervalues():
            try:
                conn.close_when_host_leave()
            except:
                logging.exception('conn %s has closed.', conn.current_user)
        self.watchers.clear()

    def broadcast(self, message):
        for conn in self.watchers.itervalues():
            try:
                conn.write_message(message)
            except:
                logging.exception('conn %s has closed.', conn.current_user)

    def notify(self, user_id, message):
        conn = self.watchers.get(user_id)
        if conn:
            conn.write_message(message)

    @property
    def conn_nums(self):
        return len(self.watchers)


class WatcherController(object):
    def __init__(self):
        # 主播
        self.watchers = {}

    def new_watcher(self, host_id, watcher_id, watcher_conn):
        item = self.watchers.get(host_id, None)
        if not item:
            item = WatcherConns(host_id)
            self.watchers[host_id] = item
        item.new_watcher(watcher_id, watcher_conn)

    def broadcast(self, host_id, msg):
        item = self.watchers.get(host_id)
        if item:
            item.broadcast(msg, True)

    @publish_receiver(MsgModel.ROOM_CLOSE_MSG_ROUTING_KEY)
    def on_room_closed(self, data):
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        item = self.watchers.get(host_id)
        if item:
            item.clear()

    @publish_receiver(MsgModel.GAME_NOTIFY_MSG_ROUTING_KEY)
    def on_game_notification(self, data):
        msg = data[MsgModel.MSG_ROOM_DATA_KEY]
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        item = self.watchers.get(host_id)
        if item:
            item.broadcast(msg)

    @publish_receiver(MsgModel.STOP_GAME_MSG_ROUTING_KEY)
    def on_game_closed(self, data):
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        item = self.watchers.get(host_id)
        if item:
            item.broadcast(MsgFormatter.make_message(MsgFormatter.msg_GameStop, None))

    @publish_receiver(MsgModel.START_GAME_MSG_ROUTING_KEY)
    def on_game_started(self, data):
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        game_type = data[MsgModel.MSG_ROOM_DATA_KEY]
        item = self.watchers.get(host_id)
        if item:
            item.broadcast(MsgFormatter.make_message(MsgFormatter.msg_GameStop, game_type))

    @publish_receiver(MsgModel.START_LIVE_MSG_ROUTING_KEY)
    def on_start_live(self, data):
        host_id = data[MsgModel.MSG_ROOM_ID_KEY]
        item = self.watchers.get(host_id)
        if item:
            item.broadcast(MsgFormatter.make_message(MsgFormatter.msg_LiveStart, None))
