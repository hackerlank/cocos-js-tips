#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-17 21:13:03
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     运维活动数据
# @end
# @copyright (C) 2015, kimech

import copy

from apps.configs import game_config

from libs.rklib.model import BaseModel
from apps.logics.helpers import act_helper
from apps.services import act as act_service

class Activity(BaseModel):
    """运维活动数据

    acts = {
        act_id: {}
    }

    """
    def __init__(self, uid=None):
        """初始化运维活动数据

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.acts = {}  # 活动数据,动态数据，随时检测服务器全局的活动配置更新

    def update_effective_acts(self, sid, role_level):
        """更新最新的运维活动数据
        """
        # 当前，正在进行中的活动
        valid_acts = act_helper.get_active_acts(sid, role_level)
        # 找出已经失效的活动，删除掉！！ ******  此操作慎重  ******
        _tmp = copy.deepcopy(self.acts)
        for act_id in _tmp:
            if act_id not in valid_acts:
                del self.acts[act_id]
            else:
                act_cfg = game_config.activity_cfg.get(act_id, {})
                if act_cfg["type"] in act_helper.PRIVATE_SALE_ACT:
                    self.acts[act_id]["data"] = act_service.get_all_private_sale_num(sid, act_id)

                valid_acts.remove(act_id)

        # ****************** 删除结束,增加新活动数据 *************
        # 每日走邮件发奖励的活动类型不保存其活动数据，由脚本执行
        for act_id in valid_acts:
            act_cfg = game_config.activity_cfg.get(act_id, {})
            if act_cfg and act_id not in self.acts and act_cfg["type"] not in act_helper.SPECIAL_ACTS:
                act_data = act_helper.new_act_data_from_id(act_id)
                self.acts[act_id] = act_data

        self.put()

    def get_effective_acts(self, sid, role_level):
        """获取最新的数据
        """
        self.update_effective_acts(sid, role_level)

        return self.acts

    @classmethod
    def install(cls, uid):
        """为新角色初始运维活动数据

        Args:
            uid: 角色ID
        """
        acts = cls(uid)
        acts.put()

        return cls.get(uid)

    def get_act_data(self, act_id):
        """获取活动数据

        """
        return self.acts.get(act_id, {})

    def update_after_award(self, act_id, act_data):
        """奖励领取完之后，更新活动数据

        Args:
            act_id :活动ID
            act_data :最新活动数据

        """
        self.acts[act_id] = act_data

        self.put()
