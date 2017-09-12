# coding: utf-8

import hashlib
import logging
from xml.etree import ElementTree

from model.orders import PayOrder
from pay_api_base import PayAPiBase
from utils.util_tools import generate_nonce_str


class WeiXinApi(PayAPiBase):
    PayType = 1
    TradeStateInfo = {
        'SUCCESS': 0,  # 支付成功
        'REFUND': 1,  # 转入退款
        'NOTPAY': 2,  # 未支付
        'CLOSED': 3,  # 已关闭
        'REVOKED': 4,  # 已撤销
        'USERPAYING': 5,  # 用户支付中
        'PAYERROR': 6,  # 支付失败, 如银行返回失败
    }

    ReturnCodeInfo = {
        'SUCCESS': True,
        'FAIL': False
    }

    def __init__(self, app_id, secret, mch_id, api_addr, callback_url):
        super(WeiXinApi, self).__init__()
        self.app_id = app_id
        self.secret = secret
        self.place_order_url = api_addr + '/pay/unifiedorder'
        self.query_order_url = api_addr + '/pay/orderquery'
        self.mch_id = mch_id
        self.callback_url = callback_url

    def get_sign_str(self, kv):
        keys = kv.keys()
        keys.sort()
        str_to_sign = '%s&key=%s' % ('&'.join(['%s=%s' % (key, kv[key]) for key in keys if key]), self.secret)
        m = hashlib.md5()
        m.update(str_to_sign.encode('utf-8'))
        return m.hexdigest().upper()

    @staticmethod
    def to_xml(kv):
        return '<xml>%s</xml>' % ''.join(['<%s>%s</%s>' % (key, val, key) for key, val in kv.items()])

    def make_order_request_body(self, uid, body, user_ip, cargo_id, cargo_cost, order_no):
        '''
        :param body: 支付提示信息
        :param cargo_id: 货物
        :param cargo_cost:
        :return:
        '''
        kv = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': generate_nonce_str(16),
            'body': body,
            'attach': self.construct_attach(uid, cargo_id),
            'out_trade_no': order_no,
            'total_fee': cargo_cost,
            'spbill_create_ip': user_ip,
            'notify_url': self.callback_url,
            'trade_type': 'APP'
        }
        kv['sign'] = self.get_sign_str(kv)
        return self.to_xml(kv)

    def make_query_request_body(self, order_id):
        kv = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'out_trade_no': order_id,
            'nonce_str': generate_nonce_str(16)
        }
        kv['sign'] = self.get_sign_str(kv)
        return self.to_xml(kv)

    @staticmethod
    def parse_xml_to_dict(xml_str):
        root = ElementTree.fromstring(xml_str)
        res = {}
        for child in root.getchildren():
            res[child.tag] = child.text.encode('utf-8')  # tips:一定要转码, 否则会出现中文签名计算问题
        return res

    def check_response(self, kv):
        sign = kv.pop('sign', '')
        if len(sign) != 32:
            return False
        kv['sign'] = self.get_sign_str(kv)
        return kv['sign'] != sign

    def is_success_response(self, info):
        if not self.check_response(info):
            logging.warning('receive fake response from weixin server.')
            return False
        if not self.ReturnCodeInfo.get(info['return_code'], False):
            logging.warning('got bad msg from weixin by query request:%s' % info['return_msg'])
            # 签名不通过等错误
            return False
        if not self.ReturnCodeInfo.get(info['result_code'], False):
            # 订单不存在(err_code=ORDERNOTEXIST),或者系统错误(err_code=SYSTEMERROR), 需要重试
            logging.warning('got bad biz response:[%s]' % info['err_code_des'])
            return False
        return True

    def get_pay_order_from_dict(self, info):
        pay_order = PayOrder()
        pay_order.total_fee = int(info['total_fee'])
        pay_order.real_fee = pay_order.total_fee
        pay_order.trade_no = info['transaction_id']
        pay_order.order_no = info['out_trade_no']
        uid, cid = self.parse_attach(info['attach'])
        pay_order.cargo_id = cid
        pay_order.user_id = uid
        pay_order.pay_channel = self.PayType
        pay_order.app_id = info['appid']
        return pay_order

    def process_query_response(self, resp):
        if resp.error:
            logging.warning('receive bad response from weixin:[%s]' % resp.body)
            return None
        info = self.parse_xml_to_dict(resp.body)
        if not self.is_success_response(info):
            return None
        pay_order = self.get_pay_order_from_dict(info)
        pay_order.trade_status = self.TradeStateInfo.get(info['trade_state'], -1)
        return pay_order

    def process_callback_msg(self, msg):
        info = self.parse_xml_to_dict(msg)
        if not self.is_success_response(info):
            return None
        pay_order = self.get_pay_order_from_dict(info)
        pay_order.trade_status = self.TradeStateInfo['SUCCESS']
        return pay_order

    def process_order_response(self, resp):
        if resp.error:
            logging.warning('receive bad response from weixin:[%s]' % resp.body)
            return None
        info = self.parse_xml_to_dict(resp.body)
        if not self.is_success_response(info):
            logging.warning('receive failed response from weixin:[%s]' % resp.body)
            return None
        return info['prepay_id']

    def check_trade_success(self, status_code):
        return self.TradeStateInfo['SUCCESS'] == status_code

    @classmethod
    def convert_status_str_to_int(cls, s):
        return cls.TradeStateInfo.get(s, -1)
