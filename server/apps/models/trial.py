#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-19 18:46:09
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      试炼数据model
# @end
# @copyright (C) 2015, kimech

import time
import random

from apps.misc import utils
from apps.configs import game_config
from libs.rklib.model import BaseModel

from apps.logics.helpers import trial_helper

PROCESS_FIGHT = 1
PROCESS_BUFF = 2
PROCESS_BOX = 3

class Trial(BaseModel):
    """角色试炼数据

    Attributes:
        uid        # 角色ID   :str
    """

    def __init__(self, uid=None):
        BaseModel.__init__(self)

        self.uid = uid                   # 角色ID
        self.daily_yesterday_max = 0     # 昨日爬到的最高层数，用来计算哪些战斗层数可以跳过
        self.history_scores = 0          # 历史积分
        self.awarded_index = []          # 领取奖励列表

        self.daily_update = 0            # 上次刷新日期
        self.daily_scores = 0            # 今日目前获得积分

        self.daily_fighters = {}         # 今日匹配到的对手目标
        self.daily_buffs = {}            # 今日随机到的buff层数据. {1: [12001,12003], 2: [13001]}
        self.daily_awards = {}           # 今日随机到的物品层数据. {1: {item_id: item_num, item_id2: item_num2}, 2: {}}
        self.stars = 0                   # 今日积累的总星星数量

        self.daily_bought_buffs = {}     # 今日已购买到的buff列表 {1:[buff_id], 2:[]}
        self.daily_current_process = 1   # 今日当前爬到的层数
        self.daily_hero_states = {}      # 记录玩家今日被换下阵的机甲的状态 {hero_id: 血量百分比, }

        self.tmp_current_fighter = 0     # 玩家选择的对手
        self.tmp_fighter_states = {}     # 当前战斗层阵容状态 {hero_id: 血量百分比, }
        self.tmp_box_counter = 0         # 某一层开箱子计数器

    @classmethod
    def install(cls, uid):
        """给新角色装配竞技场数据
        """
        trial = cls(uid)
        trial.put()

        return cls.get(uid)

    def update_position(self, hero_id, position):
        """
        """
        if hero_id in self.array:
            old_pos = self.array.index(hero_id)
            self.array[old_pos], self.array[position-1] = self.array[position-1], self.array[old_pos]
        else:
            self.array[position-1] = hero_id
            self.daily_hero_states[hero_id] = 1   # 加入血量列表中

        self.put()

    def initial_daily_fighters(self, sid, uid, heros):
        """初始化今日的对手数据
        """
        fighters = trial_helper.initial_daily_fighters(sid, uid, heros)

        self.daily_fighters = fighters
        self.put()

    def match_fighters(self, process, sid, uid, heros):
        """匹配对手数据
        """
        if process in self.daily_fighters:
            return self.daily_fighters[process]
        else:
            fighters = trial_helper.match_daily_fighters(sid, uid, heros, process)
            # 新层，保存并返回
            self.daily_fighters[process] = fighters
            self.put()

            return fighters

    def chose_fighter(self, fighter):
        """更新挑选的对手
        """
        self.tmp_current_fighter = fighter
        self.put()

    def award(self, index):
        """领取排名奖励
        """
        self.awarded_index.append(index)
        self.put()

    def incr_award_counter(self):
        """
        """
        self.tmp_box_counter += 1
        self.put()

    def add_scores_and_stars(self, scores, stars):
        """
        """
        self.daily_scores += scores
        self.stars += stars

        self.put()

    def update_next_content(self, process, ptype, content):
        """更新下一层的内容
        """
        if ptype == PROCESS_BUFF:
            self.daily_buffs[process] = content
        elif ptype == PROCESS_BOX:
            self.daily_awards[process] = content
        else:
            pass

        self.tmp_current_fighter = 0
        self.tmp_box_counter = 0
        self.tmp_fighter_states = {}

        self.daily_current_process = process
        self.put()

    def daily_reset(self):
        """每天早晨五点，重置每日数据
        """
        self.daily_update = time.strftime('%Y%m%d%H')

        # 每日的积分更新之前，按8%的比例折算
        self.history_scores += self.daily_scores
        # 每日楼层刷新前，把当前层数保留 用于计算可跳过层数
        self.daily_yesterday_max = self.daily_current_process

        self.stars = 0
        self.daily_scores = 0

        self.daily_fighters = {}
        self.daily_buffs = {}
        self.daily_awards = {}

        self.daily_bought_buffs = {}
        self.daily_current_process = 1
        self.daily_hero_states = {}

        self.tmp_current_fighter = 0
        self.tmp_fighter_states = {}
        self.tmp_box_counter = 0

        self.put()
