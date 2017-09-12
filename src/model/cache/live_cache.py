# coding: utf-8

import json
import logging
import time
import model.messgemodel as MsgModel

from cache_define import RedisStr
from cache_wrapper import ExtendedCache
from model.cache.cache_tools import atoi
from utils.subscriber import make_pub_message

__all__ = [
    'LiveCache'
]

# 获取直播详情
# 1. 从当前直播列表中随机获取10个主播
# 2. 遍历每个主播ID:
# 3. 获取主播的基本信息
# 4. 获取主播的直播信息
# 5. 获取魅力值
# 6. 获取财富值
lua_for_live_meta = '''local result={}
local id_list = redis.call("SRANDMEMBER", KEYS[1], 10)
for i=1, #id_list do
    result[i] = {}
    local live_info = redis.call("HMGET", KEYS[2]..id_list[i], ARGV[1], ARGV[2], ARGV[3], ARGV[4], ARGV[5])
    table.insert(live_info, id_list[i])
    result[i][1] = live_info
    result[i][2] = redis.call("HMGET", KEYS[3]..live_info[1], ARGV[6], ARGV[7], ARGV[8], ARGV[9])
    result[i][3] = redis.call("ZSCORE", KEYS[4], live_info[1])
    result[i][4] = redis.call("ZSCORE", KEYS[5], live_info[1])
end
return result
'''

# 获取当前直播的时间戳信息
# 1.获取正在直播的id列表
# 2.获取各个直播记录的时间戳信息
# 3.移除过期的记录
lua_for_live_hb_data = '''
local result = {}
local id_list = redis.call("SMEMBERS", KEYS[1])
for i=1, #id_list do
    table.insert(result, {id_list[i], redis.call("HGET", KEYS[2]..id_list[i], ARGV[1])})
end
return result
'''

# 获取直播当前快照数据逻辑
# 1.从当前直播间的展示用户ID列表中获取等级最高的前几位用户
# 2.遍历获取到的用户,从用户信息表中取得其头像,等级信息
# 3.从直播信息表中获取当前观看人数
# 4.从用户魅力值列表中获取当前主播的魅力值
lua_for_live_snapshot = '''
local result = {}
local id_list = redis.call("ZREVRANGE", KEYS[1], 0, ARGV[1])
for i=1, #id_list do
    local user_info = redis.call("HMGET", KEYS[2]..id_list[i], ARGV[2], ARGV[3])
    table.insert(user_info, id_list[i])
    table.insert(result, user_info)
end
local live_info = {redis.call("HGET", KEYS[3], ARGV[4]), redis.call("ZSCORE", KEYS[4], ARGV[5])}
table.insert(result, live_info)
return result
'''

# 获取正在直播的列表信息
lua_for_get_live_list = '''
local uids = redis.call("SRANDMEMBER", KEYS[1], ARGV[1])
local result = {}
for i=1, #uids do
    result[i] = {}
    table.insert(result[i], uids[i])
    table.insert(result[i], redis.call("HMGET", KEYS[2]..uids[i], ARGV[2], ARGV[3], ARGV[4], ARGV[5], ARGV[6], ARGV[7]))
    table.insert(result[i], redis.call("ZSCORE", KEYS[3], uids[i]))
    table.insert(result[i], redis.call("ZSCORE", KEYS[4], uids[i]))
    table.insert(result[i], redis.call("HMGET", KEYS[5]..uids[i], ARGV[8], ARGV[9], ARGV[10], ARGV[11]))
end
return result
'''


class LiveCache(ExtendedCache):
    cache_name = 'live'

    def __init__(self, redis_inst):
        super(LiveCache, self).__init__(redis_inst=redis_inst)
        self.live_meta_script = self.r.register_script(lua_for_live_meta)
        self.get_live_list_script = self.r.register_script(lua_for_get_live_list)
        self.get_live_snapshot_script = self.r.register_script(lua_for_live_snapshot)
        self.get_live_hb_script = self.r.register_script(lua_for_live_hb_data)

    def add_to_living_list(self, live_id):
        self.r.sadd(RedisStr.LivingListSKey, live_id)

    def remove_from_living_list(self, live_id):
        self.r.srem(RedisStr.LivingListSKey, live_id)

    def update_live_title(self, live_id, live_title):
        self.r.hset(RedisStr.LiveHKeyPtn % live_id, RedisStr.LiveTitleField, live_title)

    def change_game_type(self, live_id, game_type):
        self.r.hset(RedisStr.LiveHKeyPtn % live_id, RedisStr.RoomGameTypeField, game_type)

    def get_lives(self, size, lives_pb):
        # ex data:[
        #             [
        #                 ['主播ID', '直播标题', '观众数', '封面', '位置', '直播间ID'],
        #                 ['会员等级', '积分', '昵称', '头像'],
        #                 '魅力值',
        #                 '财富值'
        #             ], ...
        #         ]
        live_meta_keys = (
            RedisStr.LivingListSKey,
            RedisStr.LiveHKeyPtn % "",
            RedisStr.UserHKeyPtn % "",
            RedisStr.UserCharmZKey,
            RedisStr.UserTotalFortuneZKey
        )
        live_meta_args = (
            RedisStr.LiveOwnerField,
            RedisStr.LiveTitleField,
            RedisStr.LiveCurrentViewNumField,
            RedisStr.LiveCoverField,
            RedisStr.LiveLocationField,
            RedisStr.UserVipLevelField,
            RedisStr.UserCreditField,
            RedisStr.UserNickNameField,
            RedisStr.UserAvatarField,
        )
        result = self.live_meta_script(keys=live_meta_keys, args=live_meta_args)
        for live_info in result:
            item = lives_pb.items.add()
            item.ownerId = int(live_info[0][0])
            item.title = live_info[0][1] if live_info[0][1] else ""
            item.viewerNum = atoi(live_info[0][2])
            item.cover = live_info[0][3]
            item.location = live_info[0][4] if live_info[0][4] else ""
            item.id = int(live_info[0][5])
            item.vipLevel = atoi(live_info[1][0])
            item.growValue = atoi(live_info[1][1])
            item.ownerNick = live_info[1][2]
            item.ownerPic = live_info[1][3] if live_info[1][3] else ""
            item.charm = atoi(live_info[2])
            item.fortune = atoi(live_info[3])
        return lives_pb

    def update_live_settings(self, uid, channel_info, chat_room_info):
        '''
        更新用户的直播信息, 同时将用户ID增加到正在直播列表中
        :param uid:
        :param channel_info: (channel_id, push_url, http_pull_url, hls_pull_url, rtmp_pull_url, expire_time)
        :param chat_room_info: room_id
        :return:
        '''
        p = self.r.pipeline()
        data = {
            RedisStr.LiveHeartBeatField: int(time.time())
        }
        if channel_info:
            data[RedisStr.LiveChannelIdField] = channel_info[0]
            data[RedisStr.LivePushUrlField] = channel_info[1]
            data[RedisStr.LiveHttpPullUrlField] = channel_info[2]
            data[RedisStr.LiveHlsPullUrlField] = channel_info[3]
            data[RedisStr.LiveRtmpPullUrlField] = channel_info[4]
            data[RedisStr.LiveExpireTime] = channel_info[5]
        if chat_room_info:
            data[RedisStr.LiveChatRoomField] = chat_room_info
        p.hmset(RedisStr.LiveHKeyPtn % uid, data)
        p.sadd(RedisStr.LivingListSKey, uid)
        p.sadd(RedisStr.HostsSKey, uid)
        p.execute()

    def create_live(self, uid, cover, title, create_result):
        key = RedisStr.LiveHKeyPtn % uid
        p = self.r.pipeline()
        fields = (
            RedisStr.LivePushUrlField,
            RedisStr.LiveCurrentViewNumField,
            RedisStr.LiveChatRoomField,
            RedisStr.LiveOrderNumberField,
            RedisStr.LiveChannelIdField,
            RedisStr.LiveExpireTime
        )
        p.hmget(key, fields)
        p.zscore(RedisStr.UserTotalFortuneZKey, uid)
        p.zscore(RedisStr.UserCharmZKey, uid)
        p.hmset(key, {RedisStr.LiveCoverField: cover, RedisStr.LiveTitleField: title})
        ret = p.execute()
        live_cache_data = ret[0]
        create_result.pushUrl = live_cache_data[0] if live_cache_data[0] else ''
        create_result.expireTime = atoi(live_cache_data[5])
        create_result.chatRoomId = atoi(live_cache_data[2])
        create_result.watched = atoi(live_cache_data[3])
        create_result.channelId = live_cache_data[4] if live_cache_data[4] else ''
        create_result.gold = atoi(ret[1])
        create_result.charm = atoi(ret[2])

    def get_live_list(self, lives_pb):
        live_list = self.r.smembers(RedisStr.LivingListSKey)
        p = self.r.pipeline()
        for live_id in live_list:
            p.hmget(RedisStr.LiveHKeyPtn % live_id, (
                RedisStr.LiveChatRoomField,
                RedisStr.LiveRtmpPullUrlField,
                RedisStr.LiveTitleField,
                RedisStr.LiveCoverField))
        ret = p.execute()
        # [[游戏类型, 聊天室ID, 拉流地址], ...]
        for i, item in enumerate(ret):
            live_inf = lives_pb.data.add()
            live_inf.ownerId = live_list[i]
            live_inf.chatRoomId = item[0]
            live_inf.pullUrl = item[1]
            live_inf.title = item[2]
            live_inf.cover = item[3]

    def get_live_detail(self, uid, live_id, result):
        p = self.r.pipeline()
        ukey = RedisStr.UserHKeyPtn % uid
        p.hget(ukey, RedisStr.UserVipLevelField)  # 0
        p.zscore(RedisStr.UserTotalFortuneZKey, uid)  # 1
        p.hget(RedisStr.UserHKeyPtn % live_id, RedisStr.UserVipLevelField)  # 2
        p.zscore(RedisStr.UserCharmZKey, live_id)
        p.hmget(RedisStr.LiveHKeyPtn % live_id, (
            RedisStr.LiveCurrentViewNumField,
            RedisStr.LiveRtmpPullUrlField,
            RedisStr.LiveChatRoomField,
            RedisStr.RoomGameTypeField
        ))
        p.sismember(RedisStr.LivingListSKey, live_id)
        ret = p.execute()
        logging.debug('live detail from redis: [%s]' % ret)
        result.user.vipLevel = atoi(ret[0])
        result.user.gold = atoi(ret[1])
        result.live.vipLevel = atoi(ret[2])
        result.live.charm = atoi(ret[3])
        result.live.pullUrl = ret[4][1]
        result.live.chatRoomId = atoi(ret[4][2])
        result.live.isLiving = ret[5]
        result.live.gameType = atoi(ret[4][3])

    def add_user_to_living_list(self, uid):
        p = self.r.pipeline()
        p.sadd(RedisStr.HostsSKey, uid)
        p.sadd(RedisStr.LivingListSKey, uid)
        p.hset(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveHeartBeatField, int(time.time()))
        p.execute()

    def is_user_living(self, uid):
        '''
        return True if user is living else return False.
        '''
        p = self.r.pipeline()
        p.sismember(RedisStr.LivingListSKey, uid)
        p.hget(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomGameTypeField)
        ret = p.execute()
        return ret[0] and (ret[1] is not None)

    def get_users_live_status(self, uid_list):
        p = self.r.pipeline()
        for uid in uid_list:
            p.sismember(RedisStr.LivingListSKey, uid)
        res = p.execute()
        return {uid: res[i] for i, uid in enumerate(uid_list)}

    def get_live_heart_beat_data(self):
        '''
        get current living user list and its heartbeat
        :return: [[uid, hb_time], ...]
        '''
        keys = (RedisStr.LivingListSKey, RedisStr.LiveHKeyPtn % '')
        args = (RedisStr.LiveHeartBeatField,)
        return self.get_live_hb_script(keys, args)

    def clear_dead_live(self, live_list):
        p = self.r.pipeline()
        for item in live_list:
            p.srem(RedisStr.LivingListSKey, item)
        p.execute()

    def close_live(self, live_id):
        self.r.srem(RedisStr.LivingListSKey, live_id)

    def update_live_heartbeat(self, uid, ts):
        '''
        :param uid:
        :param ts:
        :return: bool: is user in living
        '''
        p = self.r.pipeline()
        p.sismember(RedisStr.LivingListSKey, uid)
        p.hset(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveHeartBeatField, ts)
        res = p.execute()
        return res[0]

    def get_val_by_gift_req_id(self, uid, req_id):
        return self.r.get(RedisStr.LiveGiftRequestKeyPtn % (uid, req_id))

    def save_gift_req_id(self, uid, req_id, resp):
        self.r.set(RedisStr.LiveGiftRequestKeyPtn % (uid, req_id), resp)

    def get_storage(self, live_id):
        return atoi(self.r.hget(RedisStr.LiveHKeyPtn % live_id, RedisStr.LiveGameStorageField))

    def update_storage(self, live_id, storage_delta, game_type, winner_tax):
        logging.debug('storage_delta:[{}]-[{}]'.format(storage_delta, type(storage_delta)))
        p = self.r.pipeline()
        # 增加总抽水和单个游戏抽水值
        p.hincrby(RedisStr.ServerStatisticsHKey, RedisStr.GameTotalTaxField, winner_tax)
        p.hincrby(RedisStr.ServerStatisticsHKey, RedisStr.GameTaxFieldPtn % game_type, winner_tax)
        if storage_delta != 0:
            key = RedisStr.LiveHKeyPtn % live_id
            logging.debug('update storage:key:{}, field:{}, delta:{}'.format(
                key, RedisStr.LiveGameStorageField, storage_delta))
            p.hincrby(key, RedisStr.LiveGameStorageField, storage_delta)
        p.execute()

    def process_game_result(self, live_id, storage_delta, winner_bet_detail):
        '''
        :return:[new_fortune, new_fortune...]
        '''
        p = self.r.pipeline()
        if storage_delta != 0:
            key = RedisStr.LiveHKeyPtn % live_id
            logging.debug('update storage:key:{}, field:{}, delta:{}'.format(
                key, RedisStr.LiveGameStorageField, storage_delta))
            p.hincrby(key, RedisStr.LiveGameStorageField, storage_delta)
        for user_id, incr in winner_bet_detail:
            p.zincrby(RedisStr.UserTotalFortuneZKey, user_id, incr)
        p.execute()

    def get_live_list_with_channel_id(self):
        res = self.r.smembers(RedisStr.LivingListSKey)
        p = self.r.pipeline()
        for uid in res:
            p.hget(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveChannelIdField)
        channels = p.execute()
        return [(uid, channels[i]) for i, uid in enumerate(res)]

    def room_status(self, uid):
        '''
        :param uid:
        :return: 游戏类型, 是否正在直播
        '''
        ret = self.r.hmget(RedisStr.LiveHKeyPtn % uid, (RedisStr.RoomGameTypeField, RedisStr.RoomIsLivingField))
        return atoi(ret[0], 0), bool(ret[1])

    def add_room_biz(self, uid):
        '''
        :param uid:
        :return: chat room id.
        '''
        p = self.r.pipeline()
        p.sadd(RedisStr.LivingListSKey, uid)
        # p.hget(RedisStr.LiveHKeyPtn % uid, RedisStr.LiveChatRoomField)
        p.hdel(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomIsLivingField, RedisStr.RoomGameTypeField)
        p.execute()

    def stop_room_biz(self, uid):
        '''
        :param uid:
        :return: 是否在游戏，是否在直播
        '''
        p = self.r.pipeline()
        p.hmget(RedisStr.LiveHKeyPtn % uid, (RedisStr.RoomGameTypeField, RedisStr.RoomIsLivingField))
        p.srem(RedisStr.LivingListSKey, uid)
        ret = p.execute()
        return bool(ret[0][0]), bool(ret[0][1])

    def set_game_type(self, uid, game_type):
        self.r.hset(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomGameTypeField, game_type)

    def clear_game_type(self, uid):
        self.r.hdel(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomGameTypeField)

    def start_live(self, uid):
        self.r.hset(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomIsLivingField, '1')

    def stop_live(self, uid):
        self.r.hdel(RedisStr.LiveHKeyPtn % uid, RedisStr.RoomIsLivingField)

    def publish_game_data(self, routing_key, user_id, data):
        return self.r.publish(MsgModel.CHANNEL_GAME_MSG, json.dumps(make_pub_message(routing_key, {
            MsgModel.MSG_ROOM_ID_KEY: user_id, MsgModel.MSG_ROOM_DATA_KEY: data})))

    def publish_room_closed(self, host_id):
        return self.r.publish(
            MsgModel.CHANNEL_GAME_MSG, json.dumps(make_pub_message(MsgModel.ROOM_CLOSE_MSG_ROUTING_KEY, {
                MsgModel.MSG_ROOM_ID_KEY: host_id
            })))

    def publish_game_closed(self, host_id):
        return self.r.publish(
            MsgModel.CHANNEL_GAME_MSG, json.dumps(make_pub_message(MsgModel.STOP_GAME_MSG_ROUTING_KEY, {
                MsgModel.MSG_ROOM_ID_KEY: host_id
            })))

    def publish_game_started(self, host_id, game_type):
        return self.r.publish(
            MsgModel.CHANNEL_GAME_MSG, json.dumps(make_pub_message(MsgModel.START_GAME_MSG_ROUTING_KEY, {
                MsgModel.MSG_ROOM_ID_KEY: host_id,
                MsgModel.MSG_ROOM_DATA_KEY: game_type
            })))

    def publish_start_live(self, host_id):
        return self.r.publish(
            MsgModel.CHANNEL_GAME_MSG, json.dumps(make_pub_message(MsgModel.START_LIVE_MSG_ROUTING_KEY, {
                MsgModel.MSG_ROOM_ID_KEY: host_id
            })))

    def get_rank_data(self, live_id, size, daily=True):
        '''
        :param live_id: host id.
        :param size: rank data size wanted.
        :param daily: True if daily required. otherwise total.
        :return: [('host id', score), ...], ie: [('315455', 1023426.0), ...]
        '''
        key = RedisStr.DailyRankingZKeyPtn % live_id if daily else RedisStr.TotalRankingZKeyPtn % live_id
        return self.r.zrange(key, 0, size - 1, desc=True, withscores=True)

    def get_player_count(self, host_id):
        return atoi(self.r.hget(RedisStr.LiveHKeyPtn % host_id, RedisStr.LiveCurrentViewNumField))
