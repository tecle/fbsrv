# coding: utf-8

import logging
import time

from cache_define import RedisStr
from cache_wrapper import ExtendedCache

from model.cache.cache_tools import atoi


class GroundCache(ExtendedCache):
    cache_name = 'ground'

    def __init__(self, redis):
        super(GroundCache, self).__init__(redis_inst=redis)
        self.max_fresh_active_for_topic = 3
        self.topic_list_expire_secs = 60

    def process_add_active(self, topic_id, active_id, user_id, latitude, longitude):
        '''when new active generated, record it position and push to new actives list'''
        p = self.r.pipeline()
        self.geoadd_for_pipeline(p, RedisStr.ActivesLocationGKey, longitude, latitude, active_id)
        p.zadd(RedisStr.FreshActiveIdLKeyPtn % topic_id, active_id, -active_id)
        topic_key = RedisStr.TopicHKeyPattern % topic_id
        p.hincrby(topic_key, RedisStr.TopicActiveNumField, 1)
        p.hincrby(topic_key, RedisStr.TopicViewNumField, 1)
        p.zadd(RedisStr.TopicParticipantsZKeyPtn % topic_id, user_id, int(time.time()))
        p.execute()

    def set_active_location(self, active_id, latitude, longitude):
        logging.debug('Set active[%d] location: %s, %s' % (active_id, latitude, longitude))
        self.geoadd(RedisStr.ActivesLocationGKey, longitude, latitude, active_id)

    def get_actives_nearby(self, latitude, longitude, radius, wanted_num):
        ''':return [[location name, location distance],[...]]'''
        ret = self.georadius(RedisStr.ActivesLocationGKey, longitude, latitude, radius=radius, count=wanted_num,
                             withdist=True, sort='ASC', unit='m')
        return ret

    def like_active(self, user_id, active_id, liked=True):
        p = self.r.pipeline()
        p.zincrby(RedisStr.ActiveLikeNumZKey, active_id, 1 if liked else -1)
        if liked:
            p.sadd(RedisStr.ActiveLikedUserSKeyPtn % active_id, user_id)
        else:
            p.srem(RedisStr.ActiveLikedUserSKeyPtn % active_id, user_id)
        p.get(RedisStr.ActivePushFlagKeyPtn % (active_id, user_id))
        p.set(RedisStr.ActivePushFlagKeyPtn % (active_id, user_id), '1', ex=24 * 3600)
        ret = p.execute()
        logging.info('active[%s] liked num:%s' % (active_id, ret[0]))
        return int(ret[0]), ret[2]

    def flag_push_like_active(self, active_id, target_id):
        self.r.set(RedisStr.ActivePushFlagKeyPtn % (active_id, target_id), '1', ex=24 * 3600)

    def is_liked(self, user_id, active_id):
        return self.r.sismember(RedisStr.ActiveLikedUserSKeyPtn % active_id, user_id)

    def get_actives_info(self, uid, actives_obj):
        p = self.r.pipeline()
        for active in actives_obj.actives:
            aid = active.activeId
            p.zscore(RedisStr.ActiveViewNumZKey, aid)
            p.zscore(RedisStr.ActiveLikeNumZKey, aid)
            p.zscore(RedisStr.ActiveCommentNumZKey, aid)
            p.sismember(RedisStr.ActiveLikedUserSKeyPtn % aid, uid)
        ret = p.execute()
        i = 0
        for j in range(0, len(ret), 4):
            actives_obj.actives[i].viewNum = atoi(ret[j])
            actives_obj.actives[i].likeNum = atoi(ret[j + 1])
            actives_obj.actives[i].commentNum = atoi(ret[j + 2])
            actives_obj.actives[i].isLiked = ret[j + 3] if ret[j + 3] else False
            i += 1

    def get_actives_nearby_data(self, uid, actives_pb):
        self.get_actives_info(uid, actives_pb)

    def get_active_info(self, uid, aid):
        p = self.r.pipeline()
        p.zincrby(RedisStr.ActiveViewNumZKey, aid, 1)
        p.zscore(RedisStr.ActiveLikeNumZKey, aid)
        p.zscore(RedisStr.ActiveCommentNumZKey, aid)
        p.sismember(RedisStr.ActiveLikedUserSKeyPtn % aid, uid)
        ret = p.execute()
        return atoi(ret[0]), atoi(ret[1]), atoi(ret[2]), ret[3]

    def get_actives_statistics(self, actives_pb):
        p = self.r.pipeline()
        for active in actives_pb.data:
            aid = active.id
            p.zincrby(RedisStr.ActiveViewNumZKey, aid, 1)
            p.zscore(RedisStr.ActiveLikeNumZKey, aid)
            p.zscore(RedisStr.ActiveCommentNumZKey, aid)
        ret = p.execute()
        logging.debug('actives info from redis is [%s]' % ret)
        i = 0
        j = 0
        ad = actives_pb.data
        while j < len(ret):
            ad[i].viewNum = atoi(ret[j])
            ad[i].likeNum = atoi(ret[j + 1])
            ad[i].commentNum = atoi(ret[j + 2])
            j += 3
            i += 1

    def add_comment_number(self, aid, incr=1):
        return self.r.zincrby(RedisStr.ActiveCommentNumZKey, aid, incr)

    def process_add_comment(self, topic_id, active_id, user_id):
        p = self.r.pipeline()
        p.zincrby(RedisStr.ActiveCommentNumZKey, active_id, 1)
        p.hincrby(RedisStr.TopicHKeyPattern % topic_id, RedisStr.TopicViewNumField, 1)
        p.zadd(RedisStr.TopicParticipantsZKeyPtn % topic_id, user_id, int(time.time()))
        res = p.execute()
        return atoi(res[0])

    def add_new_active(self, topic_id, active_id):
        active_num = self.r.lpush(RedisStr.FreshActiveIdLKeyPtn % topic_id, active_id)
        return active_num

    def get_fresh_actives(self, topic_id, actives_wanted):
        ret = self.r.zrange(RedisStr.FreshActiveIdLKeyPtn % topic_id, 0, actives_wanted)
        return ret

    def get_actives_older_than(self, topic_id, active_id, actives_wanted):
        p = self.r.pipeline()
        p.zrangebyscore(RedisStr.FreshActiveIdLKeyPtn % topic_id, -active_id + 1, '+inf', 0, actives_wanted)
        p.hincrby(RedisStr.TopicHKeyPattern % topic_id, RedisStr.TopicViewNumField, 1)
        ret = p.execute()
        logging.debug('actives newer than [{}] is [{}]'.format(active_id, ret))
        return ret[0]

    def get_actives_newer_than(self, topic_id, active_id, actives_wanted):
        p = self.r.pipeline()
        p.zrangebyscore(RedisStr.FreshActiveIdLKeyPtn % topic_id, '-inf', -active_id - 1, 0, actives_wanted)
        p.hincrby(RedisStr.TopicHKeyPattern % topic_id, RedisStr.TopicViewNumField, 1)
        ret = p.execute()
        logging.debug('actives newer than [{}] is [{}]'.format(active_id, ret))
        return ret[0]

    def remove_active(self, topic_id, active_id):
        self.r.zrem(RedisStr.FreshActiveIdLKeyPtn % topic_id, active_id)
        self.r.zrem(RedisStr.ActivesLocationGKey, active_id)

    def update_user_avatar(self, avatar_data):
        p = self.r.pipeline()
        for uid, avatar in avatar_data.iteritems():
            p.hset(RedisStr.UserInfoCacheHKeyPtn % uid, RedisStr.UserAvatarField, avatar)
        p.execute()

    def process_topics_data(self, topics, participants_count):
        if not topics:
            return
        p = self.r.pipeline()
        for item in topics:
            p.hmget(
                RedisStr.TopicHKeyPattern % item.topicId,
                (RedisStr.TopicViewNumField, RedisStr.TopicActiveNumField))
            topic_key = RedisStr.TopicParticipantsZKeyPtn % item.topicId
            p.zrevrange(topic_key, 0, participants_count)
        ret = p.execute()
        logging.debug('topic data:{}'.format(ret))

        uid_list = set()
        for i, item in enumerate(topics):
            j = (i << 1)
            item.views = atoi(ret[j][0], 1)
            item.activeNum = atoi(ret[j][1], 1)
            item.participants = ret[j + 1]
            uid_list.update(ret[j + 1])
        logging.debug('user list:{}'.format(uid_list))

        p = self.r.pipeline()
        for uid in uid_list:
            p.hget(RedisStr.UserInfoCacheHKeyPtn % uid, RedisStr.UserAvatarField)
        res = p.execute()
        return {uid: res[i] for i, uid in enumerate(uid_list)}

    def get_topic_in_cache(self, part):
        return self.r.hget(RedisStr.TopicListHkey, part)

    def update_topic_in_cache(self, part, content):
        p = self.r.pipeline()
        p.hset(RedisStr.TopicListHkey, part, content)
        p.expire(RedisStr.TopicListHkey, self.topic_list_expire_secs)
        p.execute()
