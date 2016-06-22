#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *

# 启用调试模式
DEBUG = True

# ============================================================================
CHANNEL = "dev"  #  [android | apple | ios] [只能小写]

WEB_KEY = 'spyykimech'
GAME_KEY = ')7yt4e!#)gcy&amp;#0^hlme-+082=s!b!$8+h$+(j0bucx0+nu%pe'

ENCODE_DECODE_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
ENCODE_DECODE_IV = "1234567812345678"

# SECRET_KEY = ')7yt4e!#)gcy&amp;#0^hlme-+082=s!b!$8+h$+(j0bucx0+nu%pe'

# ============================================================================
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
                "when": "W0",
                "encoding": "utf-8",
                "delay": False,
                "backupCount": 100,
            }
        ]
    },
}
