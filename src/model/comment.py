# coding: utf-8

from tornado.concurrent import run_on_executor
from db_wrapper import get_conn_pool
from table_base import TableBase
from tableconstant import (TB_COMMENTS, TB_USER_INFO)


class Comment(TableBase):
    __primary_key__ = "id"
    __table_name__ = TB_COMMENTS

    def __init__(self, **kwargs):
        self.id = None
        self.aid = None
        self.uid = None
        self.tid = None
        self.tuid = None
        self.content = None
        self.deleted = None
        self.refer = None
        self.create_time = None
        super(Comment, self).__init__(**kwargs)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def add(cls, comment_pb):
        query = "insert into comments(aid, uid, tid, tuid, content, refer) values (%s, %s, %s, %s, %s, %s)"
        return get_conn_pool().insert(query, comment_pb.activeId, comment_pb.ownerId, comment_pb.targetId,
                                      comment_pb.targetUserId, comment_pb.content, comment_pb.targetSummary)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def select_some(cls, active_id, start, size):
        q = 'SELECT t5.*, t6.avatar, t6.nick_name FROM (' \
              'SELECT t3.*, t4.nick_name AS snick FROM(' \
                'SELECT t1.*, t2.content AS scontent FROM(' \
                  'SELECT id,aid,uid,tid,tuid,content,create_time ' \
                  ' FROM {0} WHERE aid = {2} and deleted = FALSE ORDER BY create_time DESC LIMIT {3}, {4}) AS t1' \
                ' LEFT JOIN {0} AS t2 ON t1.tid = t2.id) AS t3 ' \
              ' LEFT JOIN {1} AS t4 ON t3.tuid = t4.user_id) as t5 ' \
            ' INNER JOIN {1} AS t6 on t5.uid=t6.user_id'.format(TB_COMMENTS, TB_USER_INFO, active_id, start, size)
        return get_conn_pool().query(q)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def select_specified(cls, comment_list):
        q = 'select t1.id, t1.uid, t1.content,t1.deleted, t2.avatar, t2.nick_name ' \
            ' from {} as t1 inner join {} as t2 on t1.uid = t2.user_id ' \
            ' where id in ({})'.format(TB_COMMENTS, TB_USER_INFO, ','.join(comment_list))
        return get_conn_pool().query(q)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def delete(cls, comment_id):
        query = 'update comments set deleted = %s where id = %s'
        return get_conn_pool().update(query, True, comment_id)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def detail(cls, comment_id_list):
        query = 'select * from comments where id in({})'.format(comment_id_list)
        return get_conn_pool().query(query)
