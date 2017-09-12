# coding: utf-8

from __future__ import absolute_import
import time
from .hplcore import gen_prompt, send_http_request, register_user


import_info = "HTTP请求集合"


@gen_prompt('*开启游戏', 'HTTP')
def add_user_to_live_list():
    uid = int(raw_input('主播ID:'))
    gid = int(raw_input('游戏类型:'))
    params = {
        'lid': uid,
        'gType': gid,
        'room': 7662770,
        'op': 'S',
        'reqId': int(time.time())
    }
    send_http_request('/live/play', params)


@gen_prompt('*压注', 'HTTP')
def add_user_to_live_list():
    lid = int(raw_input('主播ID:'))
    amount = int(raw_input('押注数量:'))
    uid = int(raw_input('玩家ID:'))
    slot = int(raw_input('槽:'))
    params = {
        'lid': lid,
        'uid': uid,
        'bet': amount,
        'op': 'B',
        'reqId': int(time.time()),
        'slot': slot
    }
    send_http_request('/live/play', params)


@gen_prompt('*游戏快照', 'HTTP')
def add_user_to_live_list():
    lid = int(raw_input('主播ID:'))
    params = {
        'lid': lid,
        'op': 'P',
        'reqId': int(time.time()),
        'uid': 8
    }
    send_http_request('/live/play', params)


@gen_prompt('*批量添加用户', 'HTTP')
def add_some_users():
    print "用户文件内容: \n每一行代表一个用户;\n一个用户由昵称、性别(0/1)、签名、生日组成(yyyymmdd)，使用空格分割"
    faddr = raw_input('文件地址:')
    with open(faddr) as f:
        for i, line in enumerate(f.read().split('\n')):
            parts = line.split(' ')
            nick = parts[0]
            sex = parts[1]
            sign = parts[2]
            if len(parts[3]) != 8:
                print "Invalid born:" + parts[3]
                continue
            born = '{}-{}-{}'.format(parts[3][:4], parts[3][4:6], parts[3][-2:])
            register_user(nick, sex, sign, born, i + 1)
