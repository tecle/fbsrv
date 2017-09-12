# coding: utf-8

import base64
import datetime
import json
import logging
import urllib

from Crypto.Hash import SHA256, SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5

from model.orders import PayOrder
from pay_api_base import PayAPiBase

trade_status = {
    'TRADE_FINISHED': 0,
    'TRADE_SUCCESS': 0,
    'WAIT_BUYER_PAY': 1,
    'TRADE_CLOSED': 2,
}

wap_pay_method = 'alipay.trade.wap.pay'
query_trade_method = 'alipay.trade.query'
close_trade_method = 'alipay.trade.close'
refund_trade_method = 'alipay.trade.refund'
refund_query_trade_method = 'alipay.trade.fastpay.refund.query'
pay_method = 'alipay.trade.app.pay'


class AliPayApi(PayAPiBase):
    PayType = 2

    def __init__(self, app_id, callback_url, private_key_file, public_key_file, gate_addr):
        super(AliPayApi, self).__init__()
        self.app_id = app_id
        self.callback_url = callback_url
        # 计算签名工具
        with open(private_key_file) as f:
            self.rsa_pri = RSA.importKey(f.read())
            self.signer = Signature_pkcs1_v1_5.new(self.rsa_pri)
        # 验证签名工具
        with open(public_key_file) as f:
            self.rsa_pub = RSA.importKey(f.read())
            self.verifier = Signature_pkcs1_v1_5.new(self.rsa_pub)
        self.gate_addr = gate_addr  # 支付宝服务器网关

    def get_pub_params(self, method, with_notify_url=True):
        res = {
            'app_id': self.app_id,
            'method': method,
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0'
        }
        if with_notify_url:
            res['notify_url'] = self.callback_url
        return res

    def get_pay_str(self, uid, subject, price, cargo_id, order_no):
        obj = {
            # 'body': '交易描述信息',
            'subject': subject,
            'out_trade_no': str(order_no),
            'total_amount': "%.2f" % (price / 100.0),
            'product_code': 'QUICK_WAP_WAY',  # 'QUICK_MSECURITY_PAY',
            'passback_params': self.construct_attach(uid, cargo_id),
        }
        logging.info('ali price:[{}]'.format(obj['total_amount']))
        biz_content = json.dumps(obj)
        params = self.get_pub_params(wap_pay_method)
        params['biz_content'] = biz_content
        params['sign'] = self.get_sign_str(params)
        pay_url = '&'.join(['%s=%s' % (key, urllib.quote(val)) for key, val in params.items()])
        return pay_url

    def _get_str_to_sign(self, param):
        keys = param.keys()
        keys.sort()
        return '&'.join(['%s=%s' % (key, param[key]) for key in keys if key])

    def get_sign_str(self, param, use_rsa2=True):
        hash_val = SHA256.new(self._get_str_to_sign(param)) if use_rsa2 else SHA.new(self._get_str_to_sign(param))
        return base64.b64encode(self.signer.sign(hash_val))

    def debug(self, str_to_sign, use_rsa2=True):
        hash_val = SHA256.new(str_to_sign) if use_rsa2 else SHA.new(str_to_sign)
        return base64.b64encode(self.signer.sign(hash_val))

    def verify_sign(self, param, sign, use_rsa2=True):
        hash_val = SHA256.new(self._get_str_to_sign(param)) if use_rsa2 else SHA.new(self._get_str_to_sign(param))
        return self.verifier.verify(hash_val, base64.b64decode(sign))

    def check_trade_success(self, status_code):
        return trade_status['TRADE_FINISHED'] == status_code

    def process_callback_msg(self, info):
        pay_order = PayOrder()
        pay_order.trade_status = trade_status.get(info['trade_status'], -1)
        pay_order.total_fee = int(float(info['total_amount']) * 100)
        pay_order.real_fee = int(float(info['receipt_amount']) * 100)
        pay_order.trade_no = info['trade_no']
        pay_order.order_no = info['out_trade_no']
        uid, cargo_id = self.parse_attach(info['passback_params'])
        pay_order.cargo_id = cargo_id
        pay_order.user_id = uid
        pay_order.pay_channel = self.PayType
        pay_order.app_id = info['app_id']
        return pay_order

    def make_query_request_body(self, order_no):
        params = self.get_pub_params(query_trade_method, False)
        params['biz_content'] = '{"out_trade_no": %s}' % order_no
        params['sign'] = self.get_sign_str(params)
        return '&'.join(['%s=%s' % (key, urllib.quote(val)) for key, val in params.items()])

    def process_query_response(self, resp):
        '''
        :param resp: response from AsyncHTTPClient
        :return: trade_no, trade_status, total_money
        '''
        if resp.error:
            logging.warning('bad response from Alipay:[%s]' % resp.body)
            return None, None
        obj = json.loads(resp.body, encoding='gbk')  # 支付宝的编码系统竟然是gbk, 不可思议
        query_res = obj['alipay_trade_query_response']
        if query_res['code'] != '10000':
            logging.warning('meet error when query Alipay:[%s]' % query_res['msg'])
            return None, None
        return query_res['trade_no'], trade_status.get(query_res['trade_status'], -1), int(
            float(query_res['total_amount']) * 100)

    @staticmethod
    def convert_trade_str_to_int(status_str):
        return trade_status.get(status_str, -1)
