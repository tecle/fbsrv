# coding:utf-8

import inspect
from collections import namedtuple

from tornado.concurrent import run_on_executor

from model.db_wrapper import get_conn_pool

Wanted = namedtuple('Wanted', ['attr'])


class TableBase(object):
    __primary_key__ = 'id'
    __fields_cache__ = {}
    __slots__ = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_table_name(cls):
        return getattr(cls, '__table_name__', cls.__name__)

    def reset_fields(self):
        for field in self.get_fields():
            setattr(self, field, None)

    def get_fields(self):
        table_name = self.get_table_name()
        if table_name in self.__fields_cache__:
            return self.__fields_cache__[table_name]
        self.__fields_cache__[table_name] = fields = []
        for attr in dir(self):
            if attr.startswith('_') or inspect.ismethod(getattr(self, attr)):
                continue
            fields.append(attr)
        return fields

    def parse_from_sql_response(self, response):
        fields = self.get_fields()
        for field in fields:
            setattr(self, field, response.get(field, None))

    @classmethod
    def _get_many(cls, query, *args):
        sql_res = get_conn_pool().query(query, *args)
        res = []
        if sql_res is None:
            return False, None
        for item in sql_res:
            inst = cls()
            inst.parse_from_sql_response(item)
            res.append(inst)
        return True, res

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_one(cls, target_value, target_field=None):
        if not target_field:
            target_field = cls.__primary_key__
        inst = cls()
        query = 'select * from %s where %s=%%s' % (cls.get_table_name(), target_field)
        res = get_conn_pool().get(query, target_value)
        if not res:
            return None
        inst.parse_from_sql_response(res)
        return inst

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_specified_rows(cls, targets):
        query = 'select * from %s where %s in (%s)' % (cls.get_table_name(), cls.__primary_key__, ','.join(targets))
        return cls._get_many(query)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_some(cls, condition, order=None, limit=None, *args):
        '''
        :param condition: str for condition
        :param limit: (start, size)
        :param order:("field", "desc"/"asc")
        :param args: condition args
        :return:
        '''
        order_phrase = 'order by {} {}'.format(*order) if order else ''
        limit_phrase = 'limit {}, {}'.format(*limit) if limit else ''
        query = 'select * from {} where {} {} {}'.format(cls.get_table_name(), condition, order_phrase, limit_phrase)
        return cls._get_many(query, *args)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_rows_by_pk(cls, pk, bigger_than_it, size, desc=True):
        query = 'select * from {0} where {1}{2}{3} order by {1} {4} limit {5}'.format(
            cls.get_table_name(), cls.__primary_key__,
            '>' if bigger_than_it else '<', pk, 'desc' if desc else 'asc', size)
        return cls._get_many(query)

    @classmethod
    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def get_all(cls, offset, size, desc=True):
        query = 'select * from {0} order by {1} {2} limit {3}, {4}'.format(
            cls.get_table_name(), cls.__primary_key__, 'desc' if desc else 'asc', offset, size)
        return cls._get_many(query)

    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def save(self):
        fields, values = [], []
        for field in self.get_fields():
            if getattr(self, field) is not None:
                fields.append(field)
                values.append(getattr(self, field))
        query = 'insert into %s (%s) values (%s)' % \
                (self.get_table_name(), ','.join(fields), ','.join(['%s'] * len(fields)))
        return get_conn_pool().insert(query, *values)

    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def update_to_db(self):
        fields, values = [], []
        pk = self.__primary_key__
        for field in self.get_fields():
            if getattr(self, field) is not None and field != pk:
                fields.append(field)
                values.append(getattr(self, field))
        if not fields:
            # 没有数据更新
            return 0
        query = 'update %s set %s where %s=%%s' % \
                (self.get_table_name(), ','.join(['%s=%%s' % item for item in fields]), pk)
        values.append(getattr(self, pk))
        return get_conn_pool().update(query, *values)

    @run_on_executor(executor='_thread_pool', io_loop='_io_loop')
    def update_from_db(self):
        '''
        update Wanted field from database.
        notice: make sure you have set primary key's value before update from db.
        :return: boolean(success/fail)
        '''
        fields = [field for field in self.get_fields() if getattr(self, field) == Wanted]
        pk_val = getattr(self, self.__primary_key__)
        assert pk_val is not None and pk_val != Wanted
        query = 'select %s from %s where %s=%%s' % (
            ','.join(fields), self.get_table_name(), self.__primary_key__)
        res = get_conn_pool().get(query, pk_val)
        if not res:
            return False
        for k, v in res.items():
            setattr(self, k, v)
        return True

    def __str__(self):
        return ','.join(('%s=%s' % (key, getattr(self, key)) for key in self.get_fields()))
