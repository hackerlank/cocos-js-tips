#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      英雄(卡牌)数据model:
#        英雄数值: [等级,星级,战斗力,品质,
# @end
# @copyright (C) 2015, kimech

from libs.rklib.model import BaseModel

class Hero(BaseModel):
    """角色机甲信息

    Attributes:
        uid     # 角色ID :str
        heros   # 机甲信息 :dict
        pick_info 抽卡信息
            cd 上次免费抽卡时间戳
            free_times 每日使用的免费抽卡次数
            pick_times 钻石单次抽卡次数，满十之后必得卡牌

    """
    DEFAULT_EXP = 0
    DEFAULT_LEVEL = 1
    DEFAULT_QUALITY = 0

    def __init__(self, uid=None):
        """初始化角色机甲信息

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.heros = {}  # 机甲信息
        self.pick_info = {
            "gold_cd": 0,
            "diamond_pick_times": 0,
            "diamond_ten_times": 0,
        }

    @classmethod
    def install(cls, uid):
        """为新角色初始安装机甲信息
        """
        hero = cls(uid)
        hero.put()

        return cls.get(uid)

    def add_hero(self, hero_id, star=0, need_save=False):
        """增加机甲
        """
        hero_data = {}
        hero_data['hero_id'] = hero_id
        hero_data['exp'] = self.DEFAULT_EXP
        hero_data['level'] = self.DEFAULT_LEVEL
        hero_data['star'] = star
        hero_data['quality'] = self.DEFAULT_QUALITY
        hero_data['favor'] = 0
        hero_data['marry_id'] = 0
        hero_data['fight'] = 0

        self.heros[hero_id] = hero_data

        if need_save:
            self.put()

    def add_favor(self, hero_id, favor):
        """增加机甲好感度
        """
        hero = self.heros.get(hero_id)
        hero["favor"] += favor

        self.put()

    def marry(self, hero_id, marry_id):
        """许誓言
        """
        hero = self.heros.get(hero_id)
        hero["marry_id"] = marry_id

        self.put()

    def divorce(self, hero_id):
        """解除誓约
        """
        hero = self.heros.get(hero_id)
        hero["marry_id"] = 0

        self.put()

    def get_by_hero_id(self, hero_id):
        """根据hero_id获得卡牌数据
        """
        return self.heros.get(hero_id, {})

    def update_exp_level(self, hero_id, new_exp, new_level, instant_save=True):
        """给单个英雄加经验
        """
        hero = self.heros.get(hero_id)
        hero["exp"] = new_exp
        hero["level"] = new_level

        if instant_save:
            self.put()

    def update_hero_star(self, hero_id):
        """英雄提升星级
        """
        hero = self.heros.get(hero_id)
        hero["star"] += 1

        self.put()

    def update_quality(self, hero_id):
        """给单个英雄提升品质
        """
        hero = self.heros.get(hero_id)
        hero["quality"] += 1

        self.put()

    def get_max_fight_hero(self):
        """返回机甲详情
        """
        if len(self.heros):
            hero = max([(i["fight"], i["hero_id"]) for i in self.heros.values()])
            return hero[1]
        else:
            return 0

    def update_fight(self, fights):
        """更新当前副本阵容+竞技场上机甲数据
        """
        for hid in fights:
            self.heros[hid]["fight"] = fights[hid]

        self.put()

    def _reset(self):
        """重置数据
        """
        self.heros = {}
        self.pick_info = {
            "gold_cd": 0,
            "diamond_pick_times": 0,
            "diamond_ten_times": 0,
        }

        self.put()
