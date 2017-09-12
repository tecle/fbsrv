# coding: utf-8

import json
import math
import random
import logging
from collections import namedtuple
from games.niuniu import NiuNiuFor3Player
from games.zhajinhua import ZhaJinHua
from games.taxas_poker import TaxasGame
from games.horserace import HorseRace
from games.carloops import CarLoops

MinBetAmountRequired = 10


class ConfigItem(object):
    __slots__ = []

    def __init__(self, **kwargs):
        for field in self.__slots__:
            setattr(self, field, kwargs.get(field, None))


class GiftItem(object):
    __slots__ = ['id', 'title', 'cost', 'pic_res', 'has_special_effects', 'spe_res']

    def __init__(self, gid, title, cost, pic_res, spe=False, spe_res=None):
        self.id = gid
        self.title = title
        self.cost = cost
        self.pic_res = pic_res
        self.has_special_effects = spe
        self.spe_res = spe_res


class GiftConfig(object):
    def __init__(self, json_file):
        self.version = 0
        self.gifts_map = {}
        self.gifts_item = []
        self.parse(json_file)

    def parse(self, json_file):
        with open(json_file) as f:
            obj = json.load(f)
            self.version = obj['ver']
            for item in obj['gifts']:
                gi = GiftItem(item['id'], item['title'], item['cost'], item['picRes'], item['doSpe'], item['speRes'])
                self.gifts_map[gi.id] = gi
                self.gifts_item.append(gi)

    def get_gift_cost(self, gift_id):
        if gift_id not in self.gifts_map:
            return None
        return self.gifts_map[gift_id].cost


GameStatus = namedtuple("GameStatus", ('duration', 'tag'))


class GameConfigItem(object):
    def __init__(self, game_type, title, pic, multiple, status, cls):
        self.type = game_type
        self.pic = pic
        self.multiple = multiple
        self.status = []
        for st in status:
            self.add_status(st)
        self.title = title
        self.impl_cls = cls
        self.changed = False
        self.string = None
        self.frozen = False

    def get_inst(self):
        inst = self.impl_cls()
        inst.set_game_status(self.status)
        return inst

    def slot_multiple(self, slot_id):
        return self.multiple[slot_id]

    def add_status(self, st_obj):
        self.status.append(GameStatus(duration=st_obj['duration'], tag=st_obj['status-id']))

    def to_json(self):
        return {
            'id': self.type,
            'pic': self.pic,
            'multiple': self.multiple,
            'status': [{'duration': st.duration, 'id': st.tag} for st in self.status],
            'title': self.title
        }

    def __str__(self):
        if not self.changed and self.string:
            return self.string
        self.string = json.dumps(self.to_json())
        return self.string


class GameConfig(object):
    GameTagMapping = {
        1: ('ZhaJinHua', ZhaJinHua, 3),
        2: ('NiuNiu3', NiuNiuFor3Player, 3),
        3: ('TaxasPoker', TaxasGame, 3),
        4: ('HorseRace', HorseRace, 3),
        5: ('CarLoops', CarLoops, 6)
    }

    def __init__(self, json_file):
        self.version = 0
        self.game_list = []
        self.storage_min = 0
        self.storage_max = 5000000
        self.deduct_rate = 0.01
        self.pumping_out = 0.03
        self.robot_bet = None
        self.parse_json_file(json_file)
        self.init_robot_bet()

    def _tag_to_type(self, tag):
        for game_type, item in self.GameTagMapping.items():
            if item[0] == tag:
                return game_type, item[1]
        logging.error('tag[%s] not found.' % tag)
        return -1, None

    def _reset_by_str(self, s):
        try:
            obj = json.loads(s)
            version = obj['ver']
            g_cfg = obj['global']
            storage_limit = (g_cfg['storage_min'], g_cfg['storage_max'])
            deduct_rate = g_cfg['deduct_rate']
            pumping_out = g_cfg['pumping_out']
            games = []
            for item in obj['games']:
                game_type, game_cls = self._tag_to_type(item.pop('tag'))
                if game_type < 0:
                    raise Exception('Invalid tag.')
                item['game_type'] = game_type
                item['cls'] = game_cls
                ci = GameConfigItem(**item)
                while len(games) < game_type:
                    games.append(None)
                games.append(ci)
        except:
            logging.exception('reset game list config with [%s] failed.', s)
            raise
        else:
            self.version = version
            self.storage_min, self.storage_max = storage_limit
            self.deduct_rate = deduct_rate
            self.pumping_out = pumping_out
            self.game_list = games

    def validate_game(self, game_type):
        return not self.game_list[game_type].frozen

    def change_storage_limit(self, vmin, vmax):
        self.storage_min, self.storage_max = vmin, vmax

    def freeze_game(self, game_type):
        self.game_list[game_type].frozen = True
        self.version += 1

    def unfreeze_game(self, game_type):
        self.game_list[game_type].frozen = False
        self.version += 1

    def parse_json_file(self, json_file):
        with open(json_file) as f:
            self._reset_by_str(f.read())

    def game_status(self, game_id):
        return self.game_list[game_id].status

    def decide_winner(self, game_type, bet_info, current_storage):
        '''
        :param game_type: game type.
        :param bet_info: [bet_val, bet_val, ...]当前下注情况, 从slot 0到slot N
        :param current_storage: 当前的库存(包括本局的总下注)
        :return: 获胜者所在的slot值, 若允许随机, 则返回None
        '''
        game_conf = self.game_list[game_type]
        max_out = min_out = bet_info[0] * game_conf.slot_multiple(0)
        max_idx = min_idx = 0
        for i in range(1, len(bet_info)):
            winner_out = bet_info[i] * game_conf.slot_multiple(i)
            if max_out < winner_out:
                max_out = winner_out
                max_idx = i
            elif min_out > winner_out:
                min_out = winner_out
                min_idx = i
        if current_storage < self.storage_min:
            return min_idx
        if current_storage - max_out >= 0:
            return max_idx if current_storage > self.storage_max else None
        # 如果处于亏损状态, 则压注最少的赢
        return min_idx

    def winner_tax(self, out_sum):
        return int(math.ceil(out_sum * self.pumping_out))

    def update_storage(self, current_storage, total_bet_in, total_bet_out):
        '''
        :param current_storage: 当前库存值
        :param total_bet_in: 总输入
        :param total_bet_out: 总输出
        :return: 新的库存值, 衰减值
        '''
        current_storage = current_storage + total_bet_in - total_bet_out
        if current_storage < self.storage_min:
            return current_storage, 0
        deduct_val = int(math.ceil(current_storage * self.deduct_rate))
        return current_storage - deduct_val, deduct_val

    def get_earned(self, bet_info, multiple):
        '''
        :param bet_info: 当前slot的下注信息{uid: GameCoin, ...},
        :param multiple: multiple rate.
        :return [(uid, earned), ...]
        '''
        return [(uid, bet * multiple) for uid, bet in bet_info.items()]

    def multiple(self, game_type, slot_id):
        '''
        根据游戏类型以及槽位决定倍率
        '''
        return self.game_list[game_type].slot_multiple(slot_id)

    def get_game_impl(self, game_type):
        return self.game_list[game_type].get_inst()

    def init_robot_bet(self):
        self.robot_bet = []
        # ((chance, min_rate, max_rate),...)
        x = ((10, 10, 10), (30, 11, 30), (35, 31, 60), (15, 61, 90), (10, 91, 100))
        s = 0
        for item in x:
            chance = item[0]
            rate_s, rate_e = item[1], item[2]
            for i in range(s, s + chance):
                self.robot_bet.append(random.randint(rate_s, rate_e))
            s += chance

    def get_robot(self):
        return Robot(self.robot_bet)


class Robot(object):
    def __init__(self, bet_cfg):
        self.robot_bet = bet_cfg
        self.avg = 0
        self.slot_count = 3
        self.bet_time = 40
        self.robot_num = 0

    def reset(self, person_num, slot_count=None):
        self.slot_count = slot_count or self.slot_count
        self.bet_time = random.randint(10, 40)
        self.robot_num = int(math.ceil(person_num * 0.1))
        self.avg = 0
        idx = random.randint(0, len(self.robot_bet)) - 1
        if idx > 0:
            # 每秒的下注额度
            self.avg = int(math.ceil(1.0 * self.robot_bet[idx] * self.robot_num / self.bet_time))

    def bet(self):
        if not self.avg:
            return None, None
        # 每次有一部分的robot进行下注, 下注在任意槽
        bet_person_num = random.randint(1, self.robot_num)
        return random.randint(0, self.slot_count - 1), bet_person_num * self.avg * MinBetAmountRequired
