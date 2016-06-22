#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *

# 启用调试模式
DEBUG = False

# ============================================================================
CHANNEL = "ios"  #  [android | apple | ios] [只能小写]

WEB_KEY = 'spyykimech'
GAME_KEY = ')7yt4e!#)gcy&amp;#0^hlme-+082=s!b!$8+h$+(j0bucx0+nu%pe'

ENCODE_DECODE_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
ENCODE_DECODE_IV = "1234567812345678"

# SECRET_KEY = ')7yt4e!#)gcy&amp;#0^hlme-+082=s!b!$8+h$+(j0bucx0+nu%pe'
# ============================================================================
# tornado日志功能配置
LOGGER_CONFIG = {
    "use_tornadolog": False,
    "root_level": 'INFO',
    "root_dir": '/xtzj/game_logs/', # 日志根目录（如果某具体日志filename指定路径，则自动忽略此根目录配置）
}

LOGGER = {
    'tornado': {
        "OPEN": True,
        "LEVEL": "INFO",
        "HANDLERS": [
            {
                "module": "torngas.logger.CustomRotatingFileHandler",
                "filename": "info",
                "when": "W0",
                "encoding": "utf-8",
                "delay": True,
                "backupCount": 100,
            }
        ]
    },

    'torngas.accesslog': {
        "OPEN": True,
        "LEVEL": "INFO",
        "FORMATTER": '%(message)s',
        "HANDLERS": [
            {
                "module": "torngas.logger.UsePortRotatingFileHandler",
                "filename": "access",
                "when": "midnight",
                "encoding": "utf-8",
                "delay": False,
                "backupCount": 100,
            }
        ]
    },

    'statictics.dau': {
        "OPEN": True,
        "LEVEL": "INFO",
        "FORMATTER": '%(message)s',
        "HANDLERS": [
            {
                "module": "torngas.logger.UsePortRotatingFileHandler",
                "filename": "login",
                "when": "midnight",
                "encoding": "utf-8",
                "delay": False,
                "backupCount": 100,
            }
        ]
    },

    'statictics.charge': {
        "OPEN": True,
        "LEVEL": "INFO",
        "FORMATTER": '%(message)s',
        "HANDLERS": [
            {
                "module": "torngas.logger.CustomRotatingFileHandler",
                "filename": "pay",
                "when": "W0",
                "encoding": "utf-8",
                "delay": False,
                "backupCount": 100,
            }
        ]
    },

    'statictics.charge_error': {
        "OPEN": True,
        "LEVEL": "INFO",
        "FORMATTER": '%(message)s',
        "HANDLERS": [
            {
                "module": "torngas.logger.CustomRotatingFileHandler",
                "filename": "pay_error",
                "when": "W0",
                "encoding": "utf-8",
                "delay": False,
                "backupCount": 100,
            }
        ]
    },
}
