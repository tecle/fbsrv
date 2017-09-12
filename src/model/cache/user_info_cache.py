# coding: utf-8

import logging
import time

from cache_define import RedisStr
from cache_wrapper import ExtendedCache

from model.cache.cache_tools import atof
from model.cache.cache_tools import atoi
from utils.util_tools import ApkToken


class UserInfoCache(ExtendedCache):
    cache_name = 'uinfo'

    def __init__(self, inst):
        super(UserInfoCache, self).__init__(redis_inst=inst)
        self.hb_exp_secs = None

    def init_cache_conf(self, cache_conf):
        self.hb_exp_secs = cache_conf.heartbeat_exp_time

    def is_user_exist(self, key):
        return self.r.get(key)

    def map_user_key_with_id(self, key, uid):
        return self.set(key, uid)

    def get_users_online_info(self, recommend_user_pb):
        p = self.r.pipeline()
        for item in recommend_user_pb.users:
            p.exists(RedisStr.UserHeartbeatHKeyPtn % item.userId)
        # none is offline, otherwise online
        ret = p.execute()
        for idx, key_exist in enumerate(ret):
            recommend_user_pb.users[idx].onlineInfo = '1' if key_exist else '0'

    def get_users_dis_with_someone(self, someone, userList):
        '''
        param: someone = uid, user id for someone
        param: userList = [UserInfo,UserInfo..]
        return: (distance, distance..)
        '''
        if not userList:
            return userList
        p = self.r.pipeline()
        for user in userList:
            self.geodist_for_pipeline(p, "geo:util", someone, user.getID())
        ret = p.execute()
        return (float(itr) if itr else 100000000 for itr in ret)

    def set_user_yunxin_token(self, user_id, token):
        self.r.hset(RedisStr.UserHKeyPtn % user_id, RedisStr.YunxinTokenField, token)

    def get_user_yunxin_token(self, user_id):
        return self.r.hget(RedisStr.UserHKeyPtn % user_id, RedisStr.YunxinTokenField)

    def get_users_location(self, ulist):
        p = self.r.pipeline()
        for uid in ulist:
            p.hget(RedisStr.UserHKeyPtn % uid, RedisStr.UserLocationField)
        return p.execute()

    def update_user_heartbeat(self, status, panel, data, uid, timestamp, site, lon, lat, interval):
        '''
        :param status: 当前状态
        :param panel: 所在的面板
        :param data: 面板数据
        :param uid: 用户ID
        :param timestamp: 汇报时间戳
        :param lon: 经度
        :param lat: 纬度
        :param interval: 代表时间间隔，单位为分
        :return:
        '''
        mapped_data = {
            RedisStr.UserCurrentPanelField: panel,
            RedisStr.UserPanelDataField: data,
            RedisStr.UserCurrentStatusField: status
        }
        p = self.r.pipeline()
        ukey = RedisStr.UserHKeyPtn % uid
        p.hmset(ukey, {
            RedisStr.UserLastHeartBeatField: timestamp,
            RedisStr.UserLongitudeField: lon,
            RedisStr.UserLatitudeField: lat,
            RedisStr.UserCurrentStatusField: status,
            RedisStr.UserLocationField: site
        })
        p.hincrby(ukey, RedisStr.UserOnlineTimeFieldPtn, interval)
        hb_key = RedisStr.UserHeartbeatHKeyPtn % uid
        p.hmset(hb_key, mapped_data)
        p.expire(hb_key, self.hb_exp_secs)
        self.geoadd_for_pipeline(p, RedisStr.UsersLocationGKey, lon, lat, uid)
        p.execute()

    def update_user_token(self, uid, token, machine):
        self.r.hmset(RedisStr.UserHKeyPtn % uid, {
            RedisStr.UserTokenValueField: token,
            RedisStr.UserTokenMachineField: machine
        })

    def update_user_login_data(self, uid, sys_token, device, way):
        '''
        :return: token(used to login yunxin).
        '''
        ukey = RedisStr.UserHKeyPtn % uid
        p = self.r.pipeline()
        p.hget(ukey, RedisStr.YunxinTokenField)
        p.hmset(ukey, {
            RedisStr.UserLoginTypeField: way,
            RedisStr.UserLoginDeviceField: device,
            RedisStr.UserTokenValueField: sys_token,
            RedisStr.UserTokenMachineField: device
        })
        res = p.execute()
        return res[0]

    def update_user_tokens_device(self, uid, yx_token, sys_token, machine, device, way):
        self.r.hmset(RedisStr.UserHKeyPtn % uid, {
            RedisStr.YunxinTokenField: yx_token,
            RedisStr.UserLoginDeviceField: device,
            RedisStr.UserLoginTypeField: way,
            RedisStr.UserTokenValueField: sys_token,
            RedisStr.UserTokenMachineField: machine
        })

    def get_user_token(self, uid):
        res = self.r.hmget(RedisStr.UserHKeyPtn % uid, (RedisStr.UserTokenValueField, RedisStr.UserTokenMachineField))
        return ApkToken(token=res[0], machine=res[1])

    def invalid_token(self, uid):
        self.r.hdel(RedisStr.UserHKeyPtn % uid, RedisStr.UserTokenValueField, RedisStr.UserTokenMachineField)

    def process_wx_user_login(self, user_id, sys_token, device, way):
        usr_cache_key = RedisStr.UserHKeyPtn % user_id
        p = self.r.pipeline()
        p.hget(usr_cache_key, RedisStr.YunxinTokenField)
        p.hmset(usr_cache_key, {
            RedisStr.UserLoginDeviceField: device,
            RedisStr.UserLoginTypeField: way,
            RedisStr.UserTokenValueField: sys_token
        })
        ret = p.execute()
        return ret[0]

    def update_yx_token(self, user_id, token):
        self.r.hset(RedisStr.UserHKeyPtn % user_id, RedisStr.YunxinTokenField, token)

    def process_user_login(self, user_id):
        '''
        process login info
        :param user_id:
        :return: yunxin_token, ApkToken
        '''
        usr_cache_key = RedisStr.UserHKeyPtn % user_id
        ret = self.r.hmget(usr_cache_key, (
            RedisStr.YunxinTokenField,
            RedisStr.UserTokenValueField,
            RedisStr.UserTokenMachineField
        ))
        logging.debug('process_user_login:%s', ret)
        yx_token, sys_token, usr_machine = ret
        return yx_token, ApkToken(token=sys_token, machine=usr_machine)

    def get_last_login_day(self, user_id):
        return self.r.hget(RedisStr.UserHKeyPtn % user_id, RedisStr.UserLastLoginField)

    def get_and_set_last_login_day(self, user_id):
        '''
        this function will get user last login day on redis. and then set user last login day to current day.
        '''
        p = self.r.pipeline()
        key = RedisStr.UserHKeyPtn % user_id
        day = time.strftime('%Y-%m-%d')
        p.hget(key, RedisStr.UserLastLoginField)
        p.hset(key, RedisStr.UserLastLoginField, day)
        ret = p.execute()
        return ret[0]

    def add_visitors(self, user_id, visitor_id):
        '''
        :param user_id: str
        :param visitor_id: int
        :return:
        '''
        p = self.r.pipeline()
        p.zadd(RedisStr.RecentVisitorsZKeyPtn % user_id, visitor_id, int(time.time()))
        p.zscore(RedisStr.UserTotalFortuneZKey, user_id)
        res = p.execute()
        return atoi(res[1])

    def get_user_gold(self, user_id):
        return atoi(self.r.zscore(RedisStr.UserTotalFortuneZKey, user_id))

    def get_visitors(self, user_id, start, size):
        '''
        :param user_id: str
        :param start: int
        :param size: int
        :return: [(user_id, visit_time), (user_id, visit_time)...], ['Beijing',... ], [True, ...]
        '''
        visitors = self.r.zrevrange(RedisStr.RecentVisitorsZKeyPtn % user_id, start, start + size - 1, True, int)
        p = self.r.pipeline()
        for v in visitors:
            p.hget(RedisStr.UserHKeyPtn % v[0], RedisStr.UserLocationField)
            p.sismember(RedisStr.LivingListSKey, v[0])
        res = p.execute()
        locations = [res[i] for i in range(0, len(res), 2)]
        status = [res[i] for i in range(1, len(res), 2)]
        return visitors, locations, status

    def update_user_info(self, user_id, *args):
        '''
        :param user_id:
        :param args: avatar, nick, sign, born, sex, show_pics
        :return: user vip level
        '''
        key = RedisStr.UserHKeyPtn % user_id
        p = self.r.pipeline()
        p.hget(key, RedisStr.UserVipLevelField)
        arg_keys = (
            RedisStr.UserAvatarField, RedisStr.UserNickNameField, RedisStr.UserSignField,
            RedisStr.UserBornDateField, RedisStr.UserGenderField, RedisStr.UserShowPicsField)
        data = {}
        for i, arg_val in enumerate(args):
            if arg_val is not None:
                data[arg_keys[i]] = arg_val
        if data:
            p.hmset(key, data)
        res = p.execute()
        return atoi(res[0], 1)

    def get_recommend_users(self, recommend_user_pb):
        p = self.r.pipeline()
        fields = (
            RedisStr.UserVipLevelField,
            RedisStr.UserLatitudeField,
            RedisStr.UserLongitudeField,
            RedisStr.UserLocationField
        )
        for usr in recommend_user_pb.users:
            p.hmget(RedisStr.UserHKeyPtn % usr.userId, fields)
            p.sismember(RedisStr.LivingListSKey, usr.userId)
        ret = p.execute()
        for i, u in enumerate(recommend_user_pb.users):
            idx = i << 1
            item = ret[idx]
            u.vipLevel = atoi(item[0], 1)
            u.latitude = atof(item[1])
            u.longitude = atof(item[2])
            u.site = item[3] or ''
            u.status = 1 if ret[idx + 1] else 0

    def user_has_live_room(self, uid):
        return self.r.exists(RedisStr.LiveHKeyPtn % uid)

    def user_live_status(self, uid):
        '''
        :param uid: user id
        :return: (is anchor, is living, location)
        '''
        p = self.r.pipeline()
        p.hmget(RedisStr.UserHKeyPtn % uid, (RedisStr.UserIsAnchorField, RedisStr.UserLocationField))
        p.sismember(RedisStr.LivingListSKey, uid)
        ret = p.execute()
        user_info = ret[0]
        return atoi(user_info[0]) > 0, ret[1], user_info[1]

    def get_user_vip_level_info(self, uid):
        '''
        :return: nick name, vip level, charge number
        '''
        fields = (RedisStr.UserNickNameField, RedisStr.UserVipLevelField, RedisStr.UserRechargeField)
        ret = self.r.hmget(RedisStr.UserHKeyPtn % uid, fields)
        return ret[0], atoi(ret[1], 1), atof(ret[2])

    def update_user_vip_level_info(self, uid, level, charge_sum):
        self.r.hmset(RedisStr.UserHKeyPtn % uid, {
            RedisStr.UserVipLevelField: level,
            RedisStr.UserRechargeField: charge_sum
        })

    def get_users_meta_info(self, uid_list, result):
        '''
        :param uid_list:
        :param result: UsersMetaInfo()
        :return: user id to query from db
        '''
        fields_wanted = (
            RedisStr.UserNickNameField,
            RedisStr.UserAvatarField,
            RedisStr.UserGenderField,
            RedisStr.UserSignField,
            RedisStr.UserVipLevelField,
        )
        attr_map = ("nickName", "avatar", "isMale", "signature", "vipLevel")
        p = self.r.pipeline()
        for uid in uid_list:
            p.hmget(RedisStr.UserHKeyPtn % uid, fields_wanted)
            p.sismember(RedisStr.LivingListSKey, uid)
        res = p.execute()
        failed_user = {}  # key is str
        i, sentinel = 0, len(res)
        while i < sentinel:
            data = res[i]
            in_living_list = res[i + 1]
            cached = True
            u = result.users.add()
            u.id = int(uid_list[i >> 1])  # convert to int
            u.status = 'L' if in_living_list else 'N'
            for j, cache_item in enumerate(data):
                if cache_item is None:
                    cached = False
                    break
                setattr(u, attr_map[j], cache_item)
            if cached:
                u.vipLevel = atoi(u.vipLevel, 1)
                u.isMale = atoi(u.isMale, 0)
            else:
                failed_user[u.id] = u
            i += 2
        return failed_user

    def update_users_info(self, users):
        p = self.r.pipeline()
        for u in users.users:
            p.hmset(RedisStr.UserHKeyPtn % u.id, {
                RedisStr.UserAvatarField: u.avatar,
                RedisStr.UserGenderField: u.isMale,
                RedisStr.UserNickNameField: u.nickName,
                RedisStr.UserSignField: u.signature
            })
        p.execute()

    def get_third_login_data(self, user_id):
        '''
        :return: pre login type, pre login device, yx_token
        '''
        return self.r.hmget(
            RedisStr.UserHKeyPtn % user_id,
            (RedisStr.UserLoginTypeField, RedisStr.UserLoginDeviceField, RedisStr.YunxinTokenField))

    def get_users_status(self, user_id_list):
        p = self.r.pipeline()
        for uid in user_id_list:
            p.hget(RedisStr.UserHKeyPtn % uid, RedisStr.UserLocationField)
            p.sismember(RedisStr.LivingListSKey, uid)
        ret = p.execute()
        return [ret[i] for i in range(0, len(ret), 2)], [ret[i] for i in range(1, len(ret), 2)]
