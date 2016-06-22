#-*- coding: utf-8 -*-
import cPickle as pickle

from ..client.kvs import KVSClientV1
from .engine import StorageEngine

class KVSEngine(StorageEngine):
    
    def configure(self, cfg_value):
        StorageEngine.configure(self, cfg_value)
        self.servers = cfg_value.get("servers")
        self.default_timeout = cfg_value.get("default_timeout", 300)
        self.client = KVSClientV1(self.servers,
                                  self.default_timeout,
                                  binary=False)
    
    def get_data(self, model_cls, pkey):
        """
        model_cls:  model类对象
        pkey:       model对象主键
        """
        cache_key = model_cls.generate_cache_key(pkey)
        val = self.client.get(cache_key)
        if val is None:
            return None

        try:
            return pickle.loads(val)
        except Exception,e:
            raise e

    def put_data(self, model_cls, pkey, data, create_new):
        cache_key = model_cls.generate_cache_key(pkey)
        val = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        if create_new:
            flag = self.client.add(cache_key, val, self.default_timeout)
            if not flag:
                raise Exception('KVS client add failure, cache key: %s' % cache_key)
        else:
            flag = self.client.set(cache_key, val, self.default_timeout)
            if not flag:
                raise Exception('KVS client set failure, cache key: %s' % cache_key)
    
    def reset(self):
        self.client.close()
        
    def delete_data(self, model_cls, pkey):
        cache_key = model_cls.generate_cache_key(pkey)
        flag = self.client.delete(cache_key)
        if not flag:
            raise Exception("Rekoo KVS: delete failure, cache key: %s'" % cache_key)
        

