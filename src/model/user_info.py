# coding:utf-8

import cStringIO
import random

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool
from model.table_base import TableBase
from model.tableconstant import (TB_AUTH_PHONE, TB_AUTH_WEIXIN, TB_USER_INFO)
from utils.util_tools import split_hobbies_to_list


class UserInfo(TableBase):
    __primary_key__ = 'user_id'
    __table_name__ = TB_USER_INFO

    def __init__(self, **kwargs):
        self.user_id = None
        self.avatar = None
        self.signature = None
        self.nick_name = None
        self.gender = None
        self.born = None
        self.star = None
        self.hobbies = None
        self.show_pics = None
        self.anchor = None
        self.ban_status = None
        self.create_time = None
        self.location = None
        super(UserInfo, self).__init__(**kwargs)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def update_password_by_phone(cls, phone, pwd):
        query = 'update {} set password=%s where phone=%s'.format(TB_AUTH_PHONE)
        conn = get_conn_pool()
        res = conn.update(query, pwd, phone)
        if res is not None:
            query = "select user_id from {} where phone=%s".format(TB_AUTH_PHONE)
            res = conn.get(query, phone)
            return res['user_id'] if res else 0
        return 0

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def add_hobby(cls, uid, hobby_list):
        query = 'update {} set hobbies=%s where user_id=%s'.format(cls.__table_name__)
        return get_conn_pool().update(query, hobby_list, uid)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def update(cls, uid, **args):
        query = 'update {} set %s where user_id = %s'.format(cls.__table_name__)
        set_pair_list = ['%s=%%(%s)s' % (k, k) for k, v in args.items() if v is not None]
        if not set_pair_list:
            return
        set_str = ",".join(set_pair_list)
        return get_conn_pool().update(query % (set_str, uid), **args)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_login_data(cls, key, password):
        '''
        get login data by country:phone
        :return: user id, user pwd, nickname, avatar, sign
        '''
        query = 'select t1.user_id, nick_name, avatar, signature, ban_status, born, hobbies, gender, show_pics' \
                ' from {} as t1 inner join {} as t2 on t1.user_id = t2.user_id ' \
                ' where t2.phone=%s and t2.password=%s'.format(cls.__table_name__, TB_AUTH_PHONE)
        ret = get_conn_pool().get(query, key, password)
        if ret:
            inst = cls()
            inst.parse_from_sql_response(ret)
            return inst
        return None

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_id_by_phone(cls, key):
        query = 'select user_id ' \
                'from {} ' \
                'where phone=%s'.format(TB_AUTH_PHONE)
        ret = get_conn_pool().get(query, key)
        return ret['user_id'] if ret else None

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def add(cls, key, pwd):
        query = 'call create_user_by_phone(%s, %s)'
        ret = get_conn_pool().query(query, key, pwd)
        if not ret:
            return 0
        return ret[0]['uid_']

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_detail(cls, user_id, user_data):
        query = 'select user_id,avatar,signature,nick_name,gender,born,star,hobbies,show_pics ' \
                'from {} ' \
                'where user_id=%s'.format(cls.__table_name__)
        ret = get_conn_pool().get(query, user_id)
        if ret:
            user_data.id = ret['user_id']
            user_data.avatar = ret['avatar']
            user_data.nickName = ret['nick_name']
            user_data.isMale = ret['gender'] > 0
            user_data.sign = ret['signature']
            user_data.born = ret.born.strftime('%Y-%m-%d')
            user_data.star = ret['star']
            user_data.raw_pics = ret['show_pics']
            tmp = split_hobbies_to_list(ret['hobbies'])
            for tag in tmp:
                user_data.hobbies.append(tag)
            return True
        return False

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_users_pb_info(cls, user_list, users_pb):
        s = ', '.join(['%s'] * len(user_list))
        query = 'select user_id,avatar,signature,nick_name,gender ' \
                'from {} ' \
                'where user_id in ({})'.format(cls.__table_name__, s)
        ret = get_conn_pool().query(query, *user_list)
        for item in ret:
            user_pb = users_pb.add()
            user_pb.id = item['user_id']
            user_pb.avatar = item['avatar']
            user_pb.nickName = item['nick_name']
            user_pb.isMale = item['gender']
            user_pb.signature = item['signature']

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_users_info(cls, user_list):
        s = ', '.join(['%s'] * len(user_list))
        query = 'select user_id, avatar, nick_name ' \
                'from {} ' \
                'where user_id in ({})'.format(cls.__table_name__, s)
        ret = get_conn_pool().query(query, *user_list)
        out = {}
        for item in ret:
            out[item['user_id']] = (item['avatar'], item['nick_name'])
        return out

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_recommend_users(cls, recommend_pb, userID, offset, size, **args):
        '''
        args = {"gender":xxx, "star":xxx}
        return: [UserInfo, UserInfo...]

        '''
        if int(userID):
            query = cStringIO.StringIO()
            query.write('select t1.user_id, t1.hobbies & t2.hobbies as similarity '
                        'from {0} as t1, (select hobbies from {0} where user_id={1}) as t2 '
                        'where '.format(cls.__table_name__, userID))
            conds = ['%s="%s"' % (key, val) for key, val in args.items() if val is not None]
            conds.append('user_id <> %s and ban_status < 2 and nick_name <> "" and avatar <>""' % userID)
            query.write(' AND '.join(conds))
            query.write(' order by similarity limit 0, 300')
            query = query.getvalue()
        else:
            query = "select user_id from {0} order by create_time desc limit 0, 300".format(cls.__table_name__)
        conn = get_conn_pool()
        ret = conn.query(query)

        uid_list = [str(item['user_id']) for item in ret]
        id_list = random.sample(uid_list, min(size, len(uid_list)))

        if id_list:
            query = 'select user_id,gender,born,nick_name,signature,avatar,star,location ' \
                    'from {} where user_id in ({})'.format(cls.__table_name__, ','.join(id_list))
            ret = conn.query(query)
            for obj in ret:
                item = recommend_pb.add()
                item.userId = obj['user_id']
                item.gender = obj['gender']
                item.birth = obj['born'].strftime('%Y-%m-%d')
                item.sign = obj['signature']
                item.nickname = obj['nick_name']
                item.avatar = obj['avatar']
                item.star = obj['star']
                item.site = obj['location']

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_avatar(cls, uid_list):
        q = 'select user_id, avatar from {} where user_id in ({})'.format(cls.__table_name__, ','.join(uid_list))
        res = get_conn_pool().query(q)
        if res:
            return {row['user_id']: row['avatar'] for row in res}
        return res

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def wx_add_user(cls, open_id, union_id, device, refresh_token, refresh_token_time, nick_name, avatar):
        '''
        :return: user_id(None if failed), user_already_exist, extra_db_data(ban_st, avatar, sign, nick)
        '''
        conn = get_conn_pool()
        # get user info by open_id
        res = conn.get(
            'select t1.user_id, t2.ban_status, t2.avatar, t2.signature, t2.nick_name '
            'from {} as t1 inner join {} as t2 '
            'on t1.user_id=t2.user_id '
            'where open_id=%s'.format(TB_AUTH_WEIXIN, cls.__table_name__), open_id)
        if not res:
            # user not exist, create it
            conn.update('start transaction')
            rollback = True
            user_id = None
            for _ in (1,):
                user_id = conn.insert(
                    'insert into {}(nick_name, avatar)values(%s, %s)'.format(cls.__table_name__), nick_name, avatar)
                if not user_id:
                    break
                res = conn.insert(
                    'insert into {}(open_id, union_id, user_id, device, refresh_token, refresh_time) '
                    'values(%s, %s, %s, %s, %s, %s)'.format(TB_AUTH_WEIXIN),
                    open_id, union_id, user_id, device, refresh_token, refresh_token_time)
                if res is None:
                    user_id = None
                    break
                rollback = False
            conn.update('rollback' if rollback else 'commit')
            return user_id, False, (0, avatar, '', nick_name)
        # user exist
        return res['user_id'], True, (res['ban_status'], res['avatar'], res['signature'], res['nick_name'])

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def wx_check_user(cls, user_id, device):
        '''check user is already login by wx'''
        q = 'select device from {} where user_id=%s'.format(TB_AUTH_WEIXIN)
        res = get_conn_pool().get(q, user_id)
        return res and (res['device'] == device)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def wx_update_token(cls, user_id, new_token, refresh_time):
        q = 'update {} set refresh_token=%s, refresh_time=%s where user_id=%s'.format(TB_AUTH_WEIXIN)
        res = get_conn_pool().update(q, new_token, refresh_time, user_id)
        return res is not None

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_users_detail(cls, id_list):
        sql = 'select user_id,avatar,signature,nick_name,gender,born,star' \
              ' from {}' \
              ' where user_id in ({})'.format(cls.__table_name__, ','.join(id_list))
        ret = get_conn_pool().query(sql)
        return {
            row['user_id']: row for row in ret
        } if ret else None
