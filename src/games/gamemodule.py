# coding: utf-8

import datetime
import logging
import math
import time
import tornado.ioloop
import celeryapp.tasks as CeleryTasks
import model.roommessage as MsgFormater
import model.messgemodel as MsgMode

from model.cache import LiveCache
from model.cache import UserResCache
from utils.common_define import ErrorCode
from utils.util_tools import profile_func

AdapterStarted = 1
AdapterStopping = 2
AdapterStopped = 3
AdapterFreezing = 4
AdapterFrozen = 5


class GameStatusCode(object):
    ST_Waiting = 1  # 空闲时间
    ST_Betting = 2  # 押注时间
    ST_Freezing = 3  # 停止下注
    ST_ShowResult = 4  # 结果揭晓并结算


FrozenStatusTag = -1


class GameAdapter(object):
    def __init__(self, io_loop, owner_id, room_id, game_config, game_type, game_inst, redis_wrapper, robot=None):
        self.game_id = '%s-%s' % (owner_id, int(time.time()))
        self.game_impl = game_inst
        self.game_config = game_config
        self.game_type = game_type
        # get_game_am 返回: [start_game_status, ..., end_game_status]
        self.game_status_list = self.game_config.game_status(self.game_type)
        self.game_status_index = 0
        self.game_result = None
        self.slot_count = game_inst.get_slot_count()
        self.robot = robot

        self.owner_id = owner_id
        self.room_id = room_id

        self.io_loop = io_loop
        self.live_cache = redis_wrapper.get_cache(LiveCache.cache_name)
        self.user_res_cache = redis_wrapper.get_cache(UserResCache.cache_name)
        self.progress = 0
        self.frozen_time = 0

        self.bet_detail = [{} for _ in range(self.slot_count)]
        # 虚拟下注情况为显示给用户的下注情况, 实际下注情况为bet_sum
        self.bet_sum = [0] * self.slot_count
        self.virtual_bet_sum = [0] * self.slot_count
        # 消息队列保存需要广播给客户端的消息, 外面会来取
        self.msg_queue = []
        # 适配器状态和游戏状态
        self.adapter_status = AdapterStarted
        self.has_bet = False

        self.round_start_time = datetime.datetime.utcnow()
        self.round_over_handler = []

    @property
    def current_game_status(self):
        return self.game_status_list[self.game_status_index]

    @property
    def on_betting(self):
        return self.current_game_status.tag == GameStatusCode.ST_Betting

    @property
    def stopped(self):
        return self.adapter_status == AdapterStopped

    @property
    def running(self):
        return self.adapter_status in (AdapterStarted, AdapterFreezing)

    def add_round_over_handler(self, handler):
        self.round_over_handler.append(handler)

    def start(self):
        # if game frozen, we should
        self._reset_game_data()
        self.adapter_status = AdapterStarted
        self.progress = -1

    def stop(self):
        '''
        if current status is started, then set current status to stopping. other wise, do nothing.
        status: started -> stopping -> stopped
        '''
        logging.debug('stop game:%s', self.game_id)
        if not self.ready_to_close():
            self.adapter_status = AdapterStopping

    def freeze(self):
        '''freeze game, and one day you can wake it up again.'''
        if self.adapter_status == AdapterStarted:
            self.adapter_status = AdapterFreezing

    def unfreeze(self):
        if self.adapter_status == AdapterFrozen or self.adapter_status == AdapterFreezing:
            self.adapter_status = AdapterStarted
            to_ = self.game_status_list[self.game_status_index]
            self.progress = -1
            self.msg_queue.append(
                MsgFormater.format_game_status_trans(FrozenStatusTag, to_.tag, to_.duration))

    def tick(self):
        if self.adapter_status == AdapterFrozen:
            return self._do_frozen()
        if self.adapter_status == AdapterStopped:
            return False
        return self._do_tick()

    def need_broadcast(self):
        if not self.progress:
            return True
        if not self.on_betting:
            return False
        if self.has_bet or not self.progress % 3:
            self.has_bet = False
            self.msg_queue.append(MsgFormater.format_game_bet_info(self.virtual_bet_sum))
            return True
        return False

    def _do_tick(self):
        self.progress += 1
        cur_status = self.game_status_list[self.game_status_index]
        if self.progress >= cur_status.duration:
            self.game_status_index += 1
            self.has_bet = False
            if self.game_status_index == len(self.game_status_list):
                if not self._has_next_round():
                    return False
                if self._do_freeze(cur_status):
                    return True
            self._do_status_trans(cur_status)
        elif self.on_betting:
            # 直接广播消息
            if self.robot:
                slot_id, bet_num = self.robot.bet()
                if bet_num:
                    self.virtual_bet_sum[slot_id] += bet_num
            self.msg_queue.append(MsgFormater.format_game_bet_info(
                cur_status.tag, cur_status.duration, self.progress, self.virtual_bet_sum))
        return True

    def _do_status_trans(self, cur_status):
        to_st = self.game_status_list[self.game_status_index]
        self.game_result = None
        # 状态转换
        if to_st.tag == GameStatusCode.ST_ShowResult:
            self._play_game()
        self.msg_queue.append(
            MsgFormater.format_game_status_trans(
                cur_status.tag, to_st.tag, to_st.duration, self.game_result))
        self.progress = 0

    def _do_frozen(self):
        self.frozen_time += 1
        # check live status from cache every 5min.
        return True if (self.frozen_time % 300) else self._do_check_live_status()

    def _do_freeze(self, cur_status):
        if self.adapter_status == AdapterFreezing:
            # 冻结游戏，下一个状态为-1
            self.msg_queue.append(MsgFormater.format_game_status_trans(cur_status.tag, FrozenStatusTag, 0))
            self.adapter_status = AdapterFrozen
            self.progress = 0
            self.frozen_time = 0
            return True
        return False

    def _has_next_round(self):
        if self.adapter_status == AdapterStopping:
            self.adapter_status = AdapterStopped
            return False
        if not self._do_check_live_status():
            return False
        # clear previous game data, Perhaps add some statistics here?
        self._reset_game_data()
        return True

    def _do_check_live_status(self):
        if not self.live_cache.is_user_living(self.owner_id):
            logging.debug('live not living, close game.')
            # 查看主播状态, 如果不在直播, 则关闭游戏
            self.adapter_status = AdapterStopped
            return False
        return True

    def _reset_game_data(self):
        self.game_status_index = 0
        self.bet_detail = [{} for _ in range(self.slot_count)]
        self.bet_sum = [0] * self.slot_count
        self.virtual_bet_sum = [0] * self.slot_count
        self.round_start_time = datetime.datetime.utcnow()

    def update_player_count(self, nc):
        if self.robot:
            self.robot.reset(nc, self.slot_count)

    def new_round(self):
        if self.adapter_status == AdapterStarted:
            return not self.game_status_index and not self.progress
        return False

    def ready_to_close(self):
        return self.adapter_status == AdapterStopped or self.adapter_status == AdapterFrozen

    def robot_add_bet(self, slot_id, bet_num):
        if self.current_game_status.tag != GameStatusCode.ST_Betting:
            return
        self.virtual_bet_sum[slot_id] += bet_num

    @profile_func
    def add_bet(self, uid, bet_slot, bet_num):
        '''
        :param uid: 用户ID
        :return err_code, gold_remain
        '''
        if not self.on_betting:
            logging.warning('it is not bet time for user[%s]', uid)
            return ErrorCode.NotOnBetting, None
        # 使用GameCoin来表示金币
        success, gold_remain = self.user_res_cache.consume_gold(uid, bet_num)
        logging.debug('user [%s] consume gold:[%s]', uid, bet_num)
        if not success:
            logging.warning('user[%s] has not enough coins.', uid)
            return ErrorCode.InsufficientGold, None
        # update bet sum info
        if bet_num:
            self.bet_sum[bet_slot] += bet_num
            self.virtual_bet_sum[bet_slot] += bet_num
            # update bet detail
            slot_bet_detail = self.bet_detail[bet_slot]
            if uid in slot_bet_detail:
                slot_bet_detail[uid] += bet_num
            else:
                slot_bet_detail[uid] = bet_num
            CeleryTasks.game_bet.apply_async(args=(
                uid, self.game_type, self.owner_id,
                datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), bet_num, bet_slot))
        self.has_bet = True
        return 0, gold_remain

    def _play_game(self):
        total_bet_in = sum(self.bet_sum)
        prev_storage = self.live_cache.get_storage(self.owner_id)
        # generate game result
        winner = self.game_config.decide_winner(self.game_type, self.bet_sum, prev_storage + total_bet_in)
        game_result = self.game_impl.play_game(winner_slot=winner)
        winner = game_result.winner_index

        multi_val = self.game_config.multiple(self.game_type, winner)
        logging.debug("owner:%s, winner slot:%s, multi:%s", self.owner_id, winner, multi_val)
        pumping_out = self.game_config.pumping_out
        self.game_result = MsgFormater.parse_game_result_to_dict(self.game_type, game_result, pumping_out)
        total_bet_out = multi_val * self.bet_sum[winner]
        new_storage, tax = self.game_config.update_storage(prev_storage, total_bet_in, total_bet_out)
        logging.debug(
            'owner:%s, previous storage:[%s], new storage:[%s]', self.owner_id, prev_storage, new_storage)

        # calculate earned info
        # 结算金币到redis/记录日志
        winner_bet_detail = []
        for uid, bet in self.bet_detail[winner].items():
            earned = bet * multi_val
            lose = int(math.ceil(earned * pumping_out))
            tax += lose
            winner_bet_detail.append((uid, earned - lose))
        self.live_cache.process_game_result(self.owner_id, new_storage - prev_storage, winner_bet_detail)

        try:
            CeleryTasks.game_round_over.apply_async(args=(
                self.owner_id, self.game_type, self.round_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                total_bet_in, total_bet_out, tax, '{}'.format(self.bet_sum), new_storage,
                self.game_impl.serialize_game_result(game_result)
            ))
        except:
            logging.exception('add celery task failed.')

    def game_snapshot(self, uid):
        cur_st = self.game_status_list[self.game_status_index]
        bet_ = [item.get(uid, 0) for item in self.bet_detail]
        return cur_st, bet_

    def get_broadcast_msg_queue(self):
        out = self.msg_queue
        self.msg_queue = []
        return out


class GameManager(object):
    def __init__(self, game_config, redis_wrapper):
        self.timer = None
        self.persistence_timer = None
        self.game_config = game_config
        self.io_loop = tornado.ioloop.IOLoop.current()
        self.wake_interval = 1000
        self.game_adapters = {}
        self.stopping_adapters = []
        self.redis_wrapper = redis_wrapper
        self.livecache = self.redis_wrapper.get_cache(LiveCache.cache_name)

    def do_job(self):
        # 启动定时器
        self.timer = tornado.ioloop.PeriodicCallback(self.time_event, self.wake_interval)
        self.timer.start()
        self.persistence_timer = tornado.ioloop.PeriodicCallback(self.persistence_event, self.wake_interval)
        self.persistence_timer.start()

    def persistence_event(self):
        pass

    @staticmethod
    def broadcast_callback(send_time, msg, resp):
        cost = time.time() - send_time
        logging.debug('msg:[%s]', msg)
        logging.debug('send msg cost: [{0:.3f}].'.format(cost))
        if not resp:
            logging.warning('broadcast message[%s] failed: %s.', msg, resp)

    def time_event(self):
        # 先添加当前展示的游戏时钟函数
        for owner_id, game_adapter in self.game_adapters.items():
            if game_adapter.tick():
                msg_queue = game_adapter.get_broadcast_msg_queue()
                if msg_queue:
                    # only broadcast last message.
                    last_msg = msg_queue[-1]
                    self.livecache.publish_game_data(
                        MsgMode.GAME_NOTIFY_MSG_ROUTING_KEY, game_adapter.owner_id, last_msg)
                if game_adapter.new_round():
                    self.io_loop.add_callback(self.update_player_count, game_adapter)
            else:
                self.livecache.publish_game_data(
                    MsgMode.GAME_OVER_MSG_ROUTING_KEY, game_adapter.owner_id, None)
                self._stop_game(owner_id)
                self.livecache.clear_game_type(owner_id)

        if self.stopping_adapters:
            # 停止中的游戏不将消息发送到直播间
            shadow_adapters = self.stopping_adapters
            self.stopping_adapters = []
            for adapter in shadow_adapters:
                if adapter.ready_to_close():
                    logging.debug('game[%s] exit.', adapter.game_id)
                    # 可以退出的游戏, 不再加到队列中
                    continue
                self.stopping_adapters.append(adapter)
                self.io_loop.add_callback(adapter.tick)

    def _stop_game(self, uid):
        adt = self.game_adapters.pop(uid, None)
        if adt:
            adt.stop()
            self.stopping_adapters.append(adt)
        return True

    def stop_game(self, uid, req_id, req_tag):
        return MsgFormater.format_simple_response(req_id, req_tag, None if self._stop_game(uid) else 400)

    def freeze_games(self, game_type_set):
        for uid, game_adapter in self.game_adapters.items():
            if game_adapter.game_type in game_type_set:
                logging.debug('freeze game of user %s', uid)
                game_adapter.freeze()

    def unfreeze_games(self, game_type_set):
        for uid, game_adapter in self.game_adapters.items():
            if game_adapter.game_type in game_type_set:
                logging.debug('unfreeze game of user %s', uid)
                game_adapter.unfreeze()

    def get_game_type(self, uid):
        adt = self.game_adapters.get(uid, None)
        if adt:
            return adt.game_type
        return None

    def stop_game_when_live_close(self, uid):
        return self._stop_game(uid)

    def validate_game(self, game_type):
        return self.game_config.validate_game(game_type)

    def rpc_start_game(self, uid, game_type):
        if not self.validate_game(game_type):
            return ErrorCode.GameFrozen, None
        pre_game = self.game_adapters.get(uid, None)
        if not pre_game or pre_game.game_type != game_type:
            self._stop_game(uid)
            # 重新创建一个游戏
            adt = GameAdapter(
                self.io_loop, uid, None, self.game_config, game_type, self.game_config.get_game_impl(game_type),
                self.redis_wrapper, self.game_config.get_robot())
            adt.start()
            self.game_adapters[uid] = adt
            logging.debug('start game[%s] for user[%s] success', adt.game_id, uid)
            pre_game = adt
        elif not pre_game.running:
            pre_game.start()
        self.livecache.set_game_type(uid, game_type)
        st, bet = pre_game.game_snapshot(uid)
        return 0, MsgFormater.make_snapshot_data(
            pre_game.game_type, st.tag, st.duration, pre_game.progress,
            bet, pre_game.virtual_bet_sum, pre_game.game_result)

    def rpc_add_bet(self, live_id, uid, slot_id, bet_num):
        adt = self.game_adapters[live_id]
        if not adt:
            return ErrorCode.NotExist
        err_code, remain = adt.add_bet(uid, slot_id, bet_num)
        return err_code or 0

    def rpc_get_game_snapshot(self, live_id, user_id):
        adt = self.game_adapters.get(live_id, None)
        if not adt:
            return ErrorCode.NotExist, None
        st, bet = adt.game_snapshot(user_id)
        return 0, MsgFormater.make_snapshot_data(
            adt.game_type, st.tag, st.duration, adt.progress, bet, adt.virtual_bet_sum, adt.game_result)

    def add_bet_ws(self, live_id, uid, sequence, bet_slot, bet_num):
        adt = self.game_adapters[live_id]
        if not adt:
            return {'t': MsgFormater.msg_BetResponse, 'code': ErrorCode.NotExist, 'data': {'n': sequence}}
        err_code, remain = adt.add_bet(uid, bet_slot, bet_num)
        return {'t': MsgFormater.msg_BetResponse, 'code': err_code, 'data': {'n': sequence}}

    def get_game_snapshot_ws(self, live_id, user_id):
        adt = self.game_adapters.get(live_id, None)
        if not adt:
            return MsgFormater.format_err_response(MsgFormater.msg_GameSnapshot, ErrorCode.NotExist)
        st, bet = adt.game_snapshot(user_id)
        return MsgFormater.format_snapshot(
            adt.game_type, st.tag, st.duration, adt.progress, bet, adt.virtual_bet_sum, adt.game_result)

    def start_game_ws(self, uid, game_type):
        '''
        由外层业务调用start game方法, 在调用时传入消息队列, 所有游戏产生的消息都会放到这个队列中
        :param uid: integer
        :param game_type:  integer
        :returns error_code, game_id
        '''
        if not self.validate_game(game_type):
            return ErrorCode.GameFrozen, None
        pre_game = self.game_adapters.get(uid, None)
        if not pre_game or pre_game.game_type != game_type:
            self._stop_game(uid)
            # 重新创建一个游戏
            adt = GameAdapter(
                self.io_loop, uid, None, self.game_config, game_type, self.game_config.get_game_impl(game_type),
                self.redis_wrapper, self.game_config.get_robot())
            adt.start()
            self.game_adapters[uid] = adt
            logging.debug('start game[%s] for user[%s] success', adt.game_id, uid)
            return None, adt.game_id
        elif not pre_game.running:
            pre_game.start()
        return None, pre_game.game_id

    def update_player_count(self, adapter):
        count = self.livecache.get_player_count(adapter.owner_id)
        logging.debug('update player count in living:%s', adapter.owner_id)
        adapter.update_player_count(max(count, 100))
