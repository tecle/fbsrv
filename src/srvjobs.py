# coding: utf-8

import datetime
import logging
import os
import sys

import redis
import torndb

ROOT = os.getcwd()
sys.path.append(os.path.join(ROOT, 'libs'))
sys.path.append(os.path.join(ROOT, 'src'))
from configs.config_wrapper import ConfigWrapper
from model.cache.cache_define import RedisStr

daily_table = 'DailyRankData'
total_table = 'TotalRankData'


def main():
    cfg_f = 'server-config/server.cfg'
    if len(sys.argv) > 1:
        cfg_f = sys.argv[1]
    cfg = ConfigWrapper()
    cfg.parse(cfg_f)
    conn = torndb.Connection('{}:{}'.format(
        cfg.db.host, cfg.db.port), cfg.db.name, cfg.db.user, cfg.db.password, time_zone='+8:00')
    rds = redis.Redis(cfg.redis.host, cfg.redis.port, int(getattr(cfg.redis, 'db', 0)), getattr(cfg.redis, 'pwd'))
    today = datetime.date.today().strftime('%Y-%m-%d')

    host_list = rds.smembers(RedisStr.HostsSKey)
    logging.info('save host data:%s', host_list)
    for host in host_list:
        head100 = rds.zrange(RedisStr.DailyRankingZKeyPtn % host, 0, 100, desc=True, withscores=True)
        rds.delete(RedisStr.DailyRankingZKeyPtn % host)
        daily_rank = ','.join(['{}:{}'.format(uid, score) for uid, score in head100]) if head100 else ''

        head100 = rds.zrange(RedisStr.TotalRankingZKeyPtn % host, 0, 100, desc=True, withscores=True)
        total_rank = ','.join(['{}:{}'.format(uid, score) for uid, score in head100]) if head100 else ''

        try:
            conn.insert(
                'insert into {} (host_id, detail, ctime) values(%s, %s, %s)'.format(daily_table), host, daily_rank, today)
            conn.update('insert into {} (host_id, detail, ctime) '
                        'values(%s, %s, %s) on duplicate key update detail=%s, ctime=%s'.format(
                total_table), host, total_rank, today, total_rank, today)
        except:
            logging.exception('host:%s\ndaily:%s\ntotal:%s\ntoday:%s', host, daily_rank, total_rank, today)


if __name__ == "__main__":
    '''
    cmd: srvjobs {conf_path}
    '''
    logging.basicConfig(
        filename='logs/job.log',
        filemode='a',
        format='[%(levelname)s][%(filename)s:%(lineno)d][%(asctime)s]:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    main()
