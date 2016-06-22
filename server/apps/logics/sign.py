#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-10 10:50:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      签到业务接口
# @end
# @copyright (C) 2015, kimech

import datetime

from apps.misc import utils

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import package as pack_logic

# ========================= GAME API ==============================
def sign(context):
    """签到

    Args:

    Returns:

    """
    ki_user = context.user

    this_date = utils.today()
    if this_date == ki_user.sign.last_sign:
        context.result['mc'] = MsgCode['SignAlreadyToday']
        return

    this_date1 = utils.split_date(this_date)
    cfg_key = "%s-%s-%s" % (this_date1[0], this_date1[1], ki_user.sign.month_sign_days + 1)
    sign_cfg = game_config.sign_cfg.get(cfg_key, {})

    if not sign_cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    ki_user.sign.sign(this_date)
    if ki_user.game_info.vip_level >= sign_cfg["double_vip"]:
        ki_user.daily_info.resign_tag = 1
        ki_user.daily_info.put()

    # 达到vip等级 双倍物品
    awards = {}
    if sign_cfg["double_vip"] and sign_cfg["double_vip"] <= ki_user.game_info.vip_level:
        for item, value in sign_cfg["award"].items():
            awards[item] = value * 2
    else:
        awards = sign_cfg["award"]

    pack_logic.add_items(ki_user, awards) # 加物品

    context.result['mc'] = MsgCode['SignSucc']

def award(context):
    """领取累计奖励

    Args:
        index 累计奖励项ID

    Returns:

    """
    ki_user = context.user

    index = context.get_parameter("index")
    award_cfg = game_config.sign_award_cfg.get(index, {})

    if not award_cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if index <= ki_user.sign.last_award_index:
        context.result['mc'] = MsgCode['SignAlreadyAwarded']
        return

    if award_cfg["need_sign_days"] > ki_user.sign.total_sign_days:
        context.result['mc'] = MsgCode['SignDaysNotEnough']
        return

    ki_user.sign.award(index)
    pack_logic.add_items(ki_user, award_cfg["award"]) # 加物品

    context.result['mc'] = MsgCode['SignAwardSucc']

def resign(context):
    """vip等级足够  补签

    Args:

    Returns:

    """
    ki_user = context.user

    this_date = utils.today()
    # 今日还没签  不能补签
    if this_date != ki_user.sign.last_sign:
        context.result['mc'] = MsgCode['SignNotToday']
        return

    # 已经补签过了
    if ki_user.daily_info.resign_tag == 1:
        context.result['mc'] = MsgCode['SignAlreadyToday']
        return

    this_date1 = utils.split_date(this_date)
    cfg_key = "%s-%s-%s" % (this_date1[0], this_date1[1], ki_user.sign.month_sign_days)
    sign_cfg = game_config.sign_cfg.get(cfg_key)

    if sign_cfg["double_vip"] == 0:
        context.result['mc'] = MsgCode['SignCantResignToday']
        return

    if sign_cfg["double_vip"] > ki_user.game_info.vip_level:
        context.result['mc'] = MsgCode['UserVipTooLow']
        return

    # 更新补签标记
    ki_user.daily_info.resign_tag = 1
    ki_user.daily_info.put()

    pack_logic.add_items(ki_user, sign_cfg["award"]) # 加物品

    context.result['mc'] = MsgCode['SignSucc']
