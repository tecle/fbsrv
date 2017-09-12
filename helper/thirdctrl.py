# coding: utf-8

from __future__ import absolute_import

import json
import random
import time
import traceback
import urllib

import tornado.ioloop
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPRequest

from model.cache.cache_define import RedisStr
from .hplcore import gen_prompt, get_async_im, get_db_conn, get_redis_inst, get_qiniu_api

import_info = '第三方操作集合'


@gen_prompt("转换用户头像和照片墙数据", '3RD')
def convert_user_img():
    conn = get_db_conn()
    pk = 'user_id'
    target_filed = ['avatar']
    table = 'user_info_new'
    start = 0
    size = 100
    qn = get_qiniu_api()
    conn.update('start transaction')
    try:
        while True:
            print "process {}, {}".format(start, size)
            ret = conn.query(
                'select {}, {}, show_pics from {} limit {}, {}'.format(pk, ','.join(target_filed), table, start, size))
            if not ret:
                break
            for item in ret:
                for tar in target_filed:
                    if not item[tar].startswith('http'):
                        print conn.update(
                            'update {} set {}="{}" where {}={}'.format(
                                table, tar, qn.get_pub_url(item[tar]), pk, item[pk]))
                    show_pics = 'show_pics'
                    print conn.update(
                        'update {} set {}=%s where {}={}'.format(
                            table, show_pics, pk, item[pk]), ','.join(qn.get_pub_urls(item[show_pics])))
            start += size
    except:
        traceback.print_exc()
        conn.update('rollback')
    else:
        conn.update('commit')


@gen_prompt("转换动态图片", '3RD')
def convert_active_img():
    conn = get_db_conn()
    pk = 'id'
    target_fileds = ['pics']
    table = 'actives'
    start = 0
    size = 100
    qn = get_qiniu_api()
    conn.update('start transaction')
    try:
        while True:
            print "process {}, {}".format(start, size)
            ret = conn.query(
                'select {}, {} from {} limit {}, {}'.format(pk, ','.join(target_fileds), table, start, size))
            if not ret:
                break
            for item in ret:
                for col in target_fileds:
                    if not item[col].startswith('http'):
                        print conn.update(
                            'update {} set {}=%s where {}={}'.format(
                                table, col, pk, item[pk]), ','.join(qn.get_pub_urls(item[col])))
            start += size
    except:
        traceback.print_exc()
        conn.update('rollback')
    else:
        conn.update('commit')


@gen_prompt("创建superfanyu帐号", '3RD')
def create_super_fanyu():
    uid = raw_input('super user account id:')
    async_im = get_async_im()
    request = HTTPRequest(async_im.create_user_url, body=urllib.urlencode(
        {
            "accid": uid,
            "name": "1-{}".format('系统'),
        }
    ), headers=async_im.make_header(), method='POST')
    client = HTTPClient()
    response = client.fetch(request)
    client.close()
    print response.body


@gen_prompt('获取用户聊天名片', '3RD')
def user_yunxin_card():
    uid = raw_input('用户ID:')
    try:
        async_im = get_async_im()
        body = 'accids=["{}"]'.format(uid)
        _helper(async_im, async_im.get_user_info_url, body)
    except Exception, e:
        print 'meet except:[{}]'.format(e)


@gen_prompt('*创建用户到云信', '3RD')
def sync_user_to_yunxin():
    uids = raw_input('用户ID列表(逗号分割):')
    uid_ary = uids.split(',')
    db = get_db_conn()
    async_im = get_async_im()
    client = HTTPClient()
    r = get_redis_inst()
    for uid in uid_ary:
        try:
            q = 'select avatar, nick_name, signature from user_info_new where user_id={}'.format(uid)
            print q
            usr = db.get(q)
            if not usr:
                usr = {
                    'avatar': 'testbucket:666.jpg',
                    'nick_name': 'Money',
                    'signature': 'shut up and show your money'
                }
            usr_at = get_qiniu_api().get_pub_url(usr['avatar'])
            print usr_at
            request = HTTPRequest(async_im.create_user_url, body=urllib.urlencode(
                {
                    "accid": uid,
                    "name": "1-{}".format(usr['nick_name']),
                }
            ), headers=async_im.make_header(), method='POST')
            response = client.fetch(request)
            if response.error:
                print "add user error:[{}]".format(response)
            else:
                print "add user result:[{}]".format(response.body)
                obj = json.loads(response.body)
                if obj['code'] != 414:
                    token = obj['info']['token']
                    r.hset(RedisStr.UserHKeyPtn % uid, RedisStr.YunxinTokenField, token)

            request = HTTPRequest(async_im.update_user_card_url, body=urllib.urlencode(
                {
                    "accid": uid,
                    "icon": usr_at,
                    "sign": usr['signature']
                }
            ), headers=async_im.make_header(), method='POST')
            response = client.fetch(request)
            if response.error:
                print "update error:[{}]".format(response)
            else:
                print "update result:[{}]".format(response.body)
        except Exception, e:
            traceback.print_exc()
            print 'meet except:[{}]'.format(e)


@gen_prompt('Pay-获取支付宝签名', '3RD')
def reset_server_data():
    from pay.zhifubao import AliPayApi
    s = raw_input('签名串:')
    prv_file = raw_input('私钥文件:')
    if not prv_file:
        prv_file = '/home/licheng/workspace/fanyu_git/chat-server/server-config/app_prv_key.pem'
    pub_file = raw_input('公钥文件:')
    if not pub_file:
        pub_file = '/home/licheng/workspace/fanyu_git/chat-server/server-config/zhifubao_pub_key.pem'
    ap = AliPayApi('123', 'www.baidu.com', prv_file, pub_file, 'funbox.daily2fun.com')
    print ap.debug(s)


@gen_prompt('Pay-获取支付宝支付链接', '3RD')
def reset_server_data():
    from pay.zhifubao import AliPayApi
    prv_file = raw_input('私钥文件:')
    if not prv_file:
        prv_file = 'helper/prv.pem'
    pub_file = raw_input('公钥文件:')
    if not pub_file:
        pub_file = 'helper/pub.pem'
    # gate = 'https://openapi.alipaydev.com/gateway.do'
    gate = 'https://openapi.alipay.com/gateway.do'
    ap = AliPayApi('2017072607909006', 'http://funbox.daily2fun.com/pay/cb/zfb', prv_file, pub_file, gate)
    order_id = str(int(time.time() * 1000))
    print '?'.join([gate, ap.get_pay_str('111', 'test pay', 1, 123, order_id)])


@gen_prompt('云信用户名片测试', '3RD')
def user_yunxin_card():
    uid = raw_input('用户ID:')
    try:
        async_im = get_async_im()
        import sys
        import time
        cb = lambda resp: sys.stdout.write('%s\n' % resp)

        def cb4(resp):
            print resp
            async_im.get_user_info(uid, cb)

        def cb3(resp):
            print resp
            async_im.update_user_card(uid, level=1, nick_name='%s' % random.randint(1000, 9999), callback=cb4)

        def cb2(resp):
            print resp
            async_im.get_user_info(uid, cb3)

        def cb1(resp):
            print resp
            async_im.update_user_card(uid, sign=random.randint(1000, 9999), callback=cb2)

        async_im.get_user_info(uid, cb1)

        io = tornado.ioloop.IOLoop.current()
        io.add_timeout(time.time() + 3, lambda: io.stop())
        io.start()

    except Exception, e:
        print 'meet except:[{}]'.format(e)


def _helper(async_im, url, body):
    headers = async_im.make_header()
    request = HTTPRequest(url, body=body, headers=headers, method='POST')
    import datetime
    print '%s,请求信息:\nurl:%s\nbody:%s\nheaders:%s' % (
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), url,
        body, ','.join(['{}:{}'.format(k, v) for k, v in headers]))
    response = HTTPClient().fetch(request)
    if response.error:
        print "GET error:[{}]".format(response)
    else:
        print "GET result:[{}]".format(response.body)
