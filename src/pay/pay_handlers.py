# coding: utf-8

import logging

import redis.exceptions as RedisException
import tornado.gen
import tornado.web
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest

from handlers.base_handler import KVBaseHandler
from model.pay_questions import PayQuestions
from model.table_base import Wanted
from model.cache import UserResCache
from model.orders import PayOrder
from model.response import PayOrderData, Status, HistoryOrders, DataShell
from pay.weixin import WeiXinApi
from pay.zhifubao import AliPayApi
from utils.common_define import HttpErrorStatus, ErrorCode

__all__ = ['OrderQueryHandler', 'AliPayCallbackHandler', 'WeinXinCallbackHandler']


def deliver_cargo_to_user(uid, cargo_id, cargo_config, money_cost, user_res_cache, order_no):
    logging.info('give cargo [%s] to user [%s], order no[%s].' % (cargo_id, uid, order_no))
    cargo_item = cargo_config[int(cargo_id)]
    if not cargo_item or cargo_item.price != money_cost:
        logging.warning('invalid cargo info:real cost[{}], expect[{}]'.format(
            money_cost, cargo_item.price if cargo_item else 'None'))
        return None
    try:
        cur_gold = user_res_cache.increment_gold(uid, cargo_item.total_amount)
    except RedisException.RedisError:
        logging.exception('give cargo [%s] to user [%s] failed.' % (cargo_item.id, uid))
        return None
    return cur_gold


class OrderQueryHandler(KVBaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        if not self.validate_request():
            self.finish()
            return
        # 根据交易编号查询订单
        uid = int(self.get_argument('uid'))
        order_no = self.get_argument('order')
        channel = self.get_argument('channel')
        counter = self.get_argument('counter')
        logging.info('order [{}] query count [{}]'.format(order_no, counter))
        # 1.从数据库查询,如果没有再向服务器查询
        db_order = PayOrder()
        db_order.order_no = order_no
        db_order.user_id = Wanted
        db_order.trade_status = Wanted
        db_order.cargo_id = Wanted
        db_order.real_fee = Wanted
        update_success = yield tornado.gen.Task(db_order.update_from_db)
        result = Status()
        result.success = False
        if update_success:
            if channel == 'T':
                weixin = self.application.wx_pay
                if weixin.check_trade_success(db_order.trade_status):
                    result.success = True
                else:
                    # 状态为未成功
                    req = HTTPRequest(
                        url=weixin.query_order_url,
                        method="POST",
                        body=weixin.make_query_request_body(order_no)
                    )
                    resp = yield AsyncHTTPClient().fetch(req, raise_error=False)
                    pay_info = weixin.process_query_response(resp)
                    # 查询到结果时,更新数据
                    if pay_info:
                        result.success = weixin.check_trade_success(pay_info.trade_status)
                        # 查询到结果时,更新数据
                        if result.success:
                            up = PayOrder()
                            up.order_no = order_no
                            up.trade_status = pay_info.trade_status
                            up.trade_no = pay_info.trade_no
                            up.update_to_db()
                            # 支付成功, 执行逻辑
                            self.process_pay_success(uid, db_order.cargo_id, order_no, pay_info.total_fee)
            elif channel == 'A':
                # 支付宝支付要求订单一定要先存在于db中
                if db_order:
                    alipay = self.application.ali_pay
                    if alipay.check_trade_success(db_order.trade_status):
                        result.success = True
                    else:
                        # 状态为未成功时查询服务器
                        req = HTTPRequest(
                            url=alipay.gate_addr,
                            method="POST",
                            body=alipay.make_query_request_body(order_no)
                        )
                        resp = yield AsyncHTTPClient().fetch(req, raise_error=False)
                        logging.debug(resp.body)
                        t_no, trade_status, money = alipay.process_query_response(resp)
                        result.success = alipay.check_trade_success(trade_status)
                        # 查询到结果时,更新数据
                        if result.success:
                            up = PayOrder()
                            up.order_no = order_no
                            up.trade_status = trade_status
                            up.trade_no = t_no
                            up.update_to_db()
                            # 支付成功, 执行逻辑
                            self.process_pay_success(uid, db_order.cargo_id, order_no, money)
                else:
                    logging.warning('order[%s] not exist.', order_no)
                    result.code = ErrorCode.NotExist
                    result.success = False
        else:
            result.code = ErrorCode.NotExist
            result.success = False
        self.write_response(result)
        self.finish()

    def process_pay_success(self, uid, cargo_id, order_no, amount):
        cur_gold = deliver_cargo_to_user(
            uid, cargo_id, self.application.cargo_conf, amount,
            self.application.redis_wrapper.get_cache(UserResCache.cache_name), order_no)
        if cur_gold is not None:
            self.application.growth_system.recharge(uid, amount)
            return True
        return False

    def save_order(self, db_order, new_order, order_success):
        if order_success:
            if db_order:
                logging.debug('update to db')
                # 数据库中有数据, 更新状态 trade_no 和 trade_status
                u_order = PayOrder(order_no=new_order.order_no, trade_no=new_order.trade_no,
                                   trade_status=new_order.trade_status)
                return u_order.update_to_db
            else:
                logging.debug('save to db')
                # 数据库没数据, 添加记录
                return new_order.save


class AliPayCallbackHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        logging.debug('receive alipay message:[%s]' % self.request.body)
        params = {k: v[0] for k, v in self.request.body_arguments.items()}
        sign_type = params.pop('sign_type')
        sign = params.pop('sign')
        use_rsa2 = sign_type == 'RSA2'
        if not self.application.ali_pay.verify_sign(params, sign, use_rsa2):
            logging.warning('received invalid notify message: wrong sign.[%s]' % self.request.body)
            self.write('fail')
            return
        order_info = self.application.ali_pay.process_callback_msg(params)
        # 支付宝订单在创建支付链接的时候就把信息存到数据库里面了
        db_order = yield tornado.gen.Task(PayOrder.get_one, order_info.order_no)
        if db_order:
            new_order = PayOrder()
            new_order.order_no = db_order.order_no
            new_order.trade_no = order_info.trade_no
            # 订单存在,交易状态不一致, 且最新状态为支付成功, 更新状态, 完成交易最终流程
            if self.application.ali_pay.check_trade_success(order_info.trade_status) \
                    and db_order.trade_status != order_info.trade_status:
                new_order.trade_status = order_info.trade_status
                cur_gold = deliver_cargo_to_user(
                    db_order.user_id, db_order.cargo_id, self.application.cargo_conf, order_info.total_fee,
                    self.application.redis_wrapper.get_cache(UserResCache.cache_name), db_order.order_no)
                if cur_gold is not None:
                    self.application.growth_system.recharge(db_order.user_id, db_order.real_fee)
            new_order.update_to_db()
        else:
            logging.warning('cannot get order info with order no[%s] from database.' % order_info.order_no)
        self.write('success')


class WeinXinCallbackHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        logging.debug('receive weixin message:[%s]' % self.request.body)
        pay_order = self.application.wx_pay.process_callback_msg(self.request.body)
        if pay_order:
            # 数据库查询,查看是否已经写入
            db_order = yield tornado.gen.Task(PayOrder.get_one, pay_order.order_no)
            if db_order:
                # 数据库中的状态和当前状态不一致,且当前状态为支付成功, 更新数据库
                if self.application.wx_pay.check_trade_success(pay_order.trade_status) \
                        and db_order.trade_status != pay_order.trade_status:
                    new_order = PayOrder()
                    new_order.order_no = pay_order.order_no
                    new_order.trade_status = pay_order.trade_status
                    new_order.update_to_db()
                    self.application.growth_system.recharge(pay_order.user_id, pay_order.real_fee)
                    deliver_cargo_to_user(db_order.user_id, db_order.cargo_id, self.application.cargo_conf,
                                          pay_order.total_fee,
                                          self.application.redis_wrapper.get_cache(UserResCache.cache_name),
                                          db_order.order_no)
            else:
                # 数据库无记录, 写入数据库
                if self.application.wx_pay.check_trade_success(pay_order.trade_status):
                    self.application.growth_system.recharge(pay_order.user_id, pay_order.real_fee)
                    deliver_cargo_to_user(db_order.user_id, db_order.cargo_id, self.application.cargo_conf,
                                          pay_order.total_fee,
                                          self.application.redis_wrapper.get_cache(UserResCache.cache_name),
                                          db_order.order_no)
                # 存到数据库
                pay_order.save()
            self.write(self.get_return_msg())
        else:
            self.write(self.get_return_msg(False))

    @staticmethod
    def get_return_msg(success=True):
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>' \
            if success else \
            '<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[BADRESPONSE]]></return_msg></xml>'


class PayHandler(KVBaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        if not self.validate_request():
            self.finish()
            return
        op_type = self.get_argument('op', 'A')
        uid = self.get_argument('uid')
        cargo_id = int(self.get_argument('cargo_id'))
        cargo_num = int(self.get_argument('num', 1))
        ver = int(self.get_argument('ver'))
        if self.application.cargo_conf.validate_version(ver):
            # 获取商品信息
            cargo_item = self.application.cargo_conf[cargo_id]
            if cargo_item:
                logging.info('bill:uid[{}],op[{}],cargo[{}],num[{}]'.format(uid, op_type, cargo_id, cargo_num))
                # 先生成订单
                if op_type == 'T':
                    yield self.process_wx_order(uid, cargo_item, cargo_num)
                elif op_type == 'A':
                    yield self.process_ali_order(uid, cargo_item, cargo_num)
            else:
                logging.warning('cargo with id[%s] not set in config files.' % cargo_id)
                self.set_status(*HttpErrorStatus.WrongParams)
                self.order_fail(ErrorCode.NotExist)
        else:
            logging.info('version %s not matched.', ver)
            self.order_fail(ErrorCode.OldVersion)
        self.finish()

    def order_fail(self, err_code):
        ds = DataShell()
        ds.success = False
        ds.errCode = err_code
        self.write_response(ds)

    @tornado.gen.coroutine
    def process_ali_order(self, uid, cargo_item, cargo_num):
        alipay = self.application.ali_pay
        pay_order = PayOrder(app_id=alipay.app_id, pay_channel=AliPayApi.PayType,
                             total_fee=cargo_item.price, real_fee=cargo_item.actual_price * cargo_num,
                             cargo_des=cargo_item.des, cargo_id=cargo_item.id, user_id=uid)
        order_no = yield tornado.gen.Task(pay_order.save)
        if order_no:
            param_str = alipay.get_pay_str(
                uid, cargo_item.des, cargo_item.actual_price * cargo_num, cargo_item.id, str(order_no))
            pay_order = PayOrderData()
            pay_order.order_no = order_no
            pay_order.pay_str = param_str
            self.application.secure_tools.secure_dict(pay_order)
            self.write_response(pay_order)
        else:
            self.set_status(*HttpErrorStatus.InsertToDbError)

    @tornado.gen.coroutine
    def process_wx_order(self, uid, cargo_item, cargo_num):
        weixin = self.application.wx_pay
        pay_order = PayOrder(app_id=weixin.app_id, pay_channel=WeiXinApi.PayType,
                             total_fee=cargo_item.price, real_fee=cargo_item.actual_price * cargo_num,
                             cargo_des=cargo_item.des, cargo_id=cargo_item.id, user_id=uid)
        order_no = yield tornado.gen.Task(pay_order.save)

        uip = self.get_argument('uip')
        # 获取预支付ID
        req = HTTPRequest(
            url=weixin.place_order_url,
            method='POST',
            body=weixin.make_order_request_body(
                uid, cargo_item.des, uip, cargo_item.id, cargo_item.actual_price * cargo_num, order_no)
        )
        resp = yield AsyncHTTPClient().fetch(req, raise_error=False)
        res = weixin.process_order_response(resp)
        if not res:
            self.set_status(*HttpErrorStatus.SystemError)
            return
        po = PayOrderData()
        po.order_no = order_no
        po.pay_str = res
        self.application.secure_tools.secure_dict(po)
        # 算签名并返回
        self.write_response(po)


class ConsultationHandler(KVBaseHandler):
    def do_post(self):
        uid = self.get_argument('uid')
        op = self.get_argument('op')
        Status()
        if op == 'A':
            # 增加一条咨询信息
            detail = self.get_argument('text')
            pq = PayQuestions(uid=uid, detail=detail)
            pid = yield tornado.gen.Task(pq.save)
            if pid > 0:
                self.write('{"st":"OK", "qid":%d}' % pid)
            else:
                self.set_status(*HttpErrorStatus.SystemError)
        elif op == 'Q':
            # 查询结果
            qid = self.get_argument('qid')
            question = yield tornado.gen.Task(PayQuestions.get_one(qid))
            if not question:
                logging.warning('user [%s] does not exist question[%s]' % (uid, qid))


class OrdersHandler(KVBaseHandler):
    def do_post(self, *args):
        uid = self.current_user
        part = self.get_argument('part')
        page_size = 20
        offset = page_size * part
        success_trade_status = 0

        PayOrder.get_orders(uid, offset, page_size, success_trade_status, callback=self.on_finish_get_orders)

    def on_finish_get_orders(self, orders):
        result = HistoryOrders()
        if orders is not None:
            result.orders = orders
        else:
            result.success = False
            result.errCode = ErrorCode.DatabaseError
        self.write_response(result)
        self.finish()
