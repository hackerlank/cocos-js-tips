#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

# =============================================================================================
LOGIC_CFG = os.path.join(PROJECT_PATH, 'apps/configs/app_config/logic.conf')
MODEL_CFG = os.path.join(PROJECT_PATH, 'apps/configs/app_config/model.conf')
STORAGE_CFG = os.path.join(PROJECT_PATH, 'apps/configs/app_config/storage.conf')

PLATFORM_APP_ID_MAPPING = {
    # iOS越狱
    "EZ": {"AppId": "D55F59377551A60E", "PayKey": "18JV53J1T371M459JHDEGRSY5MFSVO2W","checker": "auth_EZ"},
    "WHWJ": {"AppId": 202, "AppKey":"iYZzeZ6c", "PayKey": "DCdpov0N","checker": "auth_WHWJ"},
}

# 充值mysql表头 'orders'
CHARGE_ORDER_TABLE_NAME = 'orders'

GAME_API_URL = '/game/api'

USER_TYPE_INNER = 1
# 服务器状态配置
SERVER_STATE_CLOSE = 0
SERVER_STATE_OPEN = 1
SERVER_STATE_UPDATE = 2

# =============================================================================================

# 开启tornado xheaders
XHEADERS = True

# tornado全局配置
TORNADO_CONF = {
    "static_path": "static",
    "xsrf_cookies": False,
    "login_url": '/login',
    "cookie_secret": "bXZ/gDAbQA+zaTxdqJwxKa8OZTbuZE/ok3doaow9N4Q=",
    "template_path": os.path.join(PROJECT_PATH, 'templates'),
    "default_handler_class":'torngas.handler.ErrorHandler',
    # 安全起见，可以定期生成新的cookie 秘钥，生成方法：
    # base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
}

# ###########
# 中间件     #
# ###########
MIDDLEWARE_CLASSES = (
    'torngas.middleware.accesslog.AccessLogMiddleware',
    # 'apps.common.middlewares.timeview.TimeviewMiddleware',
    'apps.common.middlewares.context.KiContextMiddleware',
    'apps.common.middlewares.kiauth.KiAuthMiddleware',
    'apps.common.middlewares.paramsdetector.ParamsDetectorMiddleware',
    'apps.common.middlewares.userfunc.UserFuncMiddleware',
    # 'torngas.httpmodule.httpmodule.HttpModuleMiddleware',
)

INSTALLED_APPS = (
    'apps',
)

# ##########
# 缓存配置 #
# ##########
CACHES = {
    'default': {
        'BACKEND': 'torngas.cache.backends.localcache.LocMemCache',
        'LOCATION': 'process_cache',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
            'CULL_FREQUENCY': 3
        }
    },
    'default_memcache': {
        'BACKEND': 'torngas.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '127.0.0.1:11211'
        ],
        'TIMEOUT': 300
    },
    'dummy': {
        'BACKEND': 'torngas.cache.backends.dummy.DummyCache'
    },
    'default_redis': {
        'BACKEND': 'torngas.cache.backends.rediscache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'DB': 0,
            'PARSER_CLASS': 'redis.connection.DefaultParser',
            'POOL_KWARGS': {
                # timeout参数对有网络请求的库
                # 一定要加上，不然默认的timeout都很长，阻塞了就悲剧了
                'socket_timeout': 2,
                'socket_connect_timeout': 2
            },
            'PING_INTERVAL': 120  # 定时ping redis连接池，防止被服务端断开连接（s秒）
        }
    },
}

# 白名单未开启，如需使用，请用元祖列出白名单ip
WHITELIST = False
# ######
# WHITELIST = (
# '127.0.0.1',
# '127.0.0.2',
# )

# tornado日志功能配置
LOGGER_CONFIG = {
    "use_tornadolog": False,
    "root_level": 'INFO',
    # 日志根目录（如果某具体日志filename指定路径，则自动忽略此根目录配置）
    "root_dir": 'logs/'
}

IPV4_ONLY = True

# 开启session支持
SESSION = {
    'session_cache_alias': 'default',  # 'session_loccache',对应cache配置
    'session_name': '__TORNADOSSID',
    'cookie_domain': '',
    'cookie_path': '/',
    'expires': 0,  # 24 * 60 * 60, # 24 hours in seconds,0代表浏览器会话过期
    'ignore_change_ip': False,
    'httponly': True,
    'secure': False,
    'secret_key': 'fLjUfxqXtfNoIldA0A0J',
    'session_version': 'EtdHjDO1'
}
