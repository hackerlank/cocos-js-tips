#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2016-01-15 13:30:59
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      游戏充值回调接口
# @end
# @copyright (C) 2015, kimech

import logging

from .base import BaseHandler
from apps.services import chargecallbacks

class Notification(BaseHandler):
    def get(self, platform):
        """
            1.易接SDK支付:
            alliance.xtzj.luckyfuturetech.com/notification/EZ?app=1234567890ABCDEF&cbi=CBI123456&ct=1376578903&fee=100&pt=1376577801&ssid=123456&st=1&tcd=137657AVDEDFS&uid=1234&ver=1&sign=xxxxxxxxxxx

        """
        result = do(self, platform)
        logging.info("GET charge result: %s" % result)
        self.write(result)

    def post(self, platform):
        """
            1.XY SDK支付回调
        """
        result = do(self, platform)
        logging.info("POST charge result: %s" % result)
        self.write(result)

def do(handler, platform):
    """充值实际回调接口
    """
    callback_module = '%s_pay_callback' % platform.lower()
    module = getattr(chargecallbacks, callback_module)
    # 从各平台的透传回调中验证签名，解析出正确完整的订单数据
    result = module.pay_callback(handler)

    return result

