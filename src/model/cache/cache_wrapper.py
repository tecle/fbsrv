# coding: utf-8

import logging

import redis
from redis.connection import Token


class ExtendedCache(object):
    def __init__(self, cfg=None, redis_inst=None):
        if not cfg and not redis_inst:
            from utils.server_exceptions import BadInitError
            raise BadInitError('one of cfg/redis_int must be given.')
        self.r = \
            redis.Redis(host=cfg.redis.host, port=cfg.redis.port, db=0, password=cfg.redis.pwd) if cfg else redis_inst

    def init_cache_conf(self, cache_conf):
        pass

    '''Here is geodist implement for redis.'''

    def geodist(self, name, place1, place2, unit=None):
        pieces = [name, place1, place2]
        if unit and unit not in ('m', 'km', 'mi', 'ft'):
            raise Exception("GEODIST invalid unit")
        elif unit:
            pieces.append(unit)
        return self.r.execute_command('GEODIST', *pieces)

    def geoadd(self, name, *values):
        if len(values) % 3 != 0:
            raise Exception("Invalid params number")
        return self.r.execute_command('GEOADD', name, *values)

    def geopos(self, name, *values):
        return self.r.execute_command('GEOPOS', name, *values)

    def georadius(self, name, longitude, latitude, radius, unit=None, withdist=False, withcoord=False, withhash=False,
                  count=None, sort=None, store=None, store_dist=None):
        '''count: max location number, sort:asc or desc, withdist:show distance in result'''
        return self._georadiusgeneric('GEORADIUS', name, longitude, latitude, radius, unit=unit, withdist=withdist,
                                      withcoord=withcoord, withhash=withhash, count=count, sort=sort, store=store,
                                      store_dist=store_dist)

    def georadiusbymember(self, name, member, radius, unit=None, withdist=False, withcoord=False,
                          withhash=False, count=None, sort=None, store=None, store_dist=None):
        return self._georadiusgeneric('GEORADIUSBYMEMBER', name, member, radius, unit=unit,
                                      withdist=withdist, withcoord=withcoord, withhash=withhash, count=count,
                                      sort=sort, store=store, store_dist=store_dist)

    def _georadiusgeneric(self, command, *args, **kwargs):
        pieces = list(args)
        if kwargs['unit'] and kwargs['unit'] not in ('m', 'km', 'mi', 'ft'):
            raise Exception("GEORADIUS invalid unit")
        elif kwargs['unit']:
            pieces.append(kwargs['unit'])
        else:
            pieces.append('m', )
        for token in ('withdist', 'withcoord', 'withhash'):
            if kwargs[token]:
                pieces.append(Token(token.upper()))
        if kwargs['count']:
            pieces.extend([Token('COUNT'), kwargs['count']])
        if kwargs['sort'] and kwargs['sort'] not in ('ASC', 'DESC'):
            raise Exception("GEORADIUS invalid sort")
        elif kwargs['sort']:
            pieces.append(Token(kwargs['sort']))
        if kwargs['store'] and kwargs['store_dist']:
            raise Exception("GEORADIUS store and store_dist cant be set together")
        if kwargs['store']:
            pieces.extend([Token('STORE'), kwargs['store']])
        if kwargs['store_dist']:
            pieces.extend([Token('STOREDIST'), kwargs['store_dist']])
        return self.r.execute_command(command, *pieces, **kwargs)

    def geodist_for_pipeline(self, pipeline, name, place1, place2, unit=None):
        pieces = [name, place1, place2]
        if unit and unit not in ('m', 'km', 'mi', 'ft'):
            raise Exception("GEODIST invalid unit")
        elif unit:
            pieces.append(unit)
        return pipeline.execute_command('GEODIST', *pieces)

    def geoadd_for_pipeline(self, pipeline, name, *values):
        if len(values) % 3 != 0:
            raise Exception("Invalid params number")
        return pipeline.execute_command('GEOADD', name, *values)

    "Here is raw function of redis client"

    def set(self, key, val):
        return self.r.set(key, val)

    def get(self, key):
        return self.r.get(key)


class CacheWrapper(object):
    def __init__(self, cfg):
        self.r = redis.Redis(host=cfg.redis.host, port=cfg.redis.port, db=cfg.redis.db, password=cfg.redis.pwd)
        self.workers = {}
        self.cfg = cfg.redis

    def register_cache(self, name, cls):
        inst = cls(self.r)
        inst.init_cache_conf(self.cfg)
        self.workers[name] = inst

    def get_cache(self, name):
        return self.workers[name]

    def redis_info(self):
        return self.r.info('server')

    def reset_redis_server(self, host, port, db=0, pwd=None):
        try:
            r = redis.Redis(host=host, port=port, db=db, password=pwd)
            logging.info('switch to new redis:{}'.format(r.info('server')))
            for cache_name, cache_inst in self.workers.items():
                cache_inst.r = r
            self.r = r
        except Exception:
            logging.exception('reset redis server[{},{},{},{}] failed.'.format(host, port, db, pwd))
            return False
        return True
