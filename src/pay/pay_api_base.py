# coding: utf-8


class PayAPiBase(object):
    def __init__(self):
        pass

    @staticmethod
    def construct_attach(uid, cargo_id):
        return '%s-%s' % (uid, cargo_id)

    @staticmethod
    def parse_attach(attach_str):
        '''
        :param attach_str:
        :return: user_id, cargo_id
        '''
        params = attach_str.split('-')
        return params[0], params[1]
