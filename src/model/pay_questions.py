# coding: utf-8

from table_base import TableBase


class PayQuestions(TableBase):
    __primary_key__ = 'qid'

    def __init__(self, **kwargs):
        self.qid = None
        self.uid = None
        self.detail = None
        self.step = None
        self.response = None
        self.handler = None
        self.answer_time = None
        self.create_time = None
        super(PayQuestions, self).__init__(**kwargs)