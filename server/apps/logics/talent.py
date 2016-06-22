#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-21 15:46:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   技能业务逻辑接口
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic

TALENT_MAX_LEVEL = 10
TALENT_RESET_DIAMOND = 500

# ========================= GAME API ==============================
def intensify(context):
    """升级天赋

    Args:
        talent_id 天赋ID

    Returns:

    """
    ki_user = context.user
    talent_id = context.get_parameter("talent_id")

    cfg = game_config.talent_detail_cfg.get(talent_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['TalentNotExist']
        return

    if not user_logic.check_game_values1(ki_user, role_level=cfg["need_level"]):
        context.result['mc'] = MsgCode['TalentUserLevelLimit']
        return

    for front, lv in cfg["need_front"].iteritems():
        talent_level = ki_user.talent.get_talent_by_id(front)
        if lv > talent_level:
            context.result['mc'] = MsgCode['TalentFrontNotSatisfied']
            return

    current_level = ki_user.talent.get_talent_by_id(talent_id)
    if current_level >= TALENT_MAX_LEVEL:
        context.result['mc'] = MsgCode['TalentMaxLevel']
        return

    need_items = cfg["intensify_consume"].get(current_level+1, {})
    if not user_logic.check_game_values(ki_user, need_items):
        context.result['mc'] = MsgCode['TalentCondsNotEnough']
        return

    user_logic.consume_game_values(ki_user, need_items)
    ki_user.talent.intensify(talent_id)

    context.result['mc'] = MsgCode['TalentIntensifySucc']

def reset(context):
    """重置所有天赋

    Args:

    Returns:

    """
    ki_user = context.user

    if not user_logic.check_game_values1(ki_user, diamond=TALENT_RESET_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    all_talents = ki_user.talent.talents
    total_talent_point = 0
    for talent_id, level in all_talents.items():
        cfg = game_config.talent_detail_cfg.get(talent_id)
        for l in range(level):
            consume = cfg["intensify_consume"][l+1]
            total_talent_point += consume[10]

    # 返回技能点
    user_logic.add_game_values(ki_user, {10: total_talent_point})
    ki_user.talent.reset_talent()

    context.result['mc'] = MsgCode['TalentResetSucc']
