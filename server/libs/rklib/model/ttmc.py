#-*- coding: utf-8 -*-
import cPickle as pickle

from ..client.mcache import MemcacheClient
from .engine import StorageEngine

class TTMCEngine(StorageEngine):
    """把value压缩放在rklib里实现，适用于支持memcached协议，但不支持flag的存储。
    比如TokyoTyrant。
    """
    
    def configure(self, cfg_value):
        StorageEngine.configure(self, cfg_value)
        self.servers = cfg_value.get("servers")
        self.default_timeout = cfg_value.get("default_timeout", 0)
        self.min_compress = cfg_value.get("min_compress", 50)
        self.client = MemcacheClient(self.servers, self.default_timeout)
    
    def get_data(self, model_cls, pkey):
        """
        model_cls:  model类对象
        pkey:       model对象主键
        """
        cache_key = model_cls.generate_cache_key(pkey)
        val = self.client.get(cache_key)
        if val is None:
            return None
        if val[0] == "\x01":
            return pickle.loads(val[1:].decode("zip"))
        return pickle.loads(val[1:])
    
    def put_data(self, model_cls, pkey, data, create_new):
        cache_key = model_cls.generate_cache_key(pkey)
        val = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        if self.min_compress>0 and len(val)>=self.min_compress:
            val = "\x01" + val.encode("zip")
        else:
            val = "\x00" + val
        if create_new:
            flag = self.client.add(cache_key, val, self.default_timeout, 0)
            if not flag:
                raise Exception('memcache client add failure, cache key: %s' % cache_key)            
        else:
            flag = self.client.set(cache_key, val, self.default_timeout, 0)
            if not flag:
                raise Exception('memcache client set failure, cache key: %s' % cache_key)            

    def reset(self):
        self.client.close()  
        
    def delete_data(self, model_cls, pkey):
        cache_key = model_cls.generate_cache_key(pkey)
        flag = self.client.delete(cache_key)
        if flag == 0:
            raise Exception('memcache client delete failure, cache key: %s' % cache_key)          