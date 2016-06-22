#-*- coding: utf-8 -*-
# import time
# import sys
# import os
# import socket

# from ..client.mcache import MemcacheClient
# from ..model import storage_context

# class ConfigChecker(object):
#     def __init__(self):
#         self._cache = None
#         self._ts = 0

#     def setup(self, cache_server="127.0.0.1:11211", cache_flag_key="config_reload", reload_handler=None):
#         self._cache_server = cache_server
#         self._cache_flag_key = cache_flag_key
#         self._reload_handler = reload_handler
#         self._cache = MemcacheClient(self._cache_server)
#         self._cache_flag = None
#         self.check(None)

#     def check(self, children):
#         ts = int(time.time())
#         if ts-self._ts < 5:
#             return
#         self._ts = ts
#         if not self._cache:
#             return
#         try:
#             flag = self._cache.get(self._cache_flag_key)
#         except:
#             return
#         if (flag is not None) and flag <> self._cache_flag:
#             # 重新加载
#             print ">>> check_config_update", os.getpid()
#             storage_context.clear()
#             self._reload_handler()
#             storage_context.save()
#             # 通知子进程关闭
#             if children:
#                 for pid, d in children.items():
#                     child = d['file']
#                     ret = _notifyChild(child, "\xFF")
#                     # print ret
#                     d['file'].close()
#                     d['file'] = None
#                     d['avail'] = False
#             self._cache_flag = flag

# def _notifyChild(child, msg):
#     try:
#         child.send(msg)
#         return True
#     except socket.error, e:
#         return False
