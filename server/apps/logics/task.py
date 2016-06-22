#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-28 10:15:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   任务业务逻辑
# @end
# @copyright (C) 2015, kimech

import datetime
from apps.configs import game_config
from apps.configs import static_const
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

from .helpers import task_helper
from .helpers import common_helper
# ========================== API ==============================
def submit(context):
    """提交任务

    Args:
        task_id 任务ID

    Returns:
        mc
    """
    ki_user = context.user

    task_id = context.get_parameter("task_id")

    cfg = game_config.task_main_cfg.get(task_id, None)
    if cfg is None:
        context.result['mc'] = MsgCode['TaskNotExist']
        return

    if task_id in ki_user.task.main_completed_tasks:
        context.result['mc'] = MsgCode['TaskAlreadySubmit']
        return

    func = getattr(task_helper, 'task_checker_%s' % cfg["type"])
    state = func(ki_user, cfg)
    if state != static_const.TASK_STATE_COMPLETED:
        context.result['mc'] = MsgCode['TaskCantSubmit']
        return

    # 增加任务奖励
    pack_logic.add_items(ki_user, cfg["awards"])
    # 更新任务状态,
    ki_user.task.submit(task_id)
    # 检测是否有后续任务等待操作
    if cfg["next"]:
        # next_task_state = task_helper.trigger_next_task(ki_user, cfg["next"])
        # ki_user.task.fetch_next_task(cfg["next"], next_task_state)
        ki_user.task.fetch_next_task(cfg["next"])

    context.result["mc"] = MsgCode["TaskSubmitSucc"]

def daily_submit(context):
    """提交日常任务

    Args:
        task_id 任务ID

    Returns:
        mc
    """
    ki_user = context.user

    task_id = context.get_parameter("task_id")

    task = ki_user.task.daily_tasks.get(task_id, {})
    if not task:
        context.result['mc'] = MsgCode['TaskNotExist']
        return

    if task["state"] == static_const.TASK_STATE_SUBMITED:
        context.result['mc'] = MsgCode['TaskCantSubmit']
        return

    task_cfg = game_config.task_daily_cfg.get(task_id)
    # 40类型特殊  每日都可以领一次
    if task_cfg["type"] in static_const.TASK_DAILY_GET_ITEMS_TYPE:
        award_time = static_const.TASK_TIME_TO_AWARD_MAP[task_cfg["type"]]
        if not common_helper.time_to_award(award_time):
            context.result['mc'] = MsgCode['TaskCantSubmit']
            return

    elif task_cfg["type"] == static_const.TASK_DAILY_VIP_GET_DIAMOND_TYPE:
        ki_user.vip.update_card_when_request()
        if ki_user.vip.card_data["state"] < task_cfg["target"]:
            context.result['mc'] = MsgCode['TaskCantSubmit']
            return

    else:
        if task["state"] != static_const.TASK_STATE_COMPLETED:
            context.result['mc'] = MsgCode['TaskCantSubmit']
            return

    # 增加任务奖励
    ki_user.task.complete_daily_task(task_id)
    pack_logic.add_items(ki_user, task_cfg["awards"])

    context.result["mc"] = MsgCode["TaskSubmitSucc"]
