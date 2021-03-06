#-*- coding: utf-8 -*-

import cPickle as pickle

from ..client.sredis import RedisClient
from .engine import StorageEngine

class RedisEngine(StorageEngine):
    def configure(self, cfg_value):
        StorageEngine.configure(self, cfg_value)
        self.redis_host = cfg_value.get("host")
        self.redis_port = cfg_value.get("port")
        self.redis_passwd = cfg_value.get("passwd")
        self.default_timeout = cfg_value.get("default_timeout", 0)

        self.client = RedisClient(self.redis_host, self.redis_port,
                                    self.redis_passwd, self.default_timeout)


    def get_data(self, model_cls, pkey):
        """
        model_cls:  model类对象
        pkey:       model对象主键
        """
        cache_key = model_cls.generate_cache_key(pkey)
        val = self.client.get(cache_key)
        if val is None:
            return None
        return pickle.loads(val)

    def put_data(self, model_cls, pkey, data, create_new):
        cache_key = model_cls.generate_cache_key(pkey)
        val = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        if create_new:
            flag = self.client.add(cache_key, val, self.default_timeout)
            if not flag:
                raise Exception('redis client add failure, cache key: %s' % cache_key)
        else:
            flag = self.client.set(cache_key, val, self.default_timeout)
            if not flag:
                raise Exception('redis client set failure, cache key: %s' % cache_key)

    def reset(self):
        self.client.close()

    def delete_data(self, model_cls, pkey):
        cache_key = model_cls.generate_cache_key(pkey)
        flag = self.client.delete(cache_key)
        if flag == 0:
            raise Exception('memcache client delete failure, cache key: %s' % cache_key)

