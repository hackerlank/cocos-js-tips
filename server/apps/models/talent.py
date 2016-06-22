#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-24 11:20:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      天赋数据
# @end
# @copyright (C) 2015, kimech

from libs.rklib.model import BaseModel

class Talent(BaseModel):
    """天赋

    Attributes:
        uid     角色ID
        talents  天赋数据
    """

    def __init__(self, uid=None):
        """初始化天赋信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.talents = {}  # 天赋信息

    @classmethod
    def install(cls, uid):
        """为新角色初始安装天赋信息

        Args:
            uid: 角色ID
        """
        talent = cls(uid)
        talent.put()

        return cls.get(uid)

    def get_talent_by_id(self, talent_id):
        """获得某天赋信息
        """
        return self.talents.get(talent_id, 0)

    def get_talent_by_id(self, talent_id):
        """获得某天赋信息
        """
        return self.talents.get(talent_id, 0)

    def intensify(self, talent_id):
        """升级天赋

        Args:
            talent_id: 天赋ID
        """
        if talent_id not in self.talents:
            self.talents[talent_id] = 1
        else:
            self.talents[talent_id] += 1

        self.put()

    def reset_talent(self):
        """重置天赋
        """
        self.talents = {}

        self.put()
