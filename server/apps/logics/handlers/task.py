#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-13 11:10:29
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   任务监测处理
# @end
# @copyright (C) 2015, kimech

import copy
from apps.misc import utils

from apps.configs import static_const

from apps.configs import game_config
from apps.logics.helpers import task_helper
from apps.logics.helpers import act_helper

def pre_task_info_checker(context):
    # 任务数据的前处理
    ki_user = context.user

    context.data["before_level"] = ki_user.game_info.role_level
    context.data["before_vip"] = ki_user.game_info.vip_level
    context.data["hero_number"] = len(ki_user.hero.heros)

    method = context.get_parameter('method', None)
    # 遇上会触发任务的操作，需要保存一些任务前的临时数据
    if method == "mission.past" or method == "hero.intensify":
        heros = ki_user.hero.heros
        total_level = sum([hero["level"] for hero in heros.values()])
        context.data["old_hero_levels"] = total_level

def post_task_info_checker(context):
    # 检测是否有任务状态改变
    mc = context.result['mc']
    # 检测操作是否合法
    if not str(mc/100).endswith("1"):
        return

    # _post_main_task_checker(context)
    _post_update_daily_task(context)
    _post_daily_task_checker(context)
    _post_update_acts(context)

# =================================== Internal Functions ========================================
def _post_update_acts(context):
    ki_user = context.user
    method = context.get_parameter('method')

    if method == "equip.upgrade":
        act_helper.update_complex_acts(ki_user, (0,1))
    elif method == "hero.upgrade":
        act_helper.update_complex_acts(ki_user, (1,1))
    elif method == "task.daily_submit":
        act_helper.update_complex_acts(ki_user, (2,1))
    elif method == "mission.past" or method == "mission.hangup":
        mission_id = context.get_parameter("mission_id", None)
        htimes = context.get_parameter("htimes", 1)
        cfg = game_config.mission_base_cfg.get(mission_id, {})
        if cfg and cfg["type"] == 1:
            act_helper.update_complex_acts(ki_user, (3,htimes))

    elif method == "act_mission.past":
        mission_id = context.get_parameter("mission_id", None)
        htimes = context.get_parameter("htimes", 1)
        cfg = game_config.mission_act_base_cfg.get(mission_id, {})
        if cfg and cfg["type"] == 1:
            act_helper.update_complex_acts(ki_user, (4,htimes))

    else:
        pass

# def _post_main_task_checker(context):
#     """【主线】任务处理器
#     """
#     ki_user = context.user
#     method = context.get_parameter('method')

#     before_level = context.data["before_level"]
#     after_level = ki_user.game_info.role_level

#     before_hero_number = context.data["hero_number"]
#     after_hero_number = len(context.user.hero.heros)

#     if after_level > before_level:
#         _update_tasks_states(ki_user, static_const.TASK_TARGET_USER_LEVEL)

#     if after_hero_number > before_hero_number:
#         _update_tasks_states(ki_user, static_const.TASK_TARGET_HERO_NUMBER)

#     if method == "mission.past":
#         _update_tasks_states(ki_user, static_const.TASK_TARGET_MISSION_PAST)

#     if method == "hero.upgrade":
#         _update_tasks_states(ki_user, static_const.TASK_TARGET_HERO_QUALITY)

def _post_update_daily_task(context):
    """vip等级和战队等级提升之后检测是否有新日常任务开启
    """
    ki_user = context.user

    before_level = context.data["before_level"]
    before_vip = context.data["before_vip"]

    after_level = ki_user.game_info.role_level
    after_vip = ki_user.game_info.vip_level

    if after_level > before_level or after_vip > before_vip:
        new_task_ids = task_helper.prepare_daily_task(after_level, after_vip)
        add_task = [task_id for task_id in new_task_ids if task_id not in ki_user.task.daily_tasks]

        if add_task:
            for daily_task_id in add_task:
                ki_user.task.daily_tasks[daily_task_id] = {"process":0, "state": static_const.TASK_STATE_DOING}

            ki_user.task.put()
        else:
            pass

def _post_daily_task_checker(context):
    """【日常】任务处理器
    """
    ki_user = context.user
    method = context.get_parameter('method')

    # TODO 1.进行n次公会捐献

    if method == "arena.fight":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_ARENA_FIGHT)

    elif method == "trial.fight":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_TRIAL_TIMES)

    elif method == "trial.skip":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_TRIAL_TIMES)

    elif method == "hero.intensify":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_HERO_LEVEL)

    elif method == "hero.upgrade":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_HERO_UPGRADE_TIMES)

    elif method == "hero.pick":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_HERO_PICK_TIMES)

    elif method == "skill.intensify":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_SKILL_LEVEL)

    elif method == "user.buy_gold":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_BUY_GOLD)

    elif method == "user.buy_energy":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_BUY_ENERGY)

    elif method == "group.donate":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_GROUP_DONATE)

    elif method == "mission.past" or method == "mission.hangup":
        _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_HERO_LEVEL)

        mission_id = context.get_parameter("mission_id", None)
        cfg = game_config.mission_base_cfg.get(mission_id, {})
        if cfg and cfg["type"] == 1:
            _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_MISSION_PT_TIMES)
        elif cfg and cfg["type"] == 2:
            _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_MISSION_JY_TIMES)
        else:
            pass

    elif method == "act_mission.enter":
        mission_id = context.get_parameter("mission_id", None)
        cfg = game_config.mission_act_base_cfg.get(mission_id, {})
        if cfg and cfg["type"] == 1:
            _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_DAILY_GOLD_TIMES)
        elif cfg and cfg["type"] == 2:
            _handle_daily_tasks_by_type(context, static_const.TASK_TARGET_DAILY_EXP_TIMES)
        else:
            pass

    else:
        pass

def _handle_daily_tasks_by_type(context, task_type):
    """
    """
    try:
        ki_user = context.user
        _old_daily_tasks = copy.deepcopy(ki_user.task.daily_tasks)
        for task_id, task in ki_user.task.daily_tasks.items():
            cfg = game_config.task_daily_cfg.get(task_id)
            if cfg["type"] == task_type and task["state"] == static_const.TASK_STATE_DOING:
                func = getattr(task_helper, 'task_checker_%s' % cfg["checker"])
                func(task_id, task, context)

        # 日常任务数据有更新，保存到数据库
        if _old_daily_tasks != ki_user.task.daily_tasks:
            ki_user.task.put()
    except:
        print "_handle_daily_tasks_by_type %s error." % task_type

# def _update_tasks_states(user, task_type):
#     """触发了任务的检测

#     正在进行中的任务且满足类型条件的任务才需要检测，已完成的任务不需要检测

#     Args:
#         user 玩家数据
#         task_type 任务类型
#     """
#     _tmp_main_tasks = copy.deepcopy(user.task.main_doing_tasks)
#     for task_id, old_state in user.task.main_doing_tasks.items():
#         cfg = game_config.task_main_cfg.get(task_id)
#         if cfg["type"] == task_type and old_state == static_const.TASK_STATE_DOING:
#             func = getattr(task_helper, 'task_checker_%s' % cfg["type"])
#             new_state = func(user, cfg)
#             if new_state != old_state:
#                 _tmp_main_tasks[task_id] = new_state

#     # 任务状态有改变时，更新数据库中的任务数据
#     if _tmp_main_tasks != user.task.main_doing_tasks:
#         user.task.main_doing_tasks = _tmp_main_tasks
#         user.task.put()
