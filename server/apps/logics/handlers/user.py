#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#
# @end
# @copyright (C) 2015, kimech

import time
import logging

from ..helpers import user_helper
from ..helpers import hero_helper
from ..helpers import act_helper
from apps.configs import game_config

from apps.services import rank as rank_service
from apps.services.statistics import Statictics as stat_service

from apps.logics import warship as warship_logic

# 更新战力的时间间隔，暂定10s
UPDATE_FIGHT_INTERVAL = 600

def pre_user_info_checker(context):
    context.data['before_level'] = context.user.game_info.role_level
    context.data['before_fight'] = context.user.game_info.fight

    # 更新玩家引导进度
    _update_user_guide(context)

def post_user_info_checker(context):
    """

    玩家（战队）等级提升之后
        1. 检测是否解锁战舰
        2. 检测是否更新战力

    """
    ki_user = context.user

    # 日志统计玩家升级状况
    try:
        before_level = context.data['before_level']
        if ki_user.game_info.role_level != before_level:
            stat_service.level(ki_user)
    except Exception,e:
        logging.error(e)

    _check_unlock_warship(context, ki_user)
    _check_update_fight(ki_user)
    # 改为领取奖励时去判断
    # _check_act_update(context, ki_user)

    # kernel_values = {}
    # kernel_values["gold"] = ki_user.game_info.gold
    # kernel_values["diamond"] = ki_user.game_info.diamond
    # # kernel_values["role_exp"] = ki_user.game_info.role_exp

    # kernel_values["exp_items"] = {}
    # for item_id in range(120000, 120006):
    #     kernel_values["exp_items"][item_id] = ki_user.package.items.get(item_id, 0)

    # context.result["kernel_values"] = kernel_values

# ============================================================================
def _update_user_guide(context):
    """更新玩家引导流程
    """
    method = context.get_parameter("method")

    guide_apis = [info["api"] for guide, info in game_config.guide_main_cfg.items()]
    if method not in guide_apis:
        return  # 不会触发引导的操作，略过

    ki_user = context.user
    last_guide = ki_user.game_info.last_guide_id
    if last_guide >= max(game_config.guide_main_cfg.keys()):
        return  # 所有引导都已完成，略过

    next_guide_cfg = game_config.guide_main_cfg.get(last_guide + 1, {})
    if not next_guide_cfg:
        return

    # 检查引导所需要的条件，若都满足，则完成此次引导
    if next_guide_cfg["api"] == method:
        if method == "mission.past":     # 挑战副本有好几次，所以特殊处理下
            mission_id = context.get_parameter("mission_id")
            if mission_id == next_guide_cfg["target"]:
                ki_user.game_info.increase_guide()
        else:
            ki_user.game_info.increase_guide()

        # 统计玩家的引导情况
        try:
            if ki_user.game_info.last_guide_id != last_guide:
                stat_service.guide(ki_user)
        except Exception, e:
            logging.error(e)

def _check_unlock_warship(context, ki_user):
    """检测是否解锁战舰
    """
    before_level = context.data['before_level']
    after_level = ki_user.game_info.role_level

    if after_level > before_level:
        for ship_id, ship_cfg in game_config.warship_cfg.items():
            if after_level >= ship_cfg["open_level"] and ship_id not in ki_user.warship.ships:
                warship_logic.unlock_ship(ki_user, ship_id)

def _check_update_fight(ki_user):
    """检测是否更新战力

    战力更新间隔为10min
    """
    now = int(time.time())

    array_fight, arena_fight = 0, 0
    if now - ki_user.game_info.last_updated_fight <= UPDATE_FIGHT_INTERVAL:
        return

    # 计算竞技场战力时，如果竞技场战力为空  则选择副本阵容计算战力
    arena_array = ki_user.array.mission if ki_user.array.arena == [0]*6 else ki_user.array.arena
    hero_fights = {}
    for hero_id in set(ki_user.array.mission + arena_array):
        if not hero_id:
            continue

        fight = hero_helper.count_array_fight(hero_id, ki_user)
        hero_fights[hero_id] = fight

        array_fight += fight if hero_id in ki_user.array.mission else 0
        arena_fight += fight if hero_id in arena_array else 0

        rank_service.update_rank(ki_user.sid, rank_service.RANK_HERO, "%s_%s" % (ki_user.uid, hero_id), fight)  # 姬甲排行榜

    ki_user.hero.update_fight(hero_fights) # 更新副本+竞技场战斗力
    ki_user.game_info.update_fight(array_fight) # 更新副本阵容战力
    ki_user.arena.update_fight(arena_fight) # 更新竞技场阵容战力
    ki_user.array.update_fight(1, array_fight)
    ki_user.array.update_fight(2, arena_fight)

    # 更新排序数据表中的信息
    rank_service.update_rank(ki_user.sid, rank_service.RANK_FIGHT, ki_user.uid, array_fight)
    rank_service.update_rank(ki_user.sid, rank_service.RANK_ARENA_FIGHT, ki_user.uid, arena_fight)

# def _check_act_update(context, ki_user):
#     """检查运维活动数据是否更新

#     改为 # 领取奖励的时候去判断
#     """
#     before_level = context.data['before_level']
#     after_level = ki_user.game_info.role_level

#     if after_level > before_level:
#         ki_user.activity.update_effective_acts(ki_user.sid, after_level)
#         act_helper.update_after_level_up(ki_user, after_level)

#     before_fight = context.data['before_fight']
#     after_fight = ki_user.game_info.fight

#     if after_fight > before_fight:
#         # 检查运维活动数据是否更新
#         act_helper.update_after_update_fight(ki_user, after_fight)

#     **************************** 改为CRONTAB任务 ************************** #

#     最后一类特殊活动
#     截止到活动配置的结束时间点，清算玩家的战斗力在排行中的情况，根据玩家的排行发送奖励，走邮件
#     now = int(time.time())
#     if now - ki_user.game_info.last_updated_fight > UPDATE_FIGHT_INTERVAL:
#         rank = rank_service.rank(ki_user.sid, 1, ki_user.uid)
#         act_helper.update_after_rank(ki_user, rank)
