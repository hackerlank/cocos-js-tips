#-*- coding: utf-8 -*-

import redis

from ..utils.encoding import force_str, force_unicode

class RedisClient(object):
    def __init__(self, host, port, passwd, default_timeout=0):
        '''
        retry_on_timeout 超时重试机制
        '''
        self._current = redis.StrictRedis(
                                        host=host,
                                        port=port,
                                        password=passwd,
                                        socket_connect_timeout=3,
                                        socket_timeout=2,
                                        retry_on_timeout=True
                                    )

        self.default_timeout = default_timeout

    def add(self, key, value, timeout=0, min_compress=50):
        if isinstance(value, unicode):
            value = value.encode('utf-8')

        return self._current.set(force_str(key), value)

    def get(self, key, default=None):
        try:

            val = self._current.get(force_str(key))
        except:
            val = self._current.get(force_str(key))

        if val is None:
            return default

        return val

    def set(self, key, value, timeout=0, min_compress=50):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        try:
            return self._current.set(force_str(key), value)
        except:
            return self._current.set(force_str(key), value)

    def delete(self, key):
        try:
            try:
                val = self._current.delete(force_str(key))
            except:
                val = self._current.delete(force_str(key))

            if type(val)==bool:
                val = 1
        except:
            val = 0
        return val

    def get_multi(self, keys):
        return self._current.get_multi(map(force_str, keys))

    def close(self, **kwargs):
        # self._current.disconnect_all()
        pass

    def incr(self, key, delta=1):
        return self._current.incr(key, delta)

    def decr(self, key, delta=1):
        return self._current.decr(key, delta)

    def zadd(self, key, score, member):
        return self._current.zadd(key, score, member)

    def zrange(self, key, start, end, withscores=True):
        return self._current.zrange(key, start, end, withscores)

    @property
    def current(self):
        return self._current
