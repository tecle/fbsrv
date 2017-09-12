# coding:utf-8

import unittest
from pay.weixin import WeiXinApi


class WeiXinTest(unittest.TestCase):

    def setUp(self):
        self.query_response = '''<xml>
   <return_code><![CDATA[SUCCESS]]></return_code>
   <return_msg><![CDATA[OK]]></return_msg>
   <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
   <mch_id><![CDATA[10000100]]></mch_id>
   <device_info><![CDATA[1000]]></device_info>
   <nonce_str><![CDATA[TN55wO9Pba5yENl8]]></nonce_str>
   <sign><![CDATA[BDF0099C15FF7BC6B1585FBB110AB635]]></sign>
   <result_code><![CDATA[SUCCESS]]></result_code>
   <openid><![CDATA[oUpF8uN95-Ptaags6E_roPHg7AG0]]></openid>
   <is_subscribe><![CDATA[Y]]></is_subscribe>
   <trade_type><![CDATA[MICROPAY]]></trade_type>
   <bank_type><![CDATA[CCB_DEBIT]]></bank_type>
   <total_fee>1</total_fee>
   <cash_fee>1</cash_fee>
   <fee_type><![CDATA[CNY]]></fee_type>
   <transaction_id><![CDATA[1008450740201411110005820873]]></transaction_id>
   <out_trade_no><![CDATA[1415757673]]></out_trade_no>
   <attach><![CDATA[订单额外描述]]></attach>
   <time_end><![CDATA[20141111170043]]></time_end>
   <trade_state><![CDATA[SUCCESS]]></trade_state>
</xml>'''
        self.order_response = '''<xml>
   <return_code><![CDATA[SUCCESS]]></return_code>
   <return_msg><![CDATA[OK]]></return_msg>
   <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
   <mch_id><![CDATA[10000100]]></mch_id>
   <nonce_str><![CDATA[IITRi8Iabbblz1Jc]]></nonce_str>
   <openid><![CDATA[oUpF8uMuAJO_M2pxb1Q9zNjWeS6o]]></openid>
   <sign><![CDATA[7921E432F65EB8ED0CE9755F0E86D72F]]></sign>
   <result_code><![CDATA[SUCCESS]]></result_code>
   <prepay_id><![CDATA[wx201411101639507cbf6ffd8b0779950874]]></prepay_id>
   <trade_type><![CDATA[JSAPI]]></trade_type>
</xml>
        '''

    def test_sign(self):
        api = WeiXinApi()
        api.secret = '192006250b4c09247ec02edce69f6a2d'
        kv = {
            'appid': 'wxd930ea5d5a258f4f',
            'mch_id': '10000100',
            'device_info': 1000,
            'body': 'test',
            'nonce_str': 'ibuaiVcKdpRxkhJA'
        }
        api.add_sign(kv)
        self.assertEqual('9A0A8659F005D6984697E2CA0A9CF3B7', kv['sign'])

    def test_to_xml(self):
        kv = {
            'a': 'http://s',
            'b': 'sss'
        }
        self.assertEqual('<xml><a>http://s</a><b>sss</b></xml>', WeiXinApi.to_xml(kv))

    def test_parse_xml_to_dict(self):
        res = WeiXinApi.parse_xml_to_dict(self.query_response)
        self.assertEqual('SUCCESS', res['return_code'])
        self.assertEqual('1008450740201411110005820873', res['transaction_id'])

    def test_process_query_response_success(self):
        api = WeiXinApi()
        obj = api.process_query_response(self.query_response)
        self.assertEqual('wx2421b1c4370ec43b', obj.app_id)
        self.assertEqual('订单额外描述', obj.cargo_id)
