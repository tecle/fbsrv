# coding: utf-8

import json
import logging

from model.response.coredata import AppVersion

CargoType = {
    "STAR": 1,
    "F": 2
}


class CargoItem(object):
    __slots__ = ['id', 'amount', 'price', 'extra', 'des']

    def __init__(self, cargo_id):
        self.id = cargo_id
        self.amount = None
        self.price = None  # 单位为分
        self.extra = 0  # 默认无赠送
        self.des = None

    @property
    def actual_price(self):
        return self.price

    @property
    def total_amount(self):
        return self.extra + self.amount

    def dump_to_json(self):
        return {
            'id': self.id,
            'num': self.amount,
            'rmb': self.price,
            'extra': self.extra,
            'info': self.des
        }

    def __eq__(self, other):
        '''比较给定的ID是否是这个config item'''
        return other == self.id


class CargoConfig(object):
    def __init__(self):
        self.cargo_list = None
        self.cargo_map = None
        self.version = None
        self.json_obj = None

    def __getitem__(self, item_id):
        return self.cargo_map.get(item_id, None)

    def __repr__(self):
        return self.json_obj

    @property
    def data(self):
        return self.json_obj

    @property
    def routing_key(self):
        return 'cargocfg'

    def reset_config(self, obj):
        try:
            cargo_list = []
            cargo_map = {}
            version = obj.get('ver', 0)
            for cargo_obj in obj['items']:
                cargo_id = cargo_obj['id']
                cargo_item = CargoItem(cargo_id)
                cargo_item.amount = cargo_obj['num']
                cargo_item.price = cargo_obj['rmb']
                cargo_item.extra = cargo_obj['extra']
                cargo_item.des = cargo_obj['info']
                cargo_map[cargo_id] = cargo_item
                cargo_list.append(cargo_item)
        except:
            logging.exception('reset cargo info failed:[{}]'.format(obj))
            raise
        else:
            self.cargo_list = cargo_list
            self.cargo_map = cargo_map
            self.version = version
            self.json_obj = obj

    def parse_file(self, path):
        with open(path) as f:
            self.reset_config(json.load(f))

    def reset_by_string(self, string):
        self.reset_config(json.loads(string))

    def validate_version(self, ver):
        return self.version == ver


class AppConfig(object):
    def __init__(self):
        self.version_obj = None
        self.banner_obj = None
        self.cargo_obj = CargoConfig()
        self.cache_response = None
        self.cache_data = AppVersion()

    def reset_version(self, data):
        '''{
            'code': self.curVerCode,
            'text': self.curVerText,
            'min': self.minVerCodeRequired,
            'dl': self.downloadUrl,
            'info': self.verInfo
            }
        '''
        logging.info('update version config with data:[{}]'.format(data))
        self.version_obj = data
        self.cache_data.version = data
        self.cache_response = self.cache_data.SerializeToString()

    @property
    def version_routing_key(self):
        return 'Ver'

    def reset_banner(self, data):
        '''
        [{'type':1, 'data':'this is data str'}, ...]
        '''
        logging.info('update banner config with data:[{}]'.format(data))
        self.banner_obj = data
        self.cache_data.banner = data
        self.cache_response = self.cache_data.SerializeToString()

    @property
    def banner_routing_key(self):
        return 'Banner'

    def reset_cargo(self, data):
        self.cargo_obj.reset_config(data)
        self.cache_data.cargo = self.cargo_obj.data
        self.cache_response = self.cache_data.SerializeToString()

    @property
    def cargo_routing_key(self):
        return 'Cargo'

    @property
    def cargo_conf_inst(self):
        return self.cargo_obj

    def __str__(self):
        return self.cache_response
