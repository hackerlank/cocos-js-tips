#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-14 15:28:09
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     竞技场数据模块
# @end
# @copyright (C) 2015, kimech

import time

from apps.misc import utils
from apps.configs import game_config
from libs.rklib.model import BaseModel
from apps.services.arena import ArenaService

class Arena(BaseModel):
    """角色竞技场数据

    Attributes:
        uid        # 角色ID   :str
    """

    def __init__(self, uid=None):
        BaseModel.__init__(self)

        self.uid = uid              # 角色ID
        self.max_rank = 0           # 历史最高排名
        self.win_times = 0          # 胜场次数
        self.last_fight = 0         # 上次挑战时间戳
        self.awarded_index = []     # 排名奖励已经领取过的编号
        self.effective_fighters = []# 有效4名对手列表
        self.fight = 0              # 竞技场战力, 竞技场阵容中机甲战力之和

        self.daily_update = time.strftime('%Y%m%d%H') # 上次刷新日期
        self.daily_challenge_times = 0    # 今日挑战次数
        self.daily_add_times = 0          # 今日购买挑战次数
        self.daily_refresh_times = 0      # 今日“换一批”次数
        self.daily_scores = 0             # 今日获得积分数
        self.daily_awarded_index = []     # 每日积分奖励领取状态
        self.daily_admire_list = []       # 今日膜拜对手【只限竞技场前10名】

        # 心跳协议中使用的签署时间，每开一次竞技场。更新此时间，心跳中需要发送的消息筛选以此为准
        self.extra_data = {"heartbeat_last_sign": int(time.time())}

    @classmethod
    def install(cls, uid):
        """给新角色装配竞技场数据
        """
        # # 加入到竞技场中
        # from apps.services.arena import ArenaService
        # ArenaService.enter(sid, uid)

        arena = cls(uid)
        arena.put()

        return cls.get(uid)

    def init_when_install(self, sid):
        """
        """
        ArenaService.enter(sid, self.uid)
        self.max_rank = ArenaService.get_user_rank(sid, self.uid)
        self.put()

    def put_fighters(self, fighters):
        """保存对手名单
        """
        self.effective_fighters = fighters
        self.put()

    def update_fighters(self, changed_rank, new_fighter):
        """更新变更过的对手数据
        """
        if not new_fighter:
            return

        f_ranks = [fighter["rank"] for fighter in self.effective_fighters]
        for index, rank in enumerate(f_ranks):
            if rank == changed_rank:
                self.effective_fighters[index] = new_fighter
                self.put()
                break

    def challenge(self, now, result):
        """挑战
        """
        self.last_fight = now
        self.daily_challenge_times += 1
        add_scores = 2 if result else 1  # 输了得一分 赢了得两分
        self.daily_scores += add_scores

        self.put()

    def win(self, new_rank, new_fighters):
        """
        """
        self.win_times += 1  # 加一个胜场
        self.effective_fighters = new_fighters  # 更新对手列表
        if not self.max_rank or (new_rank < self.max_rank):
            self.max_rank = new_rank

        self.put()

    def refresh(self, fighters):
        """  “换一批”
        """
        self.daily_refresh_times += 1
        self.effective_fighters = fighters

        self.put()

    def admire(self, admire_id):
        """记录膜拜对象
        """
        self.daily_admire_list.append(admire_id)
        self.put()

    def clean_cd(self):
        """清除CD
        """
        self.last_fight = 0
        self.put()

    def add_times(self):
        """购买挑战次数
        """
        self.daily_add_times += 1
        self.put()

    def award(self, index):
        """领取排名奖励
        """
        self.awarded_index.append(index)
        self.put()

    def daily_award(self, index):
        """领取每日积分奖励
        """
        self.daily_awarded_index.append(index)
        self.put()

    def update_fight(self, fight):
        """更新竞技场阵容战力
        """
        self.fight = fight
        self.put()

    def daily_reset(self):
        """每天早晨五点，重置每日数据
        """
        self.daily_update = time.strftime('%Y%m%d%H')
        self.daily_challenge_times = 0
        self.daily_add_times = 0
        self.daily_refresh_times = 0
        self.daily_scores = 0
        self.daily_awarded_index = []
        self.daily_admire_list = []

        self.put()

    # def update_heartbeat_sign(self):
    #     """更新心跳签署时间
    #     """
    #     self.extra_data["heartbeat_last_sign"] = int(time.time())
    #     self.put()

    def _reset(self):
        """重置
        """
        self.win_times = 0
        self.awarded_index = []
        self.max_rank = 0
        self.last_fight = 0

        self.daily_challenge_times = 0
        self.daily_add_times = 0
        self.daily_refresh_times = 0
        self.daily_scores = 0
        self.daily_awarded_index = []
        self.daily_admire_list = []

        self.put()
