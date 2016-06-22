#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 11:10:29
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   装备数据model
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config

from libs.rklib.model import BaseModel

from apps.logics.helpers import equip_helper
from apps.logics.helpers import common_helper

class Equip(BaseModel):
    """装备信息

    {
        hero_id1: {
                    position1: {"equip_id": 150000, "exp": 0, "level": 1, "quality": 1, "star": 1},
                    position2: {"equip_id": 150000, "exp": 0, "level": 1, "quality": 1, "star": 1},

                    position5: {"equip_id": 150000, "exp": 1000, "level": 1, "quality": 1, "star": 1},
                    position6: {"equip_id": 150000, "exp": 1000, "level": 1, "quality": 1, "star": 1},
                },
    }

    Attributes:
        uid             str     角色ID
        equips     dict    机甲穿戴装备

    """

    DEFAULT_EXP = 0
    DEFAULT_LEVEL = 1
    DEFAULT_QUALITY = 0
    DEFAULT_STAR = 0

    MAX_EXP = max(game_config.equip_exp_level_cfg)

    def __init__(self, uid=None):
        """初始化装备信息

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid                              # 玩家ID
        self.equips = {}                            # 装备信息

    @classmethod
    def install(cls, uid):
        """为新角色初始安装装备信息

        Args:
            uid: 角色ID

        Returns:
            equip: 角色装备信息对象实例
        """
        equip = cls(uid)
        equip.put()

        return cls.get(uid)

    def add_hero(self, hero_id, hero_equips, instant_save=False):
        """新增装备

        Args:
            hero_id
            hero_equips 机甲携带的装备 {1:100001, 2:100003, ..., 6:100005}
            instant_save: 即时存储
        """
        hero_equip_data = {}

        for pos, equip_id in hero_equips.iteritems():
            equip_data = {}

            equip_data["equip_id"] = equip_id
            equip_data["exp"] = self.DEFAULT_EXP
            equip_data["level"] = self.DEFAULT_LEVEL
            equip_data["quality"] = self.DEFAULT_QUALITY
            equip_data["star"] = self.DEFAULT_STAR

            hero_equip_data[pos] = equip_data

        self.equips[hero_id] = hero_equip_data

        if instant_save:
            self.put()

    def get_by_hero_id(self, hero_id):
        """返回某机甲数据

        Args:
            hero_id 机甲编号

        Returns:
            某机甲的装备数据，dict
        """
        return self.equips.get(hero_id, {})

    def get_by_hero_position(self, hero_id, position):
        """返回某装备数据

        Args:
            hero_id 机甲ID
            position 装备部位

        Returns:
            某装备数据，dict
        """

        return self.equips.get(hero_id, {}).get(position, {})

    def intensify(self, hero_id, position, level, exp=0):
        """升级强化装备

        Args:
            机甲ID
            装备位置
            value 提升数值
                if position in [1,2,3,4]:
                    value = 2(等级)
                else:
                    value = +100(经验)
        """
        equip = self.equips.get(hero_id).get(position)

        if position in [1,2,3,4]:
            equip["level"] = level
        else:
            equip["exp"] = min(max(0, exp), self.MAX_EXP)
            equip["level"] = level

        self.put()

    def upgrade(self, hero_id, position):
        """提升品质

        Args:
            hero_id 机甲ID
            position 装备部位

        Returns:

        """
        equip = self.equips.get(hero_id).get(position)
        equip["quality"] += 1

        self.put()

    def weak(self, hero_id, position):
        """提升星级

        Args:
            hero_id 机甲ID
            position 装备部位

        Returns:

        """
        equip = self.equips.get(hero_id).get(position)
        equip["star"] += 1

        self.put()

    def anti_weak(self, hero_id, position):
        """降星

        Args:
            hero_id 机甲ID
            position 装备部位

        Returns:

        """
        equip = self.equips.get(hero_id).get(position)
        equip["star"] -= 1

        self.put()

    def _reset(self):
        """重置
        """
        self.equips = {}

        self.put()
