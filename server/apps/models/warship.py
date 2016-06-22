#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-09-23 19:46:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      天赋数据
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config

from libs.rklib.model import BaseModel

class Warship(BaseModel):
    """天赋

    Attributes:
        uid     角色ID
        ships  战舰数据
    """

    DEFAULT_LEVEL = 1
    DEFAULT_QUALITY = 0
    DEFAULT_STAR = 0

    def __init__(self, uid=None):
        """初始化天赋信息

        ships = {
            210001: {
                "level": 1,
                "quality": 1,
                "star": 1,
                "skills": {
                    220001: 1,
                    220002: 1,
                    220003: 1,
                    220004: 1,
                },
            },

        }

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.ships = {}  # 战舰信息
        self.team = [0,0,0]    # 战舰队形

    @classmethod
    def install(cls, uid):
        """为新角色初始安装战舰信息

        Args:
            uid: 角色ID
        """
        warship = cls(uid)
        cls.create_unlock_warship(warship)
        warship.put()

        return cls.get(uid)

    def get_warship_by_id(self, ship_id):
        """获得某战舰数据
        """
        return self.ships.get(ship_id, {})

    def unlock(self, ship_id, skills, instant_save=False):
        """解锁战舰

        Args:
            ship_id: 战舰ID
        """
        ship = {}
        ship["level"] = self.DEFAULT_LEVEL
        ship["quality"] = self.DEFAULT_QUALITY
        ship["star"] = self.DEFAULT_STAR
        ship["skills"] = skills

        self.ships[ship_id] = ship

        if instant_save:
            self.put()

    def intensify(self, ship_id, level):
        """战舰升级

        Args:
            ship_id: 战舰ID
        """
        ship_info = self.ships.get(ship_id)
        ship_info["level"] = level

        self.put()

    def upgrade(self, ship_id):
        """战舰升品

        Args:
            ship_id: 战舰ID
        """
        ship_info = self.ships.get(ship_id)
        ship_info["quality"] += 1

        self.put()

    def weak(self, ship_id):
        """战舰升星

        Args:
            ship_id: 战舰ID
        """
        ship_info = self.ships.get(ship_id)
        ship_info["star"] += 1

        self.put()

    def intensify_skill(self, ship_id, skill_id):
        """战舰技能升级

        Args:
            ship_id: 战舰ID
            skill_id: 战舰技能ID
        """
        ship_info = self.ships.get(ship_id)
        ship_info["skills"][skill_id] += 1

        self.put()

    def reset_talent(self):
        """重置天赋
        """
        self.ships = {}
        self.team = [0,0,0]

        self.put()

    @staticmethod
    def create_unlock_warship(warship):
        """初建角色时开启第一艘战舰
        """
        for id, warship_data in game_config.warship_cfg.items():
            if warship_data["open_level"] == 1:
                skill_cfg_key = "%s-%s" % (id, 0)
                unlock_skills = [skill for skill in game_config.warship_weak_cfg[skill_cfg_key]["skills"] if skill]

                ship = {}
                ship["level"] = warship.DEFAULT_LEVEL
                ship["quality"] = warship.DEFAULT_QUALITY
                ship["star"] = warship.DEFAULT_STAR
                ship["skills"] = dict.fromkeys(unlock_skills, 1)

                warship.ships[id] = ship

                # 如果队伍里还有位置，直接往上扔
                team = warship.team
                if 0 in team:
                    empty_pos = team.index(0)
                    warship.team[empty_pos] = id
