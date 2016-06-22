#!/usr/bin/env python
# encoding: utf-8

# @Date : 2015-08-24 11:20:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       游戏数据
# @end
# @copyright (C) 2015, kimech

import time

from libs.rklib.model import BaseModel

from apps.configs import game_config
from apps.logics.helpers import user_helper
from apps.logics.helpers import common_helper
from apps.services.notice import NoticeService

from apps.configs import static_const

class GameInfo(BaseModel):
    """角色游戏信息

    Attributes:
        uid   角色ID  str
        role_exp   角色经验
        role_level 角色等级
        gold     金币
        diamond   钻石
        current_energy      能量
        energe_update   能量值更新时间
        vip_exp     vip经验
        vip_level     vip等级
        honor_point   荣誉点数
        skill_point    技能点数
        talent_point   天赋点数
        trial_point    试炼点数
        group_point    帮贡
        weak_point     觉醒碎片
        box_key        宝箱钥匙
        last_guide_id   最新引导进度
    """
    ENERGY_RECOVERY_TIME = 5 * 60

    MAX_SKILL_POINT = 20

    MAX_VIP_EXP = max(game_config.vip_exp_level_cfg)
    # MAX_ROLE_EXP = max(game_config.user_exp_level_cfg)
    MAX_ROLE_EXP = 109796

    def __init__(self, uid=None):
        """初始化角色游戏信息

        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid
        self.role_exp = 0
        self.role_level = 0
        self.gold = 10000
        self.diamond = 0
        self.current_energy = 0
        self.energy_update = 0
        self.vip_exp = 0
        self.vip_level = 0

        self.fight = 0              # 玩家最强战力，最强6个机甲战力之和，战力排行榜中用到
        self.last_updated_fight = 0

        self.honor_point = 0
        # 技能点相关数据
        vip_cfg = game_config.vip_priv_cfg.get(self.vip_level)
        self.current_skill_point = 0
        self.skill_point_recover_interval = vip_cfg["skill_point_cd"]
        self.skill_point_update_time = 0

        self.talent_point = 0
        self.trial_point = 0
        self.group_point = 0
        self.weak_point = 0
        self.box_key = 0
        self.clone_point = 0

        self.last_guide_id = 0
        # 上次阅读聊天的时间，用来做私聊推送的起始时间点
        self.last_chat_read = 0
        # 上次跑马灯广播的ID，每次读取从这个值开始往后取，取了之后更新为最大的ID号
        self.broadcast_id = 0

    @classmethod
    def install(cls, uid):
        """为新角色初始安装游戏信息

        Args:
            uid: 角色ID

        Returns:
            game_info: 角色游戏信息对象实例
        """
        game_info = cls(uid)

        game_info.role_level = common_helper.get_level_by_exp(game_config.user_exp_level_cfg, game_info.role_exp)
        game_info.vip_level = common_helper.get_level_by_exp(game_config.vip_exp_level_cfg, game_info.vip_exp)

        game_info.put()

        return cls.get(uid)

    def add_role_exp(self, value, instant_save=False):
        """增加角色经验
        """
        self.role_exp = min(max(0, self.role_exp + value), self.MAX_ROLE_EXP)
        # 经验加完之后检查是否满足升级条件
        add_items = []
        after_level = common_helper.get_level_by_exp(game_config.user_exp_level_cfg, self.role_exp)
        if after_level != self.role_level:
            add_energy = 0
            for level in range(self.role_level+1, after_level+1):
                cfg = game_config.user_level_energy_cfg.get(level)
                add_energy += cfg["add_energy"]
                add_items.append(cfg["add_items"])

            self.role_level = after_level
            self.update_energy(add_energy)

        if instant_save:
            self.put()

        # 判断是否升级给了物品，为了引导任务
        return add_items

    def add_vip_exp(self, value, instant_save=False):
        """增加vip经验
        """
        self.vip_exp = min(max(0, self.vip_exp + value), self.MAX_VIP_EXP)
        # 经验加完之后检查是否满足升级条件
        tmp_vip_level = common_helper.get_level_by_exp(game_config.vip_exp_level_cfg, self.vip_exp)
        if tmp_vip_level != self.vip_level:
            self.vip_level = tmp_vip_level
            # vip等级提升之后，即时结算技能点，更新回复时间间隔
            self.update_skill_point_recover_time()

        if instant_save:
            self.put()

    def get_energy(self):
        """获取当前精力

        Returns:
            energy: 能量值
        """
        now = int(time.time())

        max_energy = 50 + 2 * (self.role_level - 1)

        # 如果当前体力已经大于上限值，则不再自然恢复体力
        if self.current_energy >= max_energy:
            self.energy_update = now
        else:
            add_energy = int(now - self.energy_update) / self.ENERGY_RECOVERY_TIME     # 计算当前增加的精力值
            self.energy_update += self.ENERGY_RECOVERY_TIME * add_energy     # 更新时间

            if self.current_energy + add_energy > max_energy:
                self.current_energy = max_energy
                self.energy_update = now
            else:
                self.current_energy += add_energy

        self.put()

        return self.current_energy

    def set_energy(self, value):
        """
        获取当前精力

        Args:
            value: 要设定的能量值
        """
        self.get_energy()
        self.current_energy = value

    # 把能量值作为property
    energy = property(get_energy, set_energy)

    def update_skill_point_recover_time(self):
        """更新技能点的回复间隔时间

        因为技能点回复间隔受vip等级影响，所以每次vip升级的时候，
        更新体力和间隔时间，以便下次计算得到正确的技能点数

        Args:
            vip_level
        """
        self.current_skill_point = self.skill_point

        vip_cfg = game_config.vip_priv_cfg.get(self.vip_level)
        self.skill_point_recover_interval = vip_cfg["skill_point_cd"]

        self.put()

    def get_skill_point(self):
        """获取当前技能点

        Returns:
            energy: 能量值
        """
        now = int(time.time())

        # 如果当前技能点已经大于上限值，则不再自然恢复技能点
        if self.current_skill_point >= self.MAX_SKILL_POINT:
            self.skill_point_update_time = now
        else:
            add_skill_point = int(now - self.skill_point_update_time) / self.skill_point_recover_interval     # 计算当前增加的技能点
            self.skill_point_update_time += self.skill_point_recover_interval * add_skill_point     # 更新时间
            if self.current_skill_point + add_skill_point > self.MAX_SKILL_POINT:
                self.current_skill_point = self.MAX_SKILL_POINT
                self.skill_point_update_time = now

            else:
                self.current_skill_point += add_skill_point

            # if self.current_skill_point + add_skill_point > self.MAX_SKILL_POINT:
            #     add_skill_point = self.MAX_SKILL_POINT - self.current_skill_point

            # if self.current_skill_point < self.MAX_SKILL_POINT:
            #     self.current_skill_point += add_skill_point
            # else:
            #     self.skill_point_update_time = now

        self.put()
        return self.current_skill_point

    def set_skill_point(self, value):
        """设置当前技能点

        Args:
            value: 要设定的技能点数量
        """
        self.get_skill_point()
        self.current_skill_point = value

    # 把能量值作为property
    skill_point = property(get_skill_point, set_skill_point)

    def update_energy(self, add_energy):
        """更新体力

        升级加体力
        购买体力
        使用体力道具

        """
        now = int(time.time())
        max_energy = 50 + 2 * (self.role_level - 1)
        if self.energy + add_energy >= max_energy:
            self.energy_update = now

        self.current_energy += add_energy

        self.put()

    def buy_skill_points(self, num):
        """购买技能点
        """
        now = int(time.time())
        if self.skill_point + num >= self.MAX_SKILL_POINT:
            self.current_skill_point = self.MAX_SKILL_POINT
            self.skill_point_update_time = now
        else:
            self.current_skill_point += num

        self.put()

    def update_fight(self, fight):
        """更新战斗力
        """
        self.fight = fight
        self.last_updated_fight = int(time.time())
        self.put()

    def increase_guide(self):
        """引导进度+1
        """
        self.last_guide_id += 1
        self.put()

    def refresh_broadcast_stamp(self):
        """
        """
        self.broadcast_id = int(time.time())
        self.put()

    def _reset(self):
        """重置数据
        """
        self.role_exp = 0
        self.role_level = 0
        self.gold = 0
        self.diamond = 0
        self.current_energy = 0
        self.energy_update = 0
        self.vip_exp = 0
        self.vip_level = 0

        self.fight = 0
        self.last_updated_fight = 0

        self.honor_point = 0
        vip_cfg = game_config.vip_priv_cfg.get(self.vip_level)
        self.current_skill_point = 0
        self.skill_point_recover_interval = vip_cfg["skill_point_cd"]
        self.skill_point_update_time = 0

        self.talent_point = 0
        self.trial_point = 0
        self.group_point = 0
        self.weak_point = 0
        self.box_key = 0
        self.clone_point = 0
        self.last_guide_id = 0

        self.put()
