#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-11 15:36:58
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     活动副本业务接口
# @end
# @copyright (C) 2015, kimech

import copy
import time
import datetime

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

from apps.services import rank as rank_service

from .helpers import user_helper
from .helpers import common_helper
from .helpers import mission_helper

MISSION_ACT_TYPE_GOLD = 1
MISSION_ACT_TYPE_EXP = 2
MISSION_ACT_TYPE_FIRE = 3
MISSION_ACT_TYPE_ICE = 4
MISSION_ACT_TYPE_PHANTOM = 5

ENTER_CD = 600
# ========================= GAME API ==============================
def info(context):
    """请求对应活动副本信息

    Args:
        mtype :活动副本类型

    Returns:
        当前排名
        今日通关次数
        对应阵容
        【金币，经验】当前累计伤害
        【金币，经验】当前已领取累计伤害奖品

    """
    ki_user = context.user

    mtype = context.get_parameter("mtype")

    data = {}
    data["rank"] = rank_service.rank(ki_user.sid, 100+mtype, ki_user.uid)
    data["past_history"] = _get_past_history(mtype, ki_user.mission.act_missions)

    if mtype == MISSION_ACT_TYPE_GOLD:
        data["last_enter"] = ki_user.mission.extra_data.get("last_gold_enter", 0)
    elif mtype == MISSION_ACT_TYPE_EXP:
        data["last_enter"] = ki_user.mission.extra_data.get("last_exp_enter", 0)
    elif mtype == MISSION_ACT_TYPE_FIRE:
        data["last_enter"] = ki_user.mission.extra_data.get("last_fire_enter", 0)
    elif mtype == MISSION_ACT_TYPE_ICE:
        data["last_enter"] = ki_user.mission.extra_data.get("last_ice_enter", 0)
    elif mtype == MISSION_ACT_TYPE_PHANTOM:
        data["last_enter"] = ki_user.mission.extra_data.get("last_boss_enter", 0)
    else:
        data["last_enter"] = 0

    daily_data = ki_user.daily_info.act_missions.get(mtype, {})
    if daily_data:
        data["used_times"] = daily_data["past_times"]
        data["daily_total_damge"] = daily_data["score"]
        data["award_index"] = daily_data["award_index"]
    else:
        data["used_times"] = 0
        data["daily_total_damge"] = 0
        data["award_index"] = []

    data["array"] = ki_user.array.get_act_array(mtype)

    context.result['data'] = data

def enter(context):
    """进入活动副本

    Args:
        mission_id :关卡ID

    Returns:

    """
    ki_user = context.user

    mission_id = context.get_parameter("mission_id")
    fight = context.get_parameter("fight")

    cfg = game_config.mission_act_base_cfg.get(mission_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['MissionNotExist']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    main_cfg = game_config.mission_act_main_cfg.get(cfg["type"])
    if not _check_mission_open(main_cfg["open_week_days"]):
        context.result['mc'] = MsgCode['MissionNotOpen']
        return

    if cfg["type"] == MISSION_ACT_TYPE_GOLD:
        last = ki_user.mission.extra_data.get("last_gold_enter", 0)
    elif cfg["type"] == MISSION_ACT_TYPE_EXP:
        last = ki_user.mission.extra_data.get("last_exp_enter", 0)
    elif cfg["type"] == MISSION_ACT_TYPE_FIRE:
        last = ki_user.mission.extra_data.get("last_fire_enter", 0)
    elif cfg["type"] == MISSION_ACT_TYPE_ICE:
        last = ki_user.mission.extra_data.get("last_ice_enter", 0)
    elif cfg["type"] == MISSION_ACT_TYPE_PHANTOM:
        last = ki_user.mission.extra_data.get("last_boss_enter", 0)
    else:
        last = 0

    if int(time.time()) - last < ENTER_CD:
        context.result['mc'] = MsgCode['MissionInCD']
        return

    if cfg["need_level"] > ki_user.game_info.role_level:
        context.result['mc'] = MsgCode['UserLevelTooLow']
        return

    if cfg["type"] in [1,2,5] and cfg["need_mission"] and cfg["need_mission"] not in ki_user.mission.act_missions:   # 金币经验通关就算
        context.result['mc'] = MsgCode['MissionCondsNotEnough']
        return
    elif cfg["type"] in [3,4] and cfg["need_mission"] and ki_user.mission.act_missions.get(cfg["need_mission"], 0) != 3:  # 烈焰冰封三星才算
        context.result['mc'] = MsgCode['MissionCondsNotEnough']
        return
    else:
        pass

    daily_data = ki_user.daily_info.act_missions
    daily_data1 = daily_data.get(cfg["type"], {})

    if daily_data1 and daily_data1["past_times"] >= main_cfg["max_times"]:
        context.result['mc'] = MsgCode['MissionTimesError']
        return

    # 战力校验
    if not user_helper.check_user_fight(ki_user, fight, cfg["type"]+3):
        context.result['mc'] = MsgCode['UserFightCheckFailed']
        return

    # 进入副本成功。更新数据
    ki_user.mission.act_enter(mission_id, cfg["type"])
    # 失败或没打完同样扣次数。防止玩家中途退出游戏
    if cfg["type"] in [MISSION_ACT_TYPE_GOLD, MISSION_ACT_TYPE_EXP, MISSION_ACT_TYPE_PHANTOM]:
        ki_user.daily_info.act_mission_enter(cfg["type"])

    context.result['mc'] = MsgCode['MissionEnterSucc']

def past(context):
    """活动副本结算

    Args:
        mission_id :关卡ID
        hurt :伤害值

    Returns:

    """
    ki_user = context.user

    mission_id = context.get_parameter("mission_id")
    hurt_percent = context.get_parameter("hurt_percent")
    hurt = context.get_parameter("hurt")
    star = context.get_parameter("star")

    if star not in range(0,4) or not hurt_percent:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cfg = game_config.mission_act_base_cfg.get(mission_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['MissionNotExist']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    extra = ki_user.mission.extra_data
    if extra.get("last_act_mission", 0) != mission_id:
        context.result['mc'] = MsgCode['MissionNotIn']
        return

    # ====================== 计算奖励 金币经验 和 烈焰冰封幻想 不同=========================
    data = {}
    add_awards = []

    if cfg["type"] in [MISSION_ACT_TYPE_GOLD, MISSION_ACT_TYPE_EXP, MISSION_ACT_TYPE_PHANTOM]:
        award_pack_list = [pack for t, pack in cfg["awards"].items() if t <= float(hurt_percent)]
        awards = [game_config.item_pack_cfg.get(id) for id in award_pack_list]
        base_awards = common_helper.handle_pack_items(awards)
        add_awards.append(base_awards)

        data["base"] = copy.copy(base_awards)
        # 金币副本，最终奖励和上阵机甲的总星级挂钩
        hero_stars = _get_fight_hero_stars(ki_user, cfg["type"])
        star_cfg = game_config.mission_act_star_award_cfg.get(hero_stars)
        data["extra"] = star_cfg[cfg["type"]]
        add_awards.append(star_cfg[cfg["type"]])
    else:
        # 随机获得物品数量
        # 输了不得奖励
        if star not in range(1,4):
            add_awards = {}
        else:
            awards_num = common_helper.weight_random(cfg["awards_num"])
            awards_lib = [{item_pack_id: weight} for item_pack_id, weight in cfg["awards"].items()]
            awards_pack_list = mission_helper.random_mission_award(awards_lib, awards_num)
            base_awards = [game_config.item_pack_cfg.get(pack_id) for pack_id in awards_pack_list]
            base_awards = common_helper.handle_pack_items(base_awards)
            add_awards.append(base_awards)
            data["base"] = base_awards

    if star in range(1,4):
        ki_user.mission.act_past(cfg["type"], mission_id, star)

    ki_user.daily_info.act_mission_past(cfg["type"], hurt, 1)

    # 增加最终物品
    pack_logic.add_items(ki_user, pack_logic.amend_goods(add_awards))

    # 更新排行榜数据
    if cfg["type"] in [MISSION_ACT_TYPE_GOLD, MISSION_ACT_TYPE_EXP]:
        rank_service.update_act_mission_rank(ki_user.sid, cfg["type"], ki_user.uid, hurt)
    else:
        if star in range(1,4):
            rank_service.update_act_mission_rank(ki_user.sid, cfg["type"], ki_user.uid, int(time.time()))

    context.result["data"] = data

def award(context):
    """金币副本和经验副本领取累计伤害奖励

    Args:
        act_mission_type :活动副本类型 经验 / 金币
        award_ids  :累计奖品索引列表 【支持一键领取】

    Returns:

    """
    ki_user = context.user

    mtype = context.get_parameter("mtype")
    award_ids = context.get_parameter("award_ids", "[]")

    try:
        award_ids = eval(award_ids)
        if not isinstance(award_ids, list):
            raise 1
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    daily_data = ki_user.daily_info.act_missions.get(mtype, {})
    if not daily_data:
        context.result['mc'] = MsgCode['MissionAwardNotSatisfied']
        return

    total_awards = []
    for index in award_ids:
        cfg_key = "%s-%s" % (mtype, index)
        cfg = game_config.mission_act_awards_cfg.get(cfg_key, {})
        if not cfg:
            context.result['mc'] = MsgCode['MissionAwardNotExist']
            return

        if cfg["need_scores"] > daily_data["score"]:
            context.result['mc'] = MsgCode['MissionAwardNotSatisfied']
            return

        if index in daily_data["award_index"]:
            context.result['mc'] = MsgCode['MissionAlreadyAwarded']
            return

        total_awards.append(cfg["awards"])

    pack_logic.add_items(ki_user, pack_logic.amend_goods(total_awards))
    ki_user.daily_info.act_mission_award(mtype, award_ids)

    context.result['mc'] = MsgCode['MissionAwardSucc']

def hangup(context):
    """冰封和烈焰副本可以扫荡

    Args:
        act_mission_type :活动副本类型 经验 / 金币

    Returns:

    """
    ki_user = context.user

    mission_id = context.get_parameter("mission_id")
    htimes = context.get_parameter("htimes")

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    cfg = game_config.mission_act_base_cfg.get(mission_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if cfg["type"] not in [MISSION_ACT_TYPE_FIRE, MISSION_ACT_TYPE_ICE]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    main_cfg = game_config.mission_act_main_cfg.get(cfg["type"])
    if htimes > main_cfg["max_times"] or htimes <= 0:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    star = ki_user.mission.act_missions.get(mission_id, 0)
    if star != 3:
        context.result['mc'] = MsgCode['MissionStarNotEnough']
        return

    daily_data = ki_user.daily_info.act_missions.get(cfg["type"], {})
    if daily_data and daily_data["past_times"] + htimes > main_cfg["max_times"]:
        context.result['mc'] = MsgCode['MissionTimesError']
        return

    awards = [cfg["awards"]] * htimes
    final_awards = common_helper.handle_pack_items(awards)

    pack_logic.add_items(ki_user, final_awards)
    ki_user.daily_info.act_mission_enter(cfg["type"], htimes)

    context.result['mc'] = MsgCode['MissionHangupSucc']

# ====================================================================
def _check_module_open(arg, role_level):
    """检测功能是否开启

    Args:
        arg :副本ID or 章节类型
        role_level :玩家等级

    Return:
        bool
    """
    cfg = game_config.mission_act_base_cfg.get(arg)
    if not cfg:
        return False

    if cfg["type"] == MISSION_ACT_TYPE_GOLD:
        func_id = 4010
    elif cfg["type"] == MISSION_ACT_TYPE_EXP:
        func_id = 4011
    elif cfg["type"] == MISSION_ACT_TYPE_FIRE:
        func_id = 4014
    elif cfg["type"] == MISSION_ACT_TYPE_ICE:
        func_id = 4015
    elif cfg["type"] == MISSION_ACT_TYPE_PHANTOM:
        func_id = 4016

    open_level = game_config.user_func_cfg.get(func_id, 999)
    if open_level > role_level:
        return False
    else:
        return True

def _check_mission_open(open_week_days):
    """检测副本今日是否开启

    Args:
        open_week_days 开放星期天数

    Return:
        bool
    """
    today = datetime.date.today()
    week_day = today.weekday() + 1

    return week_day in open_week_days

def _get_fight_hero_stars(ki_user, act_mission_type):
    """获取上阵机甲总星数

    经验 金币副本中 战利品计算使用

    """
    if act_mission_type == MISSION_ACT_TYPE_GOLD:
        array = ki_user.array.act_gold
    elif act_mission_type == MISSION_ACT_TYPE_EXP:
        array = ki_user.array.act_exp
    else:
        array = []

    total_stars = 0
    for hero_id in array:
        if hero_id:
            hero = ki_user.hero.get_by_hero_id(hero_id)
            total_stars += hero["star"]

    return total_stars

def _get_past_history(mtype, missions):
    """获取通关记录
    """
    past = []

    for mid, star in missions.items():
        cfg = game_config.mission_act_base_cfg.get(mid)
        if cfg["type"] == mtype:
            past.append({mid:star})

    return past
