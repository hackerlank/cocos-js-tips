#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-24 11:20:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      天赋数据
# @end
# @copyright (C) 2015, kimech

import time

from libs.rklib.model import BaseModel

from apps.misc import utils
from apps.configs import static_const

class Vip(BaseModel):
    """vip系统

    Attributes:
        uid     角色ID
        bought_gifts  已购vip特权礼包
    """

    def __init__(self, uid=None):
        """初始化vip信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid
        self.bought_gifts = 0
        self.charged_index = 0
        self.card_data = {"state": 0, "count1": 0, "count2": 0, "time1": 0, "time2": 0}

    @classmethod
    def install(cls, uid):
        """为新角色初始安装vip信息

        Args:
            uid: 角色ID
        """
        vip = cls(uid)
        vip.put()

        return cls.get(uid)

    def charge(self, index):
        """充值
        """
        if not utils.bit_test(self.charged_index, index):
            self.charged_index = utils.bit_set(self.charged_index, index)

        self.put()

    def buy(self, index):
        """购买vip特权礼包
        """
        self.bought_gifts = utils.bit_set(self.bought_gifts, index)
        self.put()

    def update_card_when_request(self):
        """玩家每次操作时，计算玩家的月卡是否失效【重要数据，必须严格】
        """
        if self.card_data["state"] == 0:
            return

        # 检测银卡是否激活
        now = int(time.time())

        if utils.bit_test(self.card_data["state"], 1) and \
            now - self.card_data["time1"] >= static_const.VIP_CARD_REMAIN_SECONDS:
                self.card_data["state"] -= 1
                self.card_data["time1"], self.card_data["count1"] = 0, 0

        if utils.bit_test(self.card_data["state"], 2) and \
            now - self.card_data["time2"] >= static_const.VIP_CARD_REMAIN_SECONDS:
                self.card_data["state"] -= 2
                self.card_data["time2"], self.card_data["count2"] = 0, 0

        self.put()

    def update_card_when_charge(self, rmb):
        """成功充值时，计算玩家是否激活月卡（金、银）两种

        Args:
            data {"state": 0, "count1": 0, "count2": 0, "time1": 1454401585, "time2": 1454401585}
                state: 0 / 1 / 2 / 3 状态 转 -》 二进制
                count1: 当前银卡充值累计 月卡失效时归0
                count2: 当前金卡充值累计 月卡失效时归0
                time1: 激活银卡的时间戳
                time2: 激活金卡的时间戳

        Returns:
            data
        """
        # 两种都已激活
        if self.card_data["state"] == 3:
            return

        # 检测银卡是否激活
        now = int(time.time())
        if not utils.bit_test(self.card_data["state"], 1):
            self.card_data["count1"] += rmb
            if self.card_data["count1"] >= static_const.VIP_SILVER_CARD_NEED_RMB:
                self.card_data["state"] += 1
                self.card_data["time1"] = now

        if not utils.bit_test(self.card_data["state"], 2):
            self.card_data["count2"] += rmb
            if self.card_data["count2"] >= static_const.VIP_GOLD_CARD_NEED_RMB:
                self.card_data["state"] += 2
                self.card_data["time2"] = now

        self.put()
