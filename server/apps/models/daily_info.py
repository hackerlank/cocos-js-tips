#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-19 14:18:34
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   每日限制类数据结构
#   第二日数据刷新
# @end
# @copyright (C) 2015, kimech

import time
import datetime

from apps.misc import utils
from libs.rklib.model import BaseModel

class DailyInfo(BaseModel):
    """角色每日数据信息

    Attributes:
        uid   角色ID  str
        date   今日日期  int  20150819
        hero_pick_info   每日免费抽卡已使用次数
    """

    def __init__(self, uid=None):
        """初始化每日数据

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid
        self.date = time.strftime('%Y%m%d%H')
        self.buy_energy_times = 0
        self.buy_gold_times = 0
        self.hero_pick_info = {"gold": 0, "diamond": 1} # 金币抽卡为今日免费抽取次数， 钻石抽卡为当前是否可以抽卡 0 - 不可，1 - 可以免费抽卡
        self.mission_info = {}
        self.act_missions = {}  # 活动副本数据 {1:{"past_times": 0, "score": 45000, "award_index": []}, }
        self.world_chat_times = 0
        self.mall_pick_cd = 0
        self.mall_refresh_times = dict.fromkeys(range(1,5), 0)
        self.resign_tag = 0  # 今日是否已经补签
        self.group_info = {
            "donate_times": 0,         # 今日捐献总次数
            "tiger_time1": 0,          # 老虎机投掷次数
            "tiger_time2": 0,          # 老虎机免费改投次数

            "bird_times": 0,           # 小鸟使用次数
            "bird_daily_best": 0,      # 小鸟今日最佳
            "bird_awards": {},         # 今日已获得奖励列表
        }
        self.online_awards = {"index": 0, "last": 0} # 每日在线奖励

        self.group_train_express_times = 0    # 今日已使用训练所加速次数

        self.boss_encourage_times = 0       # 今日世界boss鼓舞次数
        self.boss_last_fight = 0            # 今日上次挑战世界boss时间戳
        self.boss_supported = ""            # 支持的玩家

    @classmethod
    def install(cls, uid):
        """初始或者重置每日数据

        Args:
            uid: 角色ID

        Returns:
            daily_info: 角色每日数据对象实例
        """
        game_info = cls(uid)
        game_info.put()

        return cls.get(uid)

    def reset_jy_mission(self, mission_id):
        """重置精英副本的次数

        Args:
            mission_id  副本ID
        """
        mission_data = self.mission_info.get(mission_id)
        mission_data["past_times"] = 0
        mission_data["reset_times"] += 1

        self.put()

    def update_mall_refresh_times(self, mtype):
        """商店刷新次数+1

        """
        if self.mall_refresh_times:
            self.mall_refresh_times[mtype] += 1
        else:
            self.mall_refresh_times = dict.fromkeys(range(1,5), 0)
            self.mall_refresh_times[mtype] += 1

        self.put()

    def act_mission_enter(self, act_mission_type, add_times=1):
        """活动副本数据【进入】

        """
        if act_mission_type not in self.act_missions:
            data = {"past_times": add_times, "score": 0, "award_index": []}
            self.act_missions[act_mission_type] = data
        else:
            self.act_missions[act_mission_type]["past_times"] += add_times

        self.put()

    def act_mission_past(self, act_mission_type, score, add_times):
        """活动副本数据【结算】
        """
        if act_mission_type not in self.act_missions:
            data = {"past_times": add_times, "score": score, "award_index": []}
            self.act_missions[act_mission_type] = data
        else:
            self.act_missions[act_mission_type]["score"] += score
            if act_mission_type not in [1,2,5]:
                self.act_missions[act_mission_type]["past_times"] += add_times

        self.put()

    def act_mission_award(self, act_mission_type, award_ids):
        """活动副本数据【领奖】

        """
        self.act_missions[act_mission_type]["award_index"] += award_ids
        self.put()

    def group_update(self, field):
        """
        """
        self.group_info[field] += 1

        self.put()

    def group_game_bird_update(self, k, value):
        """
        """
        self.group_info[k] = value

        self.put()

    def update_online_awards(self, timestamp):
        self.online_awards["index"] += 1
        self.online_awards["last"] = timestamp

        self.put()
