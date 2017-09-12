# coding: utf-8

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool
from model.table_base import TableBase

'''
 type_id identifies this report action type.
 1: report against a comment.
 2: report against an active
'''


class Report(TableBase):
    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def add(cls, src_id, dest_id, product_id, type_id):
        query = "insert into reaction (id0, id1, id2, type) values(%s, %s, %s, %s)"
        return get_conn_pool().insert(query, src_id, dest_id, product_id, type_id)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def add_suggest(cls, user_id, content):
        return get_conn_pool().insert('insert into suggestion(uid, detail)values(%s, %s)', user_id, content)
