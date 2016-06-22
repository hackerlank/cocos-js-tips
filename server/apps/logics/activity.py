#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-11 15:36:58
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     运营活动业务接口
# @end
# @copyright (C) 2015, kimech

import time
import copy
import random
import datetime

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

from apps.services import act as act_service

from .helpers import common_helper
from .helpers import act_helper
from .helpers import user_helper

LEVEL_FUND_DIAMOND = 1000

LEVEL_FUND_STATE_ACTIVE = 1
# ========================= GAME API ==============================
def info(context):
    """请求玩家运营活动数据信息

    Args:

    Returns:
        act_datas
    """
    ki_user = context.user

    data = {}
    data["acts_data"] = ki_user.activity.get_effective_acts(ki_user.sid, ki_user.game_info.role_level)
    data["acts_info"] = act_helper.get_active_act_info(ki_user.sid, ki_user.game_info.role_level)

    context.result["data"] = data

def info1(context):
    """请求玩家活动数据

    Args:

    Returns:
        act_datas
    """
    ki_user = context.user

    act_id = context.get_parameter("act_id")
    act_cfg = game_config.activity_cfg.get(act_id, {})

    data = {}
    if act_cfg and act_cfg["type"] in act_helper.DIAMOND_GAMBLE:
        data["records"] = act_service.get_diamond_gamble_records(ki_user.sid, act_id)
    else:
        ki_user.activity.update_effective_acts(ki_user.sid, ki_user.game_info.role_level)
        data["act_data"] = ki_user.activity.acts.get(act_id)

    context.result["data"] = data

def award(context):
    """活动领奖

    Args:
        act_id 活动ID
        index 奖项编号

    Returns:
        mc

    """
    ki_user = context.user

    act_id = context.get_parameter("act_id")
    index = context.get_parameter("index")

    if index <= 0:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    act_data = ki_user.activity.get_act_data(act_id)
    if not act_data:
        context.result['mc'] = MsgCode['ActNotExist']
        return

    server_acts = act_helper.get_active_acts(ki_user.sid, ki_user.game_info.role_level)
    if act_id not in server_acts:
        context.result['mc'] = MsgCode['ActAlreadyFinish']
        return

    if act_helper.check_award_repeat(act_id, act_data, index):
        context.result['mc'] = MsgCode['ActAlreadyAwarded']
        return

    cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, index))
    main_cfg = game_config.activity_cfg.get(act_id)

    if (not main_cfg) or (not cfg):
        context.result['mc'] = MsgCode['ActAwardFail']
        return

    if main_cfg["type"] in act_helper.SPECIAL_ACTS1:
        func = getattr(act_helper, 'act_checker_%s' % main_cfg["type"])
        # 等级基金未激活
        if main_cfg["type"] in act_helper.LEVEL_FUND_ACT and act_data["data"] != LEVEL_FUND_STATE_ACTIVE:
            context.result['mc'] = MsgCode['ActAwardNotSatisfied']
            return

        if not func(ki_user, cfg):
            context.result['mc'] = MsgCode['ActAwardNotSatisfied']
            return
    else:
        if not act_helper.check_award_can_get(act_id, act_data, index):
            context.result['mc'] = MsgCode['ActAwardNotSatisfied']
            return

        if main_cfg["type"] in act_helper.PRIVATE_SALE_ACT:
            # 每周特卖活动,检测 物品存量是否足够 元宝是否足够
            saled_num = act_service.get_private_sale_num(ki_user.sid, act_id, index)
            if saled_num >= cfg["cond_c"]:
                context.result['mc'] = MsgCode['ActAwardEmpty']
                return

            if not user_logic.check_game_values1(ki_user, diamond=cfg["cond_e"]):
                context.result['mc'] = MsgCode['DiamondNotEnough']
                return

            if ki_user.game_info.vip_level < cfg["cond_b"]:
                context.result['mc'] = MsgCode['UserVipTooLow']
                return

            act_service.update_private_sale_num(ki_user.sid, act_id, index)
            user_logic.consume_game_values1(ki_user, diamond=cfg["cond_e"]) # 扣款

    pack_logic.add_items(ki_user, cfg["awards"])
    old_data = copy.deepcopy(act_data)
    new_data = act_helper.update_after_award(act_id, old_data, index)
    ki_user.activity.update_after_award(act_id, new_data)

    # 处理相关任务
    if main_cfg["union"]:
        act_helper.update_union_acts(ki_user, main_cfg["union"], 1)

    context.result['mc'] = MsgCode['ActAwardSucc']

def buy_level_fund(context):
    """等级基金

    基金达到指定等级返利

    """
    ki_user = context.user

    act_id = context.get_parameter("act_id")

    server_acts = act_helper.get_active_acts(ki_user.sid, ki_user.game_info.role_level)
    if act_id not in server_acts:
        context.result['mc'] = MsgCode['ActAlreadyFinish']
        return

    act_data = ki_user.activity.get_act_data(act_id)
    if not act_data:
        context.result['mc'] = MsgCode['ActNotExist']
        return

    if act_data["data"] == LEVEL_FUND_STATE_ACTIVE:
        context.result['mc'] = MsgCode['ActLevelFundAlreadyActive']
        return

    if not user_logic.check_game_values1(ki_user, diamond=LEVEL_FUND_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=LEVEL_FUND_DIAMOND)
    act_helper.update_after_buy_level_fund(ki_user, LEVEL_FUND_STATE_ACTIVE)

    context.result["mc"] = MsgCode['ActBuyLevelFundSucc']

def gamble(context):
    """钻石赌博
    """
    ki_user = context.user

    act_id = context.get_parameter("act_id")
    server_acts = act_helper.get_active_acts(ki_user.sid, ki_user.game_info.role_level)
    if act_id not in server_acts:
        context.result['mc'] = MsgCode['ActAlreadyFinish']
        return

    act_data = ki_user.activity.get_act_data(act_id)
    if not act_data:
        context.result['mc'] = MsgCode['ActNotExist']
        return

    if act_data["data"] >= max(game_config.activity_gamble_cfg):
        context.result['mc'] = MsgCode['ActGambleTimesUseUp']
        return

    cfg = game_config.activity_gamble_cfg.get(act_data["data"] + 1)
    if not user_logic.check_game_values1(ki_user, diamond=cfg["need_diamond"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    A = float("%.5f" % random.random())
    B = pow((A - 0.5), 3) * cfg["arg_a"] + cfg["arg_b"]
    diamond = int((cfg["max"] - cfg["need_diamond"]) * B + cfg["need_diamond"])

    # 需要扣除的部分
    cosume_diamond = cfg["need_diamond"] - diamond
    user_logic.consume_game_values1(ki_user, diamond=cosume_diamond)
    act_helper.update_after_diamond_gamble(ki_user)

    try:
        record = {"id": ki_user.uid, "name": ki_user.name, "diamond": diamond}
        act_service.add_diamond_gamble_records(ki_user.sid, act_id, record)
    except:
        pass

    context.result["data"] = {}
    context.result["data"]["diamond"] = diamond

def online_awards(context):
    """在线礼包
    """
    ki_user = context.user

    daily = ki_user.daily_info.online_awards
    award_cfg = game_config.act_online_awards_cfg.get(daily["index"] + 1, {})
    if not award_cfg:
        context.result['mc'] = MsgCode['ActAlreadyFinish']
        return

    current_timestamp = int(time.time())
    if current_timestamp - daily["last"] < award_cfg["interval"]:
        context.result['mc'] = MsgCode['ActAwardNotSatisfied']
        return

    ki_user.daily_info.update_online_awards(current_timestamp)
    pack_logic.add_items(ki_user, award_cfg["awards"])

    context.result["mc"] = MsgCode['ActAwardSucc']
