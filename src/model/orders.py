# coding: utf-8

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool
from table_base import TableBase


class PayOrder(TableBase):
    __primary_key__ = 'order_no'

    def __init__(self, **kwargs):
        self.order_no = None
        self.app_id = None
        self.trade_no = None
        self.user_id = None
        self.pay_channel = None
        self.trade_status = None
        self.total_fee = None
        self.real_fee = None
        self.cargo_des = None
        self.cargo_id = None
        super(PayOrder, self).__init__(**kwargs)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_orders(cls, user_id, offset, size, success_code):
        '''
        :return:[(order_time, price), ...]
        '''
        q = 'select create_time, real_fee from {} ' \
            'where user_id=%s and trade_status=%s ' \
            'order by create_time desc ' \
            'limit %s, %s'.format(cls.get_table_name())
        conn = get_conn_pool()
        res = conn.query(q, user_id, success_code, offset, size)
        return [(row['create_time'].strftime('%Y-%m-%d'), row['real_fee']) for row in res] if res is not None else None

