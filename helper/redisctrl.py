# coding: utf-8

from __future__ import absolute_import

import json

from model.cache.cache_define import RedisStr
from .hplcore import gen_prompt, get_redis_inst, get_db_conn

import_info = "Redis操作集合"


@gen_prompt('*修改用户金钱', 'Redis')
def modify_some_user_money():
    if raw_input('用户类型: \n1.范围用户\n2.单个用户') == '1':
        s = raw_input('用户ID(起始ID-结束ID):')
        start, end = [int(item) for item in s.split('-')]
        amount = int(raw_input('金币数量:'))
        r = get_redis_inst()
        p = r.pipeline()
        for uid in range(start, end + 1):
            p.zincrby(RedisStr.UserTotalFortuneZKey, uid, amount)
        print p.execute()
    else:
        uid = int(raw_input('用户ID:'))
        amount = int(raw_input('金币数量:'))
        r = get_redis_inst()
        p = r.pipeline()
        p.zincrby(RedisStr.UserTotalFortuneZKey, uid, amount)
        print p.execute()


@gen_prompt('查看用户金钱', 'Redis')
def modify_user_money():
    uid = int(raw_input('用户ID:'))
    r = get_redis_inst()
    p = r.pipeline()
    p.zscore(RedisStr.UserTotalFortuneZKey, uid)
    print p.execute()


@gen_prompt('修改库存值', 'Redis')
def modify_user_money():
    uid = int(raw_input('主播ID:'))
    r = get_redis_inst()
    print("当前库存值:%s" % r.hget(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveGameStorageField))
    incr = int(raw_input('库存增量:'))
    print("修改结果:%s" % r.hincrby(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveGameStorageField, incr))


@gen_prompt('查看用户缓存', 'Redis')
def lookup_user_redis_info():
    uid = int(raw_input('用户ID:'))
    r = get_redis_inst()
    p = r.pipeline()
    p.hgetall(RedisStr.UserHKeyPtn % uid)
    p.hgetall(RedisStr.LiveHKeyPtn % uid)
    p.zscore(RedisStr.UserTotalFortuneZKey, uid)
    res = p.execute()
    print '用户基本信息缓存:'
    print json.dumps(res[0], ensure_ascii=False, indent=2)
    print '用户直播信息缓存:'
    print json.dumps(res[1], ensure_ascii=False, indent=2)
    print '当前金钱总和:'
    print res[2]


@gen_prompt('直播列表', 'Redis')
def show_current_living_list():
    r = get_redis_inst()
    res = list(r.smembers(RedisStr.LivingListSKey))
    p = r.pipeline()
    for uid in res:
        p.hmget(RedisStr.LiveHKeyPtn % uid, (RedisStr.LiveChannelIdField, RedisStr.LiveCurrentViewNumField))
    ret = p.execute()
    print '直播列表:'
    print '\n'.join(['{}:{}:{}'.format(res[i], ret[i][0], ret[i][1]) for i in range(len(res))])


@gen_prompt('查看所有主播', 'Redis')
def show_current_living_list():
    r = get_redis_inst()
    print r.smembers(RedisStr.HostsSKey)


@gen_prompt('*清除直播信息', 'Redis')
def clear_live_infomation():
    uid = int(raw_input('用户ID:'))
    clear_room = raw_input('清除直播间ID(y/n):') == 'y'
    r = get_redis_inst()
    vals = {
        RedisStr.LivePushUrlField: '',
        RedisStr.LiveHlsPullUrlField: '',
        RedisStr.LiveHttpPullUrlField: '',
        RedisStr.LiveRtmpPullUrlField: ''
    }
    if clear_room:
        vals[RedisStr.LiveChatRoomField] = ''
    r.hmset(RedisStr.LiveHKeyPtn % uid, vals)
    print '清除完毕'


@gen_prompt('*添加用户到直播列表', 'Redis')
def add_user_to_live_list():
    uid = int(raw_input('用户ID:'))
    r = get_redis_inst()
    print '添加结果:{0}'.format(r.sadd(RedisStr.LivingListSKey, uid))
    show_current_living_list()


@gen_prompt('动态位置', 'Redis')
def add_user_to_live_list():
    active_id = int(raw_input('动态ID:'))
    r = get_redis_inst()
    print r.execute_command('GEOPOS', RedisStr.ActivesLocationGKey, active_id)


@gen_prompt('用户位置', 'Redis')
def add_user_to_live_list():
    uid = int(raw_input('用户ID:'))
    r = get_redis_inst()
    print r.execute_command('GEOPOS', RedisStr.UsersLocationGKey, uid)


@gen_prompt('查看所有兴趣', 'Redis')
def get_all_hobbies():
    r = get_redis_inst()
    hbs = list(r.smembers(RedisStr.HobbySKey))
    hbs.sort(key=lambda k: int(k[:k.find(':')]))
    for item in hbs:
        print item


@gen_prompt('*删除兴趣', 'Redis')
def rm_hobby():
    r = get_redis_inst()
    print "当前兴趣列表"
    items = r.smembers(RedisStr.HobbySKey)
    for i, item in enumerate(items):
        print "{} -> {}".format(i, item)
    idx = int(raw_input('输入要删除的兴趣索引:'))
    r.srem(RedisStr.HobbySKey, items[idx])
    print "OK"


@gen_prompt('*删除所有兴趣', 'Redis')
def rm_all_hobby():
    r = get_redis_inst()
    r.delete(RedisStr.HobbySKey)
    print r.smembers(RedisStr.HobbySKey)


@gen_prompt('*批量添加兴趣，使用空格分割', 'Redis')
def add_hobbies():
    hbs = raw_input("兴趣(使用空格分割):")
    hb_list = hbs.strip().split(' ')
    r = get_redis_inst()
    for i, hb in enumerate(hb_list):
        r.sadd(RedisStr.HobbySKey, '{}:{}'.format(i + 1, hb))
    get_all_hobbies()


@gen_prompt('*删除话题下的所有动态', 'Redis')
def rm_all_actives():
    r = get_redis_inst()
    r.delete(RedisStr.ActivesLocationGKey)
    print 'delete active location data finish'
    for i in xrange(1, 12):
        r.delete(RedisStr.FreshActiveIdLKeyPtn % i)
        r.delete(RedisStr.TopicHKeyPattern % i)
        print 'delete actives in topic[{}] finish.'.format(i)


@gen_prompt('*执行redis命令', 'Redis')
def execute_redis_cmd():
    cmd = raw_input('redis 命令:')
    r = get_redis_inst()
    print r.execute_command(cmd)


@gen_prompt('*修改评论数', 'Redis')
def set_comment_number():
    aid = raw_input('Active ID:')
    incr = raw_input('Incr:')
    r = get_redis_inst()
    print r.zincrby(RedisStr.ActiveCommentNumZKey, aid, incr)


@gen_prompt('**重置服务器信息', 'Redis')
def reset_server_data():
    r = get_redis_inst()
    print r.flushdb()
    tables = ('user_info_new', 'auth_phone')
    conn = get_db_conn()
    for table in tables:
        conn.update('delete from {}'.format(table))


@gen_prompt('*清除用户', 'Redis')
def clear_user():
    uid = int(raw_input('用户ID：'))
    phone = "86:" + raw_input('用户手机号:')
    tables = ('auth_phone', 'auth_weixin')
    conn = get_db_conn()
    conn.update('start transaction')
    try:
        conn.update('delete from user_info_new where user_id=%s', uid)
        for table in tables:
            print "delete from mysql:", conn.update('delete from {} where user_id=%s'.format(table), uid)
        r = get_redis_inst()
        print "delete from redis:", r.delete(RedisStr.UserHKeyPtn % uid)
        print "delete phone:", r.delete(phone)
    except Exception:
        conn.update('rollback')
        raise
    else:
        print conn.update('commit')


@gen_prompt('获取魅力值排行榜前20', 'Redis')
def modify_some_user_money():
    r = get_redis_inst()
    print r.zrange(RedisStr.UserCharmZKey, 0, 19, desc=True, withscores=True)
