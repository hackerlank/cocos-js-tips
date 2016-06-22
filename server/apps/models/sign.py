#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-10 10:30:32
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      签到数据model
# @end
# @copyright (C) 2015, kimech

import datetime

from apps.misc import utils
from libs.rklib.model import BaseModel

class Sign(BaseModel):
    """角色签到信息

    Attributes:
        uid     # 角色ID :str

    """
    def __init__(self, uid=None):
        """初始化角色签到信息

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid
        self.last_sign = 0              # 上次签到日期 20151110
        self.month_sign_days = 0        # 本月内累计签到次数

        self.last_award_index = 0       # 已领取的累计签到奖励ID
        self.total_sign_days = 0        # 总签到次数

    @classmethod
    def install(cls, uid):
        """为新角色初始安装签到信息

        Args:
            uid: 角色ID
        """
        sign = cls(uid)
        sign.put()

        return cls.get(uid)

    def sign(self, this_date):
        """玩家签到

        Args:
            this_date 今日日期 20151110

        """
        self.last_sign = this_date

        # 更新本月内累计签到次数
        if self.last_sign == 0:
            self.month_sign_days = 1
        else:
            last_date = utils.split_date(self.last_sign)
            last_month = last_date[1]

            this_date1 = utils.split_date(this_date)
            this_month = this_date1[1]

            if this_month != last_month:
                self.month_sign_days = 1
            else:
                self.month_sign_days += 1

        # 更新总签到累计次数
        self.total_sign_days += 1

        self.put()

    def award(self, index):
        """领取累计奖励
        """
        self.last_award_index = index
        self.put()

    def _reset(self):
        """重置数据
        """
        self.last_sign = 0
        self.month_sign_days = 0
        self.last_award_index = 0
        self.total_sign_days = 0

        self.put()
