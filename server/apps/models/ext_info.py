#!/usr/bin/env python
# encoding: utf-8
"""
ext_info.py

Copyright (c) 2011 Rekoo Media. All rights reserved.
"""
from libs.rklib.model import BaseModel

class ExtInfo(BaseModel):
    """
    角色游戏扩展信息

    Attributes:
        uid: 角色ID str
        items: 扩展信息 dict
    """

    def __init__(self, uid=None):
        """
        初始化角色游戏信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.ban_chat = 0  # 禁言截止时间 0 - 未被禁言
        self.ban_account = 0  # 账号封禁截止时间 0 - 未被封禁账号

        self.boss_enter_tag = 0  # 0 - 未进入 1 - 已进入

    @classmethod
    def install(cls, uid):
        """
        为新角色初始安装游戏信息

        Args:
            uid: 角色ID
        Returns:
            ext_info: 角色游戏扩展信息对象实例
        """
        ext_info = cls(uid)
        ext_info.put()

        return cls.get(uid)
