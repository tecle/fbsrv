# coding: utf-8

import json
import logging
import time
from functools import partial

import tornado.gen
import tornado.ioloop
import tornado.websocket

import model.roommessage as MsgFormater
import model.messgemodel as MsgMode
from games.gamemodule import GameManager
from model.cache.live_cache import LiveCache
from utils.common_define import ErrorCode
from utils.rpcfrmwrk import ERR_WHEN_RPC_CALL

hb_interval = 200


class ConnHandlerBase(tornado.websocket.WebSocketHandler):
    def initialize(self):
        logging.debug('init conn handler')
        self.close_event_handlers = []
        self.host_id = None

    def add_close_event(self, event_handler):
        self.close_event_handlers.append(event_handler)

    def on_message(self, message):
        # process client message
        # in this version it is not necessary
        try:
            obj = json.loads(message)
            if obj['t'] == MsgMode.REQ_FOR_BET:
                self.do_bet(obj['n'], obj['bet'])
            elif obj['t'] == MsgMode.REQ_FOR_SEND_GIFT:
                self.do_send_gift(obj['n'], obj['gift'])
            else:
                self.process_message(obj)
        except:
            logging.exception('user %s process message [%s] failed', self.current_user, message)

    def process_message(self, obj):
        raise NotImplementedError('process_message not implement.')

    def do_bet(self, sequence, bet_detail):
        self.application.rpc.remote_call(
            GameManager.rpc_add_bet, partial(self.on_bet, sequence),
            self.host_id, self.current_user, bet_detail['S'], bet_detail['N'])

    def do_send_gift(self, sequence, gift_inf):
        gift_id, gift_num = gift_inf['G'], gift_inf['N']
        err_code, remain, charm = self.application.live_biz.handle_send_gift_event(
            self.current_user, self.host_id, gift_id, gift_num)
        self.write_message(
            MsgFormater.make_message(
                MsgFormater.msg_SendGiftResponse,
                {
                    'n': sequence,
                    'left': remain
                }, err_code))

    def process_room_snapshot(self):
        game_type, on_live = self.application.get_cache(LiveCache.cache_name).room_status(self.host_id)
        if game_type:
            self.application.rpc.remote_call(
                GameManager.rpc_get_game_snapshot, partial(
                    self.on_snapshot, game_type, on_live), self.host_id, self.host_id)
        else:
            self.on_snapshot(game_type, on_live, (0, None))

    def on_bet(self, bet_id, err_code):
        if err_code == ERR_WHEN_RPC_CALL:
            err_code = ErrorCode.RPCError
        self.write_message(MsgFormater.make_message(MsgFormater.msg_BetResponse, {'n': bet_id}, err_code))

    def on_snapshot(self, game_type, on_live, data):
        err_code, snapshot = (ErrorCode.RPCError, None) if data == ERR_WHEN_RPC_CALL else data
        self.write_message(MsgFormater.make_message(MsgFormater.msg_GameSnapshot, {
            'OL': on_live,
            'GT': game_type,
            'GS': snapshot
        }, err_code))
        if err_code:
            self.close()

    def check_origin(self, origin):
        return True

    def get_room_snapshot(self):
        '''获取房间状态: 当前开启的道具，以及开启游戏时的快照信息'''
        pass


class HostHandler(ConnHandlerBase):
    def initialize(self):
        super(HostHandler, self).initialize()
        self.last_ping = 0
        self.ioloop = tornado.ioloop.IOLoop.current()

    def open(self):
        self.set_nodelay(True)
        self.current_user = int(self.get_argument('uid'))
        self.host_id = self.current_user
        self.do_ping(self.last_ping)
        already_exist = self.application.host_ctrl.new_host(self)
        if already_exist:
            self.process_room_snapshot()

    def process_message(self, obj):
        cache = self.application.get_cache(LiveCache.cache_name)
        op_type = obj['t']
        if op_type == 3:
            # 关闭直播
            cache.stop_live(self.host_id)
        elif op_type == 4:
            # 开启直播
            cache.start_live(self.host_id)
            cache.publish_start_live(self.host_id)
        elif op_type == 5:
            # 关闭游戏
            cache.clear_game_type(self.host_id)
        elif op_type == 6:
            # 开启游戏
            game_type = obj['gt']
            self.application.rpc.remote_call(
                GameManager.rpc_start_game, self.on_start_game, self.current_user, game_type)
            cache.publish_game_started(self.host_id, game_type)
        self.write_message(MsgFormater.make_message(MsgFormater.msg_SimpleResponse, None, 0))

    def on_start_game(self, data):
        err_code, snapshot = (ErrorCode.RPCError, None) if data == ERR_WHEN_RPC_CALL else data
        self.write_message(MsgFormater.make_message(MsgFormater.msg_SimpleResponse, None, err_code))
        if err_code:
            self.close()

    def do_ping(self, ping_expect):
        if self.ws_connection is None:
            return
        if self.last_ping == ping_expect:
            ping_expect += 1
            self.ping(str(ping_expect))
            self.ioloop.add_timeout(time.time() + hb_interval, self.do_ping, ping_expect)
        else:
            logging.warning('no ping data.')
            self.close()

    def on_pong(self, data):
        self.last_ping = int(data)

    def on_close(self):
        logging.debug('Live closed')
        for handler in self.close_event_handlers:
            handler()


class WatcherHandler(ConnHandlerBase):
    def open(self):
        self.set_nodelay(True)
        self.current_user = int(self.get_argument('uid'))
        self.host_id = int(self.get_argument('lid'))
        self.application.watcher_ctrl.new_watcher(self.host_id, self.current_user, self)
        self.application.num_watcher_conns += 1
        self.process_room_snapshot()

    def on_close(self):
        for handler in self.close_event_handlers:
            handler(self.current_user)

    def close_silent(self):
        '''安静关闭，清空关闭回调'''
        self.close_event_handlers = []
        self.close()

    def close_when_host_leave(self):
        self.write_message(MsgFormater.make_message(MsgFormater.msg_HostEndLiving, None))
        self.close()
