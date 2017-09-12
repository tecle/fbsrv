# coding: utf-8

from __future__ import absolute_import, unicode_literals, print_function
from .funboxapp import app
from .funboxapp import AppResource
import datetime
import logging
import json
import time


@app.task
def push_comment_message_to_user(target_id, commenter, active_id, comment_id, comment_data, summary):
    data = json.dumps({
        'type': 2,
        'from': commenter,
        'aid': active_id,
        'cid': comment_id,
        'data': comment_data,
        'refer': summary,
        'ts': int(time.time())
    })
    AppResource().push_data(target_id, data)


@app.task
def push_like_message_to_user(target_id, liker, active_id, summary):
    data = json.dumps({
        'type': 1,
        'from': liker,
        'aid': active_id,
        'refer': summary,
        'ts': int(time.time())
    })
    AppResource().push_data(target_id, data)


@app.task
def create_yx_user_failed(user_id, code, why):
    AppResource().insert_to_database(
        'insert into FailedOperation(op_type, message) values(%s, %s)',
        1, 'user:{};code:{};reason:{}'.format(user_id, code, why)
    )


@app.task
def refresh_yx_token_failed(user_id, code, why):
    AppResource().insert_to_database(
        'insert into FailedOperation(op_type, message) values(%s, %s)',
        2, 'user:{};code:{};reason:{}'.format(user_id, code, why)
    )


@app.task
def like_active(user_id, active_id, is_like):
    AppResource().insert_to_database(
        'insert into LikeActiveData(user_id, active_id, is_like) values(%s, %s, %s) on duplicate key update is_like=%s',
        user_id, active_id, is_like, is_like
    )


@app.task
def user_login(user_id, imei, ip, location):
    AppResource().insert_to_database(
        'insert into LoginData(uid, imei, ip, login_time) values(%s, %s, %s, %s)',
        user_id, imei, ip, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    )
    AppResource().insert_to_database(
        'update user_info_new set location=%s where user_id=%s', location, user_id)


@app.task
def send_gift(user_id, gift_id, target_id, total_cost, amount):
    AppResource().insert_to_database(
        'insert into SendGiftLogs(uid, target, gift_id, cost, amount) values({}, {}, {}, {}, {})'.format(
            user_id, target_id, gift_id, total_cost, amount))


@app.task
def game_round_over(user_id, game_type, start_time, end_time, bet_in, bet_out, tax, bet_detail, storage, result_detail):
    AppResource().insert_to_database(
        'insert into GameRoundsLogs'
        '(uid, game_type, start_time, end_time, bet_in, bet_out, sys_tax, bet_detail, storage, result)'
        'values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        user_id, game_type, start_time, end_time, bet_in, bet_out, tax, bet_detail, storage, result_detail
    )


@app.task
def game_bet(user_id, game_type, owner_id, time, amount, slot_id):
    AppResource().insert_to_database(
        'insert into UserBetLogs(uid, game_type, owner_id, amount, slot_id, bet_time) values (%s, %s, %s, %s, %s, %s)',
        user_id, game_type, owner_id, amount, slot_id, time
    )


@app.task
def add_report(reporter_id, target_id, target_owner_id, report_type):
    AppResource().insert_to_database(
        "insert into Reaction(id0, id1, id2, type) values(%s, %s, %s, %s)",
        reporter_id, target_owner_id, target_id, report_type
    )


@app.task
def app_status_check(start_info):
    logging.info('server start call:{} output:{}'.format(start_info, AppResource().query('show tables')))


@app.task
def opinion_feedback(user_id, user_name, time_str, device, android_version, app_code, net_type, content):
    AppResource().insert_to_database(
        'insert into Suggestion(uid, detail, device, app_code, net_env, android_ver, time)'
        'values(%s, %s, %s, %s, %s, %s, %s)',
        user_id, content, device, app_code, net_type, android_version, time_str)
    AppResource().alert_opinion(
        '用户:{}({})\n'
        '建议: {}\n'
        '时间: {}\n'
        '应用版本代码: {}\n'
        '设备: {}\n'
        '安卓版本: {}\n'
        '网络类型:{}'.format(
            user_name, user_id, content, time_str, app_code, device, android_version, net_type))


@app.task
def consult(user_id, user_name, time_str, device, android_version, app_code, net_type, content):
    AppResource().insert_to_database(
        'insert into Consultion(uid, detail, device, app_code, net_env, android_ver, time)'
        'values(%s, %s, %s, %s, %s, %s, %s)',
        user_id, content, device, app_code, net_type, android_version, time_str)
    AppResource().alert_need_support(
        '用户:{}({})\n'
        '咨询: {}\n'
        '时间: {}\n'
        '应用版本代码: {}\n'
        '设备: {}\n'
        '安卓版本: {}\n'
        '网络类型:{}'.format(
            user_name, user_id, content, time_str, app_code, device, android_version, net_type))
