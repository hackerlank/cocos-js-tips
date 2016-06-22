#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-21 16:44:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       任务检测工具
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs import static_const

def prepare_main_task():
    """【主线】创建角色的时候，初始化主线任务数据

    Returns:
        [task_id1, task_id2, task_id3]
    """
    tmp = []
    for task_id, task in game_config.task_main_cfg.items():
        if task["front_task"] == 0:
            tmp.append(task_id)

    return tmp

def prepare_daily_task(level, vip):
    """【日常】根据玩家当前的等级和vip等级筛选日常任务  扔进列表里

    Args:
        level 玩家当前战队等级
        vip 玩家当前vip等级

    Returns:
        [task_id1, task_id2, task_id3]
    """
    tmp = []
    for task_id, task in game_config.task_daily_cfg.items():
        if task["need_level"] <= level and task["need_vip"] <= vip:
            tmp.append(task_id)

    return tmp

# def trigger_next_task(user, next_task_id):
#     """【主线】玩家提交任务之后，检测后续任务是否可接 -》是否完成

#     Args:
#         user 玩家数据model
#         task_id 当前提交的任务ID

#     """
#     # 此系列没有后续任务了，返回
#     if not next_task_id:
#         return 0
#     else:
#         next_cfg = game_config.task_main_cfg.get(next_task_id)
#         # 下一个任务的配置不全，放弃吧
#         if not next_cfg:
#             return 0
#         else:
#             task_state = eval("task_checker_%s(user, next_cfg)" % next_cfg["type"])
#             return task_state

# ================================ TASK CHECKER ===============================
def task_checker_1(user, next_cfg):
    """【主线】【通关副本】任务检测器
    """
    return 1 if next_cfg["target"] in user.mission.missions else 0

def task_checker_2(user, next_cfg):
    """【战队等级】任务检测器
    """
    return 1 if user.game_info.role_level >= next_cfg["target"] else 0

def task_checker_3(user, next_cfg):
    """【机甲收集数量】任务检测器
    """
    hero_number = len(user.hero.heros)
    return 1 if hero_number >= next_cfg["target"] else 0

def task_checker_4(user, next_cfg):
    """【n个姬甲升到n品级】任务检测器
    """
    count = 0
    for hero in user.hero.heros.values():
        if hero["quality"] >= next_cfg["target"]:
            count += 1

    return 1 if count >= next_cfg["target2"] else 0

# =========================== 【日常】通用检测接口 ===============================
def _task_common_checker(task_id, task, count):
    """任务检测器的代码复用部分

    """
    cfg = game_config.task_daily_cfg.get(task_id)
    task["process"] = min(cfg["target"], task["process"]+count)
    if task["process"] >= cfg["target"]:
        task["state"] = static_const.TASK_STATE_COMPLETED

def task_checker_0(task_id, task, context):
    """【日常】通用任务检测器

    5. 挑战n次竞技场
    7. 完成n次试炼
    8. 进行n次姬甲升品
    10. 进行n次金币购买
    11. 进行n次体力购买
    12. 社团n次捐献

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    count = 1
    _task_common_checker(task_id, task, count)

def task_checker_6(task_id, task, context):
    """【日常】【任意姬甲升n级】任务检测器

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    ki_user = context.user
    old_hero_levels = context.data.get("old_hero_levels", 0)
    new_total_levels = sum([hero["level"] for hero in ki_user.hero.heros.values()])
    count = new_total_levels - old_hero_levels
    _task_common_checker(task_id, task, count)

def task_checker_9(task_id, task, context):
    """【日常】【抽卡n次】任务检测器

    十连抽算做10次

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    ptype = context.get_parameter("ptype")
    count = 1 if ptype in [1,3] else 10

    _task_common_checker(task_id, task, count)

def task_checker_13(ki_user, diamond):
    """【日常】【每日消费n钻石】任务检测器

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    for task_id, task in ki_user.task.daily_tasks.items():
        cfg = game_config.task_daily_cfg.get(task_id)
        if cfg["type"] == static_const.TASK_TARGET_CONSUME_DIAMOND and \
            task["state"] == static_const.TASK_STATE_DOING:
            _task_common_checker(task_id, task, diamond)
            ki_user.task.put()

def task_checker_14(task_id, task, context):
    """【日常】【技能升级】任务检测器

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    count = context.get_parameter("level")

    _task_common_checker(task_id, task, count)

def task_checker_20(task_id, task, context):
    """【日常】【通关精英、普通副本n次】任务检测器

    扫荡n次算通关n次

    Args:
        task_id 任务ID
        task = {"process": 1, "state": 1} 任务数据
        context 请求数据环境变量

    Returns:
        task: {"process": 1, "state": 1}

    """
    method = context.get_parameter("method")
    count = 0
    if method == "mission.past":
        count = 1
    elif method == "mission.hangup":
        count = context.get_parameter("htimes", 0)
    else:
        pass

    _task_common_checker(task_id, task, count)

# ================================ TASK CHECKER ===============================
