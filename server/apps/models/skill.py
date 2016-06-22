#!/usr/bin/env python
# encoding: utf-8

# @Date : 2015-08-24 11:20:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   技能数据
# @end
# @copyright (C) 2015, kimech

import time

from apps.configs import game_config
from libs.rklib.model import BaseModel

class Skill(BaseModel):
    """技能

    Attributes:
        uid     角色ID
        skills   技能信息
    """

    DEFAULT_LEVEL = 1

    def __init__(self, uid=None):
        """初始化角色机甲技能信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.skills = {}  # 机甲技能信息

    @classmethod
    def install(cls, uid):
        """为新角色初始安装机甲技能信息

        Args:
            uid: 角色ID
        """
        skill = cls(uid)
        skill.put()

        return cls.get(uid)

    def append_skill(self, hero_id, skill_id, need_save=False):
        """学习技能

        Args:
            hero_id: 机甲ID
            skill_id: 技能id
        """
        hero_skill_data = self.skills.get(hero_id, {})
        hero_skill_data[skill_id] = self.DEFAULT_LEVEL

        self.skills[hero_id] = hero_skill_data

        if need_save:
            self.put()

    def replace_skill(self, hero_id, old, new):
        """替换技能

        Args:
            old: 旧技能ID
            new: 新技能id
        """
        hero_skill_data = self.skills.get(hero_id, {})
        if old in hero_skill_data:
            level = hero_skill_data[old]
            del hero_skill_data[old]
            hero_skill_data[new] = level

        self.skills[hero_id] = hero_skill_data

        self.put()

    def get_skills_by_hero_id(self, hero_id):
        """获得某机甲技能详细信息
        """
        return self.skills.get(hero_id, {})

    def intensify(self, hero_id, skill_id, level):
        """技能升级
        """
        self.skills[hero_id][skill_id] += level

        self.put()

    def _reset(self):
        """重置技能
        """
        self.skills = {}  # 技能信息

        self.put()
