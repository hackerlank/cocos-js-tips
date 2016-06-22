#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-28 14:00:19
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     副本数据
# @end
# @copyright (C) 2015, kimech

import time

from apps.configs import game_config
from libs.rklib.model import BaseModel

class Mission(BaseModel):
    """副本数据

    Attributes:
        uid     # 角色ID :str
        chapters   # 章节数据  {"chapter_type-chapter_id": {"star": 0, "got_award": []}}
        missions   # 副本数据  {mission_id: {"first_award": 0, "best_award": 0, "star": 0}}

        act_missions # 活动副本数据 {}

    """
    def __init__(self, uid=None):
        """初始化副本数据

        Args:
            uid: 玩家ID
        """
        BaseModel.__init__(self)

        self.uid = uid
        self.chapters = {}
        self.missions = {}
        self.extra_data = {
                            "last_enter": 0,
                            "last_mission": 0,
                            "last_act_mission": 0,
                            "last_gold_enter": 0,
                            "last_exp_enter": 0,
                            "last_fire_enter": 0,
                            "last_ice_enter": 0,
                            "last_boss_enter": 0,
                        }

        self.act_missions = {}

    @classmethod
    def install(cls, uid):
        """为新角色初始安装副本数据

        Args:
            uid: 玩家ID

        Returns:
            mission
        """
        mission = cls(uid)
        mission.put()

        return cls.get(uid)

    def get_mission_by_id(self, mission_id):
        """根据副本id获得副本数据

        Args:
            mission_id  副本ID
        Returns:
            mission_info 单个副本数据
        """
        return self.missions.get(mission_id, {})

    def get_chapter_by_type_id(self, chapter_type, chapter_id):
        """根据章节类型和章节ID获得章节数据

        Args:
            chapter_type  章节类型
            chapter_id    章节ID
        Returns:
            chapter_info 单个副本数据
        """
        chapter_key = "%s-%s" % (chapter_type, chapter_id)

        return self.chapters.get(chapter_key, {})

    def enter(self, mission_id):
        """进入副本

        Args:
            mission_id: 进入副本ID
        """
        self.extra_data["last_enter"] = int(time.time())
        self.extra_data["last_mission"] = mission_id

        self.put()

    def act_enter(self, mission_id, atype):
        """
        """
        self.extra_data["last_act_mission"] = mission_id
        now = int(time.time())
        if atype == 1:
            self.extra_data["last_gold_enter"] = now
        elif atype == 2:
            self.extra_data["last_exp_enter"] = now
        elif atype == 5:
            self.extra_data["last_boss_enter"] = now
        else:
            pass

        self.put()

    def act_past(self, mtype, mission_id, star):
        """
        """
        if mission_id in self.act_missions:
            old = self.act_missions[mission_id]
            if star > old:
                self.act_missions[mission_id] = star
        else:
            self.act_missions[mission_id] = star

        # 冰封烈焰过关CD
        now = int(time.time())
        if mtype == 3:
            self.extra_data["last_fire_enter"] = now
        elif mtype == 4:
            self.extra_data["last_ice_enter"] = now
        else:
            pass

        self.extra_data["last_act_mission"] = 0
        self.put()

    def past(self, mission_id, star):
        """过关副本 更新副本数据

        Args:
            mission_id: 通关副本ID
            star: 通关副本星星数量
        """
        # 更新上次临时副本数据
        self.extra_data["last_enter"] = 0
        self.extra_data["last_mission"] = 0

        # 更新单个副本数据
        if mission_id not in self.missions:
            mission_data = {}
            mission_data["first_award"] = 0
            mission_data["best_award"] = 0
            mission_data["star"] = star

            chapter_add_star = star
            self.missions[mission_id] = mission_data
        else:
            old_info = self.missions.get(mission_id)
            # 如果历史记录最高是3星或者当前星星比之前少 则章节星星数量不会再随着改变
            if star > old_info["star"]:
                chapter_add_star = star - old_info["star"]
            else:
                chapter_add_star = 0

            self.missions[mission_id]["star"] = star if star > old_info["star"] else old_info["star"]

        # 更新章节数据
        cfg = game_config.mission_chapter_cfg.get(mission_id)
        chapter_key = "%s-%s" % (cfg["type"], cfg["id"])
        chapter_data = self.chapters.get(chapter_key, {})

        if not chapter_data:
            chapter_data = {}
            chapter_data["star"] = star
            chapter_data["got_award"] = []

            self.chapters[chapter_key] = chapter_data
        else:
            chapter_data["star"] += chapter_add_star

        self.put()

    def get_mission_award(self, mission_id, award_type):
        """领取副本首次通关奖励

        Args:
            mission_id: 副本ID
        """
        mission_data = self.missions.get(mission_id)
        if award_type == 1:
            mission_data["first_award"] = 1  # 改为已领取状态
        else:
            mission_data["best_award"] = 1

        self.put()

    def get_chapter_awards(self, chapter_key, index):
        """领取章节星星宝箱

        Args:
            chapter_key 章节数据Key
            index 奖品位置
        """
        chapter_data = self.chapters.get(chapter_key)
        chapter_data["got_award"].append(index)

        self.put()

    def _reset(self):
        """重置
        """
        self.chapters = {}
        self.missions = {}
        self.extra_data = {
            "last_enter": 0,
            "last_mission": 0
        }

        self.put()
