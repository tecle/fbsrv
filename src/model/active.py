# coding: utf-8

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool
from model.table_base import TableBase
from model.tableconstant import (TB_ACTIVE, TB_USER_INFO, USER_BANNED)
from utils.util_tools import datetime_to_timestamp


class Active(TableBase):
    __primary_key__ = 'id'
    __table_name__ = TB_ACTIVE

    def __init__(self, **kwargs):
        self.id = None
        self.uid = None
        self.tid = None
        self.content = None
        self.pics = None
        self.deleted = None
        self.permission = None
        self.location = None
        self.latitude = None
        self.longitude = None
        self.geo_code = None
        self.create_time = None
        super(Active, self).__init__(**kwargs)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def insert(cls, owner_id, topic_id, content, pictures, location, lon, lat, geo_code):
        query = "insert into {} (uid, tid, content, pics, location, longitude, latitude, geo_code)" \
                "values(%s, %s, %s, %s, %s, %s, %s, %s)".format(TB_ACTIVE)
        res = get_conn_pool().insert(query, owner_id, topic_id, content, pictures, location, lon, lat, geo_code)
        if res:
            return res
        return 0

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_actives_by_range(cls, geo_code_prefix, start, size):
        sql = " select id,uid,tid,content,pics,t1.location ,t1.create_time,t2.avatar,t2.nick_name " \
              " from {} as t1 inner join {} as t2 on t1.uid = t2.user_id where geo_code like '{}%%' " \
              " and deleted=False and ban_status!={}" \
              " order by create_time desc limit {}, {}".format(
            TB_ACTIVE, TB_USER_INFO, geo_code_prefix, USER_BANNED, start, size)
        return get_conn_pool().query(sql)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def select_one(cls, active_id, active_pb):
        query = 'select id, uid, tid, content, pics, deleted, ' \
                ' location, create_time, latitude, longitude ' \
                ' from {} where id=%s'.format(TB_ACTIVE)
        active_obj = get_conn_pool().get(query, active_id)
        if not active_obj or active_obj['deleted']:
            return False
        active_pb.activeId = active_obj['id']
        active_pb.ownerId = active_obj['uid']
        active_pb.topicId = active_obj['tid']
        active_pb.content = active_obj['content']
        active_pb.pictures = active_obj['pics']
        active_pb.location = active_obj['location']
        active_pb.publishTime = datetime_to_timestamp(active_obj['create_time'])
        return True

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def delete(cls, active_id):
        query = 'update {} set deleted=True where id=%s '.format(TB_ACTIVE)
        return get_conn_pool().update(query, active_id) > 0

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_latest_actives(cls, topic_id, size):
        q = " select id,uid,tid,content,pics,t1.location ,t1.create_time,t2.avatar,t2.nick_name " \
            " from {} as t1 inner join {} as t2 on t1.uid = t2.user_id where tid={} " \
            " and t1.deleted=False and t2.ban_status!={} " \
            " order by create_time desc limit 0, {}".format(TB_ACTIVE, TB_USER_INFO, topic_id, USER_BANNED, size)
        return get_conn_pool().query(q)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_older_actives(cls, topic_id, start_id, size):
        q = " select id,uid,tid,content,pics,t1.location ,t1.create_time,t2.avatar,t2.nick_name " \
            " from {} as t1 inner join {} as t2 on t1.uid = t2.user_id where tid={} " \
            " and t1.deleted=False and t2.ban_status!={} and t1.id < {} " \
            " order by create_time desc limit 0, {}".format(
            TB_ACTIVE, TB_USER_INFO, topic_id, USER_BANNED, start_id, size)
        return get_conn_pool().query(q)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_actives_in_list(cls, active_id_list, actives_pb):
        query = 'select * from %s where id in (%s)' % (TB_ACTIVE, active_id_list)
        result = get_conn_pool().query(query)
        parse_actives_to_pb(result, actives_pb)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_actives_meta_in_list(cls, active_id_list, actives_pb):
        query = 'select id, content, pics from %s where id in (%s)' % (TB_ACTIVE, active_id_list)
        r = get_conn_pool().query(query)
        if r is None:
            return False
        for a in r:
            actives_pb.add_active(a['id'], a['content'], a['pics'])
        return True


def parse_actives_to_pb(result, actives_pb):
    for active in result:
        active_pb = actives_pb.actives.add()
        active_pb.Initialize()
        ac = active_pb.active
        ac.activeId = active['id']
        ac.ownerId = active['uid']
        ac.topicId = active['tid']
        ac.content = active['content']
        ac.pictures = active['pics']
        ac.location = active['location']
        ac.publishTime = datetime_to_timestamp(active['create_time'])
