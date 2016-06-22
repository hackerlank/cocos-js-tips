#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-20 11:13:32
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     阵列业务逻辑:
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import trial as trial_logic

ARRAY_MISSION = 1
ARRAY_ARENA = 2
ARRAY_TRIAL = 3
ARRAY_ACT_GOLD = 4
ARRAY_ACT_EXP = 5
ARRAY_ACT_FIRE = 6
ARRAY_ACT_ICE = 7
ARRAY_ACT_PHANTOM = 8

ARRAY_ACT_FIRE_LIMIT = [1,3]  # 烈焰挑战上阵机甲类型限制
ARRAY_ACT_ICE_LIMIT = [2,4] # 冰封挑战上阵机甲类型限制

# ========================= GAME API ==============================
def update(context):
    """更新阵容

    Args:
        atype: 阵容类型 [副本 | 竞技场 | 试炼 | 每日试炼活动1-4]
        array = []
    """
    ki_user = context.user

    atype = context.get_parameter("atype")
    array = context.get_parameter("array", "[]")

    try:
        array = eval(array)
        if (not isinstance(array, list)) or (len(array) != 6) or (atype not in range(1,10)):
            raise 1
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    for hero in array:
        if hero != 0 and array.count(hero) > 1:
            context.result['mc'] = MsgCode['ArrayCantRepeat']
            return

    for hero in array:
        if (hero != 0) and (hero not in ki_user.hero.heros):
            context.result['mc'] = MsgCode['HeroNotExist']
            return

    if not _act_mission_check_hero_type(atype, array):
        context.result['mc'] = MsgCode['ArrayHeroTypeError']
        return

    ki_user.array.update(atype, array)
    if atype == ARRAY_TRIAL:
        trial_logic.update_hero_states_after_array(ki_user, array)

    context.result['mc'] = MsgCode['ArraySetPositionSucc']

def _act_mission_check_hero_type(mtype, array):
    """活动副本限制上阵机甲的类型

    Args:
        mtype 活动副本类型
        array :新阵容

    """
    limits = []
    if mtype == ARRAY_ACT_FIRE:
        limits = ARRAY_ACT_FIRE_LIMIT
    elif mtype == ARRAY_ACT_ICE:
        limits = ARRAY_ACT_ICE_LIMIT
    else:
        return True

    for hero in array:
        cfg = game_config.hero_base_cfg.get(hero)
        if hero and (cfg["type"] not in limits):
            return False

    return True
