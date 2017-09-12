import logging

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool
from model.table_base import TableBase


class Topic(TableBase):
    UPDATE_KEY = ('detail', 'title', 'weight')

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def insert(cls, title, detail, visible, hobbies, pics):
        logging.info("insert new topic to db.")
        query = "call create_topic(%s, %s, %s, %s, %s)"
        ret = get_conn_pool().query(query, title, detail, visible, hobbies, pics)
        if not ret:
            return 0
        return ret[0]['id']

    @classmethod
    def select_all(cls, conn):
        query = "select id, title, detail, visible, hobbies, pics from topics"
        return conn.query(query)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def update_topic(cls, topic_id, **kwargs):
        '''weight=None, detail=None, title=None'''
        tmp = []
        args = []
        for k, w in kwargs.items():
            if w is not None:
                tmp.append(k + '=%s')
                args.append(w)
        args.append(topic_id)
        query = 'update topics set %s where id=%%s' % ','.join(tmp)
        return get_conn_pool().update(query, *args)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def delete_topic(cls, topic_id):
        query = 'update topics set visible=false where id = %s'
        return get_conn_pool().update(query, topic_id)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_topics(cls, start, size):
        query = 'select id,title,detail,pics from topics where visible=true order by weight limit %s, %s'
        return get_conn_pool().query(query, start, size)
