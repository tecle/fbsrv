# coding:utf-8

import time
import logging
import base64
import json
import hashlib
import datetime
import random
from collections import namedtuple
from functools import wraps
from utils.common_define import RewardType

ApkSession = namedtuple('ApkSession', ('req_exist', 'token', 'owner'))
ApkToken = namedtuple('ApkToken', ('token', 'machine'))


def profile_func(func):
    @wraps(func)
    def do_func(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        # logging.debug('PROFILE: %s cost %.3fms', func.__name__, (time.time() - start) * 1000)
        return res

    return do_func


def make_force_offline_msg():
    return json.dumps({
        'type': 4,
        'msg': 'You are kicked by another user.',
        'ts': int(time.time())
    })


def make_like_notify_msg(liker, active_id, summary):
    return json.dumps({
        'type': 1,
        'from': liker,
        'aid': active_id,
        'refer': summary,
        'ts': int(time.time())
    })


def make_comment_notify_msg(commenter, active_id, comment_id, comment_data, summary):
    return json.dumps({
        'type': 2,
        'from': commenter,
        'aid': active_id,
        'cid': comment_id,
        'data': comment_data,
        'refer': summary,
        'ts': int(time.time())
    })


def make_solve_pay_problem_msg(qid):
    return json.dumps({
        'type': 3,
        'qid': qid,
        'ts': int(time.time())
    })


def simple_profile(func):
    @wraps(func)
    def record(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        logging.info(
            "function[%s], start[%f], end[%f], spent[%f]ms" % (func.func_name, begin, end, (end - begin) * 1000))
        print "function[%s], start[%f], end[%f], spent[%f]ms" % (func.func_name, begin, end, (end - begin) * 1000)
        return ret

    return record


def make_key(country, phone):
    ''' make key in redis to get user id. style:key-value'''
    return "%s:%s" % (country, phone)


def make_user_status_key(user_id):
    return 'usr:%s' % user_id


def singleton_wrapper(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance


def decode_pb_str(s, pb_obj):
    # ss = s.decode('hex')
    ss = base64.b64decode(s)
    pb_obj.ParseFromString(ss)


def encode_pb_str(s):
    # return s.encode('hex')
    return base64.b64encode(s)


class SingletonBase(type):
    def __init__(cls, name, bases, dict):
        super(SingletonBase, cls).__init__(name, bases, dict)
        cls._instance = None

    def __call__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = super(SingletonBase, cls).__call__(*args, **kw)
        return cls._instance


def datetime_to_timestamp(dt):
    return int(time.mktime(dt.timetuple()))


def datetime_to_timestamp_ms(dt):
    return int(time.mktime(dt.timetuple()) * 1000)


def split_hobbies_to_list(hobbies_num):
    nums = (1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4, 1 << 5, 1 << 6, 1 << 7, 1 << 8, 1 << 9, 1 << 10,
            1 << 11, 1 << 12, 1 << 13, 1 << 14, 1 << 15, 1 << 16, 1 << 17, 1 << 18, 1 << 19,
            1 << 20, 1 << 21, 1 << 22, 1 << 23, 1 << 24, 1 << 25, 1 << 26, 1 << 27, 1 << 28,
            1 << 29, 1 << 30, 1 << 31, 1 << 32, 1 << 33, 1 << 34, 1 << 35, 1 << 36, 1 << 37,
            1 << 38, 1 << 39, 1 << 40, 1 << 41, 1 << 42, 1 << 43, 1 << 44, 1 << 45, 1 << 46,
            1 << 47, 1 << 48, 1 << 49, 1 << 50, 1 << 51, 1 << 52, 1 << 53, 1 << 54, 1 << 55,
            1 << 56, 1 << 57, 1 << 58, 1 << 59, 1 << 60, 1 << 61, 1 << 62, 1 << 63)
    ret = []
    for i, item in enumerate(nums):
        if hobbies_num & item > 0:
            ret.append(i)
    return ret


def merge_hobbies_to_number(hobby_list):
    nums = (1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4, 1 << 5, 1 << 6, 1 << 7, 1 << 8, 1 << 9,
            1 << 10, 1 << 11, 1 << 12, 1 << 13, 1 << 14, 1 << 15, 1 << 16, 1 << 17, 1 << 18,
            1 << 19, 1 << 20, 1 << 21, 1 << 22, 1 << 23, 1 << 24, 1 << 25, 1 << 26, 1 << 27,
            1 << 28, 1 << 29, 1 << 30, 1 << 31, 1 << 32, 1 << 33, 1 << 34, 1 << 35, 1 << 36,
            1 << 37, 1 << 38, 1 << 39, 1 << 40, 1 << 41, 1 << 42, 1 << 43, 1 << 44, 1 << 45,
            1 << 46, 1 << 47, 1 << 48, 1 << 49, 1 << 50, 1 << 51, 1 << 52, 1 << 53, 1 << 54,
            1 << 55, 1 << 56, 1 << 57, 1 << 58, 1 << 59, 1 << 60, 1 << 61, 1 << 62, 1 << 63)
    ret = 0
    for hobby in hobby_list:
        ret |= nums[hobby]
    return ret


def calculate_sign(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def get_utc_timestamp_ms():
    x = datetime.datetime.utcnow()
    y = time.mktime(x.utctimetuple())
    return int(y * 1000 + x.microsecond / 1000)


def validate_position_pair(longitude, latitude):
    return abs(longitude) <= 180 and abs(latitude) <= 85


def map_reward_type_to_int(reward_type, ret=('GOLD',)):
    return ret.index(reward_type)


def parse_reward_in_json_obj(reward, dest):
    for item in dir(RewardType):
        if item.startswith('__'):
            continue
        if item in reward:
            dest.append((getattr(RewardType, item), reward[item]))


def get_star(
        month, day, d=((1, 20), (2, 19), (3, 21), (4, 21), (5, 21), (6, 22),
                       (7, 23), (8, 23), (9, 23), (10, 23), (11, 23), (12, 22)),
        stars=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)):
    # stars = (u'摩羯座', u'水瓶座', u'双鱼座', u'白羊座', u'金牛座', u'双子座', u'巨蟹座', u'狮子座', u'处女座', u'天秤座', u'天蝎座', u'射手座')
    return stars[len(filter(lambda y: y <= (month, day), d)) % 12]


def get_age(year, month, day):
    born = datetime.date(year, month, day)
    today = datetime.date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:
        # raised when birth date is February 29
        # and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day - 1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def generate_nonce_str(length=16):
    candidate = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
    return ''.join(random.sample(candidate, length))


def generate_order_no(order_type):
    '''
    :param order_type: int, indicate the type of pay channel, ie: 1, weixin; 2, zhifubao
    :return:
    '''
    order = int(time.time() * 1000) * 10000 + random.randint(0, 999) * 10 + order_type
    return order


def get_geohash_precision_by_range(wanted):
    '''meter'''
    info = (2500000, 630000, 78000, 20000, 2400, 610, 76, 19, 2)
    for i, p in enumerate(info):
        if wanted < p:
            return i or 1
    return len(info)


def decode_token(src):
    decoder = (
        '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
        '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
        '0', 'e', '0', '0', '9', 'l', 'F', 'L', 'M', 'x', 'f', '1', 'X', 'T', 's', '0', '0', '0', '0', '0', '0', 'o',
        '6', 'Y', '4', 'I', 'v', 'N', ':', 'h', 'j', 'a', 'b', 'p', 'S', '8', 't', 'Z', 'm', 'E', 'Q', 'J', 'B', 'C',
        '7', 'd', 'D', '0', '0', '0', '0', '0', '0', '-', 'q', 'y', 'H', 'V', 'P', 'U', 'K', '0', '2', 'u', 'k', 'r',
        'R', 'g', 'A', 'W', 'i', 'n', '5', 'c', 'w', 'G', 'O', '3', 'z', '0', '0', '0', '0', '0')
    return ''.join([decoder[ord(ch)] for ch in src])


def encode_token(src):
    encoder = (
        '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
        '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
        '0', 'a', '0', '0', 'i', '7', 'j', 'y', 'D', 't', 'B', 'X', 'O', '0', 'H', '0', '0', '0', '0', '0', '0', 'p',
        'V', 'W', 'Z', 'S', '2', 'w', 'd', 'E', 'U', 'h', '3', '4', 'G', 'x', 'f', 'T', 'n', 'N', '9', 'g', 'e', 'q',
        '8', 'C', 'Q', '0', '0', '0', '0', '0', '0', 'K', 'L', 'u', 'Y', '-', '6', 'o', 'I', 'r', 'J', 'l', '1', 'R',
        's', 'A', 'M', 'b', 'm', ':', 'P', 'k', 'F', 'v', '5', 'c', 'z', '0', '0', '0', '0', '0')
    return ''.join([encoder[ord(ch)] for ch in src])


def helper():
    s = '0 1 2 3 4 5 6 7 8 9 - :'.split(' ')
    s.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
    s.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])
    import copy
    src = copy.copy(s)
    random.shuffle(s)
    print src
    print s
    encoder = ['0'] * 128
    decoder = ['0'] * 128
    # src: abcd
    # s:   dbca    out['a'] = 'd'
    for i, ch in enumerate(src):
        print ord(ch)
        encoder[ord(ch)] = s[i]
        decoder[ord(s[i])] = ch
    print tuple(encoder)
    print tuple(decoder)


class SecureTool(object):
    def __init__(self, secret):
        self.secret = secret

    def secure_dict(self, pay_order):
        '''
        :param pay_order: PayOrderData
        '''
        pay_order.time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        sign_str = '{}&{}&{}&{}'.format(pay_order.order_no, pay_order.pay_str, pay_order.time, self.secret)
        pay_order.sign = hashlib.md5(sign_str).hexdigest()
