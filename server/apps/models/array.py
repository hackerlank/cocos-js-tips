#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   玩家布阵数据
# @end
# @copyright (C) 2015, kimech

from libs.rklib.model import BaseModel

class Array(BaseModel):
    """角色阵列信息

    Attributes:
        uid        # 角色ID   :str
        mission    # 副本排阵信息  :list
        arena      # 竞技场排阵信息  :list

        # 日常试炼
        act1       # 活动1排阵信息  :list
        act2       # 活动2排阵信息  :list
        act3       # 活动3排阵信息  :list
        act4       # 活动4排阵信息  :list
    """

    MAPPING = {
                1: "mission",
                2: "arena",
                3: "trial",
                4: "act_gold",
                5: "act_exp",
                6: "act_fire",
                7: "act_ice",
                8: "act_phantom",
                9: "worldboss",
            }

    def __init__(self, uid=None):
        """
        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID

        self.mission = [0]*6
        self.mission_fight = 0

        self.arena = [0]*6
        self.arena_fight = 0

        self.trial = [0]*6
        self.trial_fight = 0

        self.act_gold = [0]*6
        self.act_gold_fight = 0

        self.act_exp = [0]*6
        self.act_exp_fight = 0

        self.act_fire = [0]*6
        self.act_fire_fight = 0

        self.act_ice = [0]*6
        self.act_ice_fight = 0

        self.act_phantom = [0]*6
        self.act_phantom_fight = 0

        self.worldboss = [0]*6
        self.worldboss_fight = 0

    @classmethod
    def install(cls, uid):
        """
        Args:
            uid: 角色ID

        Returns:
            info: 角色阵列信息对象实例

        """
        array = cls(uid)
        array.put()

        return cls.get(uid)

    def update(self, atype, array):
        """玩家摆放阵型

        Args:
            atype  阵容类型
            array  新阵容
        """
        exec("self.%s = %s" % (self.MAPPING[atype], array))
        self.put()

    def get_act_array(self, mtype):
        """获取玩家活动副本的阵容数据

        金币副本 、 经验副本  如果阵容为空  使用默认

        Args:
            mtype 阵容类型
        """
        if mtype == 1:
            if self.act_gold == [0]*6:
                self.act_gold = self.mission
                self.put()

            return self.act_gold

        elif mtype == 2:
            if self.act_exp == [0]*6:
                self.act_exp = self.mission
                self.put()

            return self.act_exp

        elif mtype == 3:
            return self.act_fire
        elif mtype == 4:
            return self.act_ice
        elif mtype == 5:
            if self.act_phantom == [0]*6:
                self.act_phantom = self.mission
                self.put()

            return self.act_phantom
        else:
            return []

    def get_arena_array(self):
        """获取玩家竞技场阵容数据
        """
        if self.arena == [0]*6:
            self.arena = self.mission
            self.put()

        return self.arena

    def get_trial_array(self):
        if self.trial == [0]*6:
            self.trial = self.mission
            self.put()

        return self.trial

    def get_worldboss_array(self):
        if self.worldboss == [0]*6:
            self.worldboss = self.mission
            self.put()

        return self.worldboss

    def update_fight(self, atype, fight):
        """
        """
        exec("self.%s_fight = %s" % (self.MAPPING[atype], fight))

        self.put()
