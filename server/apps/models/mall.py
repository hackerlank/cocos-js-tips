#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-25 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       商店系统
# @end
# @copyright (C) 2015, kimech

from libs.rklib.model import BaseModel

class Mall(BaseModel):
    """角色商店信息

    Attributes:
        uid        # 角色ID   :str

    """

    def __init__(self, uid=None):
        """
        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.misc = {"items": [], "last_refresh": 0, "bought": []}
        self.honor = {"items": [], "last_refresh": 0, "bought": []}
        self.trial = {"items": [], "last_refresh": 0, "bought": []}
        self.group = {"items": [], "last_refresh": 0, "bought": []}
        self.mystery = {"items": [], "last_refresh": 0, "bought": []}  # 副本随机商店

    @classmethod
    def install(cls, uid):
        """
        Args:
            uid: 角色ID

        Returns:
            info: 商店数据实例

        """
        mall = cls(uid)
        mall.put()

        return cls.get(uid)

    def _reset(self):
        """重置
        """
        self.misc = {"items": [], "last_refresh": 0, "bought": []}
        self.honor = {"items": [], "last_refresh": 0, "bought": []}
        self.trial = {"items": [], "last_refresh": 0, "bought": []}
        self.group = {"items": [], "last_refresh": 0, "bought": []}
        self.mystery = {"items": [], "last_refresh": 0, "bought": []}  # 副本随机商店

        self.put()
