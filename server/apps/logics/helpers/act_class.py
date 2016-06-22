#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-17 21:27:21
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     运维活动类
# @end
# @copyright (C) 2015, kimech

import time
import math
import datetime

from apps.misc import utils
from apps.configs import game_config

from apps.services.mail import MailService
from apps.services import act as act_service
from torngas.settings_manager import settings

class Act(object):
    """运维活动基础类
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 0, "data": 0, "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """有可以影响数据的操作之后，更新数据

        此方法只适用于最基本的活动:
            1.类似累计获得金币达到指定数量

        Args:
            act_id :活动ID
            act_data :活动数据
            data :操作数值 类如：消费xx钻石
        """
        # 更新进度
        act_data["data"] += data

        canget, awarded = act_data["canget"], act_data["awarded"]

        # 检查是否达成某几个阶段的目标
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            # 领过奖励的和已经知晓完成状态的步数上不再检测
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                if act_data["data"] >= cfg["cond_a"]:
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data

    @classmethod
    def check_award_can_get(cls, act_data, index):
        """检查奖励是否满足条件了

        Returns:
            0 / 1
        """
        # TODO 须扩展  领取时再次详细检查活动达成条件
        return utils.bit_test(act_data["canget"], index)

    @classmethod
    def check_award_repeat(cls, act_data, index):
        """检查奖励是否重复领取了
        """
        return utils.bit_test(act_data["awarded"], index)

    @classmethod
    def update_after_award(cls, act_data, index):
        """领完奖励更新状态

        """
        act_data["awarded"] = utils.bit_set(act_data["awarded"], index)
        act_data["canget"] = act_data["canget"] - utils.bit_set(0, index)

        return act_data

class ActLogin(Act):
    """登录领取类活动类

    1.登录有礼


    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 1, "data": utils.today(), "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """有可以影响数据的操作之后，更新数据

        此方法只适用于登录领取类的活动:
            1.类似好礼七天送之类的活动，登录一天领一天的东西

        Args:
            act_id :活动ID
            act_data :活动数据
            data :上次登录日期 20151118
        """
        # 判断登录日期是否相同，如果相同 则不需要更新数据了
        if act_data["data"] == data:
            return act_data
        else:
            canget, awarded = act_data["canget"], act_data["awarded"]

            # 不相同，则需要多加一次可领取的礼包步数
            new_canget = utils.bin2dec("1" + utils.dec2bin(canget+awarded))
            act_data["canget"] = int(new_canget) - awarded
            act_data["data"] = data

            return act_data

class ActLoginSendMail(Act):
    """登录发送邮件奖励活动类

    1.圣诞活动

    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """有可以影响数据的操作之后，更新数据

        此方法只适用于登录领取类的活动:
            1.类似好礼七天送之类的活动，登录一天领一天的东西

        Args:
            act_id :活动ID
            act_data :活动数据
            data :上次登录日期 20151118
        """
        # 判断登录日期是否相同，如果相同 则不需要更新数据了
        if act_data["data"] == data:
            return act_data
        else:
            canget, awarded = act_data["canget"], act_data["awarded"]

            # 不相同，则需要多加一次可领取的礼包步数
            new_canget = utils.bin2dec("1" + utils.dec2bin(canget+awarded))
            act_data["canget"] = int(new_canget) - awarded
            act_data["data"] = data

            return act_data

class ActReachStandardA(Act):
    """达标A类活动类

    备注：此类活动分几个档次，类如战力达到[1000,3000,10000,30000,70000]
         每个档次都可领取对应的奖励
         A类为数值更新 B类数值累加

    1.战斗力达到指定标准 √
    2.拥有姬甲达到指定数量
    3.达到指定级别
    4.累计获得试炼积分达到指定数量
    7.达到指定星级的姬甲达到指定数量

    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def update_after_award(cls, act_data, index):
        """领完奖励更新状态

        """
        act_data["awarded"] = utils.bit_set(act_data["awarded"], index)

        return act_data

class ActReachStandardB(Act):
    """达标类活动类

    备注：此类活动分几个档次，类如战力达到[1000,3000,10000,30000,70000]
         每个档次都可领取对应的奖励

    1.拥有指定ID姬甲（多个）
    2.累计获得金币达到指定数量
    3.累计消耗金币达到指定数量
    4.技能升级次数达到指定数量
    5.战魂升级数达到指定数量
    6.累计充值钻石达到指定数量
    7.累计消耗钻石达到指定数量
    8.开启试炼宝箱次数达到指定数量
    9.购买体力次数达到指定数量
    10.购买金币次数达到指定数量
    11.累计抽取姬甲达到指定数量
    12.累计抽取商店宝箱达到指定数量
    13.通关金币副本达到指定数量
    14.通关经验副本达到指定数量
    15.通关烈焰挑战达到指定数量
    16.通关冰封挑战达到指定数量
    17.竞技场挑战达到指定数量

    18.钻石抽取姬甲达到指定数量

    """
    def __init__(self):
        super(Act, self).__init__()

class ActPassMission(Act):
    """通关指定副本活动类

    1.通关指定副本，通关即完成 每个副本一次阶段

    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据

        Returns:
            canget 可领取状态 0111 =》 7
            past 活动期间内，通过的副本ID列表
            awarded 奖励领取ID历史

        """
        return {"canget": 0, "past": [], "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """有可以影响数据的操作之后，更新数据

        此方法只适用于通关指定副本活动:
            1.类似第一步，通关A,B两个副本，第二步，通关C,D两个副本。

        Args:
            act_id :活动ID
            act_data :活动数据
            data :通关副本ID
        """
        missions = [cfg["cond_a"] for key, cfg in game_config.act_detail_cfg.items() if key.startswith("%s-" % act_id)]

        if data not in missions:
            return act_data

        # 更新进度
        if data not in act_data["past"]:
            act_data["past"].append(data)

        canget, awarded = act_data["canget"], act_data["awarded"]

        def check_past_missions(past, cfg):
            conds = filter(lambda x: x, [cfg[attr] for attr in cfg.keys() if attr.startswith("cond_")])
            # 判断conds 是否为past的子集即可判断条件是否都已满足
            if len(set(conds).difference(past)) == 0:
                return True
            else:
                return False

        # 检查是否达成某几个阶段的目标
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            # 领过奖励的和已经知晓完成状态的步数上不再检测
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                # 完成了
                if check_past_missions(act_data["past"], cfg):
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data

class ActHaveHeros(Act):
    """获得指定机甲活动类

    1.获得指定的某几个机甲完成任务
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据

        Returns:
            canget 可领取状态 0111 =》 7
            have 当前拥有的机甲列表
            awarded 奖励领取ID历史

        """
        return {"canget": 0, "have": [], "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """有可以影响数据的操作之后，更新数据

        此方法只适用于通关指定副本活动:
            1.类似第一步，通关A,B两个副本，第二步，通关C,D两个副本。

        Args:
            act_id :活动ID
            act_data :活动数据
            data :当前获得机甲ID列表
        """
        if data == act_data["have"]:
            return act_data

        # 更新进度
        if data != act_data["have"]:
            act_data["have"] = data

        canget, awarded = act_data["canget"], act_data["awarded"]

        def check_have_heros(have, cfg):
            conds = filter(lambda x: x, [cfg[attr] for attr in cfg.keys() if attr.startswith("cond_")])
            # 判断conds 是否为have的子集即可判断条件是否都已满足
            if len(set(conds).difference(have)) == 0:
                return True
            else:
                return False

        # 检查是否达成某几个阶段的目标
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            # 领过奖励的和已经知晓完成状态的步数上不再检测
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                # 完成了
                if check_have_heros(act_data["have"], cfg):
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data

    @classmethod
    def update_after_award(cls, act_data, index):
        """领完奖励更新状态

        """
        act_data["awarded"] = utils.bit_set(act_data["awarded"], index)
        # act_data["canget"] = act_data["canget"] - utils.bit_set(0, index)

        return act_data

class ActArenaRank(Act):
    """竞技场排名10内

    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        初始名次都为20000
        """
        return {"canget": 0, "data": 20000, "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """竞技场获得更好名次

        Args:
            data :新名次
        """
        # 更新进度
        if data >= act_data["data"]:
            return act_data
        else:
            act_data["data"] = data
            canget, awarded = act_data["canget"], act_data["awarded"]

            # 检查是否达成某几个阶段的目标
            index_list = game_config.act_sample_detail_cfg.get(act_id)
            for index in index_list:
                # 领过奖励的和已经知晓完成状态的步数上不再检测
                if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                    cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                    # 完成了
                    if act_data["data"] <= cfg["cond_a"]:
                        canget = utils.bit_set(canget, index)

            act_data["canget"] = canget

            return act_data

class ActTrial(Act):
    """通关试炼指定层数&累计获得试炼积分达到指定数量

    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """通关试炼指定层数

        Args:
            data :新楼层
        """
        if data <= act_data["data"]:
            return act_data

        act_data["data"] = data
        canget, awarded = act_data["canget"], act_data["awarded"]

        # 检查是否达成某几个阶段的目标
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            # 领过奖励的和已经知晓完成状态的步数上不再检测
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                if act_data["data"] >= cfg["cond_a"]:
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data

class ActChargeAct1(Act):
    """累计充值得姬甲

    1.每日充值60领取奖品，非连续充值5日 每日达到60后 领取大奖
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 0, "data": [utils.today(), 0, 0], "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, sid, data):
        """充值成功

        Args:
            data :充值金额
        """
        date = act_data["data"][0]
        if date == utils.today() and act_data["data"][2] == 1:  # 今天已经达标
            act_data["data"][1] += data
            return act_data
        else:
            if date == utils.today():
                act_data["data"][1] += data
            else:
                act_data["data"] = [utils.today(), data, 0]

        canget, awarded = act_data["canget"], act_data["awarded"]
        next_index = int(math.log(canget + awarded + 1, 2)) + 1
        cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, next_index))
        if act_data["data"][1] >= cfg["cond_a"]:
            act_data["data"][2] = 1
            act_data["canget"] = utils.bit_set(canget, next_index)

            # 第五天充值达标 最终的大奖置为可领取
            if (act_data["canget"] + awarded + 1) == math.pow(2, max(game_config.act_sample_detail_cfg[act_id]) - 1):
                act_data["canget"] = utils.bit_set(act_data["canget"], max(game_config.act_sample_detail_cfg[act_id]))

        return act_data

class ActChargeLevelFund(Act):
    """等级基金
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 0, "data": 0, "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """激活基金

            data :基金状态
        """
        act_data["data"] = data

        return act_data

    @classmethod
    def update_after_award(cls, act_data, index):
        """领完奖励更新状态

        """
        act_data["awarded"] = utils.bit_set(act_data["awarded"], index)
        return act_data

class ActDailySale(Act):
    """每日折扣道具
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 0, "data": {}, "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, sid, data):
        """
        """
        act_info = act_service.get_act_info(sid, act_id)
        if not act_info:
            return act_data

        daydiff = (datetime.date.today() - datetime.date.fromtimestamp(act_info["start"])).days + 1

        canget, awarded = act_data["canget"], act_data["awarded"]
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
                if daydiff >= cfg["cond_a"]:
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data

class ActDiamondGamble(Act):
    """钻石赌博
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"data": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """ 更新进度
        """
        act_data["data"] += data

        return act_data

class ActComplexTargets(Act):
    """多条件达成类活动
    """
    def __init__(self):
        super(Act, self).__init__()

    @classmethod
    def new(cls):
        """初始化活动数据
        """
        return {"canget": 0, "data": [0,0,0,0,0], "awarded": 0}

    @classmethod
    def update_after_action(cls, act_id, act_data, data):
        """ 更新进度
        """
        act_data["data"][data[0]] += data[1]

        canget, awarded = act_data["canget"], act_data["awarded"]

        # 检查是否达成某几个阶段的目标
        index_list = game_config.act_sample_detail_cfg.get(act_id)
        for index in index_list:
            # 领过奖励的和已经知晓完成状态的步数上不再检测
            if utils.bit_test(canget, index) == 0 and utils.bit_test(awarded, index) == 0:
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))

                if tuple(act_data["data"]) >= (cfg["cond_a"], cfg["cond_b"], cfg["cond_c"], cfg["cond_d"], cfg["cond_e"]):
                    canget = utils.bit_set(canget, index)

        act_data["canget"] = canget

        return act_data
