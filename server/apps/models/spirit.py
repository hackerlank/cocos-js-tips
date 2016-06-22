#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-24 11:20:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   战魂数据
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config

from libs.rklib.model import BaseModel
from apps.logics.helpers import common_helper

class Spirit(BaseModel):
    """战魂

    Attributes:
        uid     角色ID
        spirits  战魂信息
    """

    DEFAULT_LEVEL = 1
    DEFAULT_EXP = 0

    MAX_EXP = max(game_config.spirit_exp_level_cfg)

    def __init__(self, uid=None):
        """初始化角色机甲战魂信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.spirits = {}  # 战魂信息

    @classmethod
    def install(cls, uid):
        """为新角色初始安装机甲战魂信息

        Args:
            uid: 角色ID
        """
        spirit = cls(uid)
        spirit.put()

        return cls.get(uid)

    def get_spirit(self, hero_id, spirit_id):
        """获取单个战魂数据
        """
        return self.spirits.get(hero_id, {}).get(spirit_id, {})

    def get_spirits_by_hero_id(self, hero_id):
        """获得某机甲战魂详细信息
        """
        return self.spirits.get(hero_id, {})

    def append_spirit(self, hero_id, spirit_id, need_save=False):
        """觉醒战魂

        Args:
            hero_id: 机甲ID
            spirit_id: 战魂id
        """
        hero_spirit_data = self.spirits.get(hero_id, {})

        spirit_data = {}
        spirit_data["exp"] = self.DEFAULT_EXP
        spirit_data["level"] = self.DEFAULT_LEVEL

        hero_spirit_data[spirit_id] = spirit_data
        self.spirits[hero_id] = hero_spirit_data

        if need_save:
            self.put()

    def add_exp(self, hero_id, spirit_id, exp):
        """战魂获得经验
        """
        spirit = self.spirits.get(hero_id).get(spirit_id)

        spirit["exp"] = spirit["exp"] + exp
        level = common_helper.get_level_by_exp(game_config.spirit_exp_level_cfg, spirit["exp"])
        if spirit["level"] != level:
            spirit["level"] = level

        self.put()

    def _reset(self):
        """重置战魂
        """
        self.spirits = {}

        self.put()
