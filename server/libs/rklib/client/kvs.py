#-*- coding: utf-8 -*-
try:
    import pylibmc as memcache
    _pylibmc = True
except ImportError, e:
    import memcache
    _pylibmc = False

from ..utils.encoding import force_str, force_unicode

class KVSClientV1(object):
    def __init__(self, servers, default_timeout=300, binary=False):
        '''
        servers is a string like "192.168.0.1:9988;192.168.0.1:9989"
        '''
        if _pylibmc:
            self._current = memcache.Client(servers.split(';'), binary=binary)
            self._current.behaviors['distribution'] = 'consistent'
            self._current.behaviors['tcp_nodelay'] = 1
        else:
            self._current = memcache.Client(servers.split(';'))
        self.default_timeout = default_timeout

    def compress(self, input, min_compress):
        if input is None:
            return None

        if min_compress>0 and len(input)>=min_compress:
            return "\x01" + input.encode("zlib")
        else:
            return "\x00" + input

    def decompress(self, input):
        if input is None:
            return None

        if input[0] == "\x01":
            return input[1:].decode("zlib")
        else:
            if input == '<D>':
                return None
            return input[1:]
    
    def add(self, key, value, timeout=0, min_compress=50):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        val = self.get(key)
        if val is None:
            return self._current.set(force_str(key),\
                                     self.compress(value, min_compress), \
                                     timeout or self.default_timeout,\
                                     0) # no compress by pylibmc
        else:
            return 0
    
    def get(self, key, default=None):
        try:
            val = self._current.get(force_str(key))
        except:
            val = self._current.get(force_str(key))

        val = self.decompress(val)
        if val is None:
            return default

        return val
    
    def delete(self, key):
        try:
            return self._current.set(force_str(key), \
                                     '<D>', \
                                     self.default_timeout,\
                                     0) # no compress by pylibmc
        except:
            return self._current.set(force_str(key), \
                                     '<D>', \
                                     self.default_timeout,\
                                     0) # no compress by pylibmc

    def set(self, key, value, timeout=0, min_compress=50):
        if isinstance(value, unicode):
            value = value.encode('utf-8')

        try:
            return self._current.set(force_str(key), \
                                     self.compress(value, min_compress), \
                                     timeout or self.default_timeout,\
                                     0) # no compress by pylibmc
        except:
            return self._current.set(force_str(key), \
                                     self.compress(value, min_compress), \
                                     timeout or self.default_timeout,\
                                     0) # no compress by pylibmc
    
    def close(self, **kwargs):
        self._current.disconnect_all()
    
    def current(self):
        return self._current


