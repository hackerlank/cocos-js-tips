#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   服务器全局设置文件
#       用户唯一ID生成序列类
#       平台
#       服务器
# @end
# @copyright (C) 2015, kimech

import copy
import time
import cPickle as pickle

from libs.rklib.core import app
from apps.configs import rediskey_config

from torngas.settings_manager import settings

redis_client = app.get_storage_engine('redis').client.current

class Server(object):
    """服务器类
    """
    def __init__(self):
        super(Server, self).__init__()

    @classmethod
    def get_all_servers(cls):
        results = {}
        servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
        for s, info in servers.items():
            results[s] = pickle.loads(info)

        return results

    @classmethod
    def get_server_by_id(cls, server_id):
        try:
            server = redis_client.hget(rediskey_config.PLATFORM_SERVER_KEY, server_id)
            decrypt_data = pickle.loads(server)

            return decrypt_data
        except Exception, e:
            return {}

    @classmethod
    def get_server_state_by_id(cls, sid):
        try:
            server = redis_client.hget(rediskey_config.PLATFORM_SERVER_KEY, sid)
            decrypt_data = pickle.loads(server)

            return decrypt_data["state"]
        except Exception, e:
            return 0

class Platform(object):
    """平台类
    """
    def __init__(self):
        super(Platform, self).__init__()

    @classmethod
    def get_platform_info(cls):
        plat = redis_client.hgetall(rediskey_config.PLATFORM_CONFIG_KEY)

        return plat

    @classmethod
    def get_plat_config(cls, plat=None):
        """获取子一级渠道的配置
            PP {"sign": "PP", "checker": "auth_EZ", "name": "PP助手"}
        """
        config = redis_client.hget(rediskey_config.PLATFORM_PLATS_KEY, plat)
        if not config:
            return {}
        else:
            return pickle.loads(config)

class AccountMapping(object):
    """玩家账号类
    """
    def __init__(self):
        super(AccountMapping, self).__init__()

    @classmethod
    def generate_account_info_mysql(cls, account_id, server_id, uid):
        """将信息备份到mysql数据库中，方便统计和登录时候发送登录历史
        """
        now = int(time.time())
        engine = app.get_storage_engine("mysql")
        sql = "INSERT INTO accounts (account_id, server_id, uid, create_time, last_login) \
               VALUES ('%s', %s, '%s', %s, %s);" % (account_id, server_id, uid, now, now)

        engine.master_execute(sql)

    @classmethod
    def update_account_info_mysql(cls, account_id, server_id):
        """将信息备份到mysql数据库中，方便统计和登录时候发送登录历史
        """
        now = int(time.time())
        engine = app.get_storage_engine("mysql")
        sql = "UPDATE accounts SET last_login = %s WHERE account_id = '%s' \
               AND server_id = %s;" % (now, account_id, server_id)

        engine.master_execute(sql)

    @classmethod
    def get_login_history(cls, account_id):
        """获取账号登录历史服务器
        """
        engine = app.get_storage_engine("mysql")
        sql = "SELECT server_id, last_login FROM accounts WHERE account_id = '%s';" % account_id

        rows = engine.master_query(sql)

        return rows[:5] if rows else []
