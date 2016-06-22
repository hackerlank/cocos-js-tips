#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-10 11:05:50
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     社团，帮派
# @end
# @copyright (C) 2015, kimech

import time

from apps.configs import game_config
from libs.rklib.model import BaseModel

class Group(BaseModel):
    """角色帮派社团信息

    Attributes:
        group_id
    """
    def __init__(self, uid=None):
        """初始化角色机甲信息

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.group_id = 0 # 帮派ID
        self.donate = {"tiger_exp1": 0, "tiger_exp2": 0, "bird_exp1": 0, "bird_exp2": 0} # 捐献获得经验
        self.game_data = {
                            "tiger_points": -1,         # 当前点数
                            "tiger_change_times": 0,    # 每回合中花钱改投次数
                            "tiger_best_score": 0,      # 历史最好成绩

                            "bird_best_score": 0,       # 历史最好成绩
                        }
        self.cd = 0 # 退出时间戳

        self.train_dict = {}            # 训练姬甲起始时间点 example: {100001: 1463367207}
        self.train_list = [0,0,0,-1,-1,-1,-1,-1,-1]     # 训练锁队列 example: [100001, 0, -1]  0 已开启 -1 未开启

    @classmethod
    def install(cls, uid):
        """为新角色初始安装机甲信息
        """
        group = cls(uid)
        group.put()

        return cls.get(uid)

    def join(self, group_id):
        """加入公会
        """
        self.group_id = group_id
        self.put()

    def quit(self):
        """离开公会
        """
        self.group_id = 0
        self.donate = {"tiger_exp1": 0, "tiger_exp2": 0, "bird_exp1": 0, "bird_exp2": 0}
        self.game_data = {
                            "tiger_points": -1,
                            "tiger_change_times": 0,
                            "tiger_best_score": 0,
                            "bird_best_score": 0,
                        }
        self.cd = int(time.time())
        self.put()

    def donate_game_exp(self, target, exp):
        """捐献获得公会游戏经验
        """
        if target == 2:
            self.donate["tiger_exp1"] = min(self.donate["tiger_exp1"]+exp, max(game_config.group_game_tiger_exp1_cfg))
        elif target == 3:
            self.donate["tiger_exp2"] = min(self.donate["tiger_exp2"]+exp, max(game_config.group_game_tiger_exp2_cfg))
        elif target == 4:
            self.donate["bird_exp1"] = min(self.donate["bird_exp1"]+exp, max(game_config.group_game_bird_exp1_cfg))
        elif target == 5:
            self.donate["bird_exp2"] = min(self.donate["bird_exp2"]+exp, max(game_config.group_game_bird_exp2_cfg))
        else:
            return

        self.put()

    def tiger_update(self, point, times):
        """老虎机玩法

        Args:
            times 花钱改投次数
        """
        self.game_data["tiger_points"] = point
        self.game_data["tiger_change_times"] = times

        self.put()

    def bird_update(self, process):
        """
        """
        self.game_data["bird_best_score"] = process

        self.put()

    def open_train_slot(self, slot_id):
        self.train_list[slot_id] = 0
        self.put()

    def set_express_hero(self, sid, group_id, uid, hero_id, slot_id):
        """放置新机甲的加速
        """
        old = self.train_list[slot_id]
        if old in self.train_dict:
            del self.train_dict[old]

        self.train_list[slot_id] = hero_id
        self.train_dict[hero_id] = int(time.time())

        self.put()
