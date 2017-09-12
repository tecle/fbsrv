# coding: utf-8


import os

import torndb
from celery import Celery

work_dir = os.getcwd()

app = Celery('third_party.celery_task')
db = []


class UserDataType(object):
    LoginPre = 'login_pre'
    LoginDays = 'login_days'
    LoginReward = 'login_reward'
    YxToken = 'yx_token'
    Credits = 'rsc_credit'
    RealGold = 'rsc_gold_real'
    FreeGold = 'rsc_gold_free'
    TotalMoney = 'rk_money'
    Charm = 'rk_charm'
    Latitude = 'latitude'
    Longitude = 'longitude'


class ActiveDataType(object):
    ViewCount = 'a_see'
    LikeCount = 'like_count'
    CommentCount = 'comment_count'


@app.task
def update_user_data(user_id, data_type, value):
    '''
    :param data_type: UserDataType
    '''
    db[0].update('update user_resource set %s=%%s where id=%%s' % data_type, value, user_id)


@app.task
def update_topic_view_count(active_id, new_count):
    db[0].update('update topic_log set s_sees=%s where id=%s', new_count, active_id)


@app.task
def update_topic_acitve_count(active_id, new_count):
    db[0].update('update topic_log set s_tpcs=%s where id=%s', new_count, active_id)


@app.task
def add_like_log(user_id, active_id, liked):
    db[0].insert('insert into like_log(uid, aid, liked)values(%s,%s,%s)', user_id, active_id, liked)


@app.task
def update_active_data(active_id, active_data_type, new_data):
    '''
    :param active_data_type:ActiveDataType
    '''
    db[0].update('update active_log set %s=%%s where id=%%s' % active_data_type, new_data, active_id)


@app.task
def add_suggestion(uid, content):
    db[0].insert('insert into suggestion(uid, detail)values(%s, %s)', uid, content)


@app.task
def add_report(reporter_id, target_id, target_owner_id, report_type):
    db[0].insert("insert into reaction (id0, id1, id2, type) values(%s, %s, %s, %s)",
                 reporter_id, target_owner_id, target_id, report_type)


if __name__ == '__main__':
    print 'Usage:\ncelery_task /path/to/server.cfg (celery task start params)' \
          '\ncelery start param: -A celery_task -c 1 worker --l=info -f log_file]'
    import sys

    sys.path.append(os.path.join(work_dir, 'src'))
    sys.path.append(os.path.join(work_dir, 'libs'))
    from configs import config_wrapper as Configs

    cfg_file_path = sys.argv[1]
    cfg = Configs.ConfigWrapper()
    cfg.set_config_component('mysql', Configs.MysqlConfig())
    if not cfg.parse(cfg_file_path):
        print ("Parse config file [%s] failed." % cfg_file_path)
        exit(1)
    db.append(torndb.Connection(cfg.mysql.host, cfg.mysql.database, cfg.mysql.user, cfg.mysql.pwd, time_zone="+8:00"))
    # turn into background process
    args = sys.argv[1:]
    app.start(argv=args)
