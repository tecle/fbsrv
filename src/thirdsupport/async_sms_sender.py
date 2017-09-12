# coding:utf-8

import logging
from tornado.httpclient import AsyncHTTPClient as AsyncSender


def call_back_wrapper(call_back, *args):
    '''If response is ok, status is 0.'''
    def func(resp):
        if resp.error:
            logging.warning("Async http client error:%s" % resp.error)
            call_back(1, *args)
        else:
            body = resp.body
            logging.debug(body)
            #parse
            logging.info("Done.")
            call_back(0, *args)
    return func


def call_back_wrapper(call_back, *args):
    '''If response is ok, status is 0.'''
    def func(resp):
        call_back(resp, *args)
    return func


def async_send_sms(call_back, *args):
    logging.debug("begin send sms message.")
    client = AsyncSender()
    client.fetch("http://120.26.126.59:5000/login",
                 call_back_wrapper(call_back, *args))


def huanxin_async_request(call_back, huanxin_inst, cache, uid, pwd, nick, *args):
    '''at last, call call_back(response, *args)'''
    token = cache.get_huanxin_token()
    if not token:
        def parse_wrapper(resp):
            huanxin_inst.parse_token_response(resp)
            if huanxin_inst.token:
                logging.info('update huanxin token[%s] expires in %s'
                             % (huanxin_inst.token, huanxin_inst.token_alive_time))
                cache.set_huanxin_token(huanxin_inst.token, huanxin_inst.token_alive_time - 6 * 60 * 60)
                async_send_request(call_back, huanxin_inst.make_register_request(uid, pwd, nick), *args)
            else:
                logging.info('get huanxin token failed. will not register user[%s] to huanxin.' % uid)
                call_back(None, *args)
        client = AsyncSender()
        logging.info('Token out of date. Get new token.')
        client.fetch(huanxin_inst.make_token_request(), parse_wrapper)
    else:
        if not huanxin_inst.token:
            huanxin_inst.token = token
        async_send_request(call_back, huanxin_inst.make_register_request(uid, pwd, nick), *args)


def async_send_request(call_back, request, *args):
    logging.info("begin send request")
    client = AsyncSender()
    client.fetch(request, call_back_wrapper(call_back, *args))
