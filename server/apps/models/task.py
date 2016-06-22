#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-28 10:17:49
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   任务数据model
# @end
# @copyright (C) 2015, kimech

import time
import datetime
from apps.misc import utils

from apps.configs import game_config
from apps.configs import static_const

from libs.rklib.model import BaseModel

from apps.logics.helpers import task_helper
from apps.logics.helpers import common_helper

class Task(BaseModel):
    """任务信息

    Attributes:
        uid: 用户uid
        last_refresh_date: 日常任务上次刷新日期和小时 2015110404
        daily_tasks: 日常任务
            {
                10002: {
                    "process": 1,
                    "state": 0, # 0 - 进行中 1 - 已完成 2 - 已提交
                }
            }
        main_completed_tasks: [task_id]
        main_doing_tasks: 主线任务
            {
                10005: 0,   # 0 - 进行中 1 - 已完成
                10007: 1,
            }
    """

    def __init__(self, uid=None):
        """初始化任务信息

        Args:
            uid: 平台用户ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 用户ID
        self.last_refresh_date = 0
        self.daily_tasks = {}  # 日常任务

        self.main_completed_tasks = [] # 已经提交完的任务列表
        self.main_doing_tasks = {}  # 主线任务

    @classmethod
    def install(cls, uid):
        """为新角色初始安装任务数据信息

        Args:
            uid: 角色ID
        """
        task = cls(uid)

        task.main_doing_tasks = dict.fromkeys(task_helper.prepare_main_task(), 0)
        task.put()

        return cls.get(uid)

    def submit(self, task_id):
        """【主线】提交任务

        从正在进行的任务字典中删除。把ID加入已完成的任务列表

        """
        self.main_completed_tasks.append(task_id)
        del self.main_doing_tasks[task_id]

        self.put()

    def fetch_next_task(self, task_id):
        """【主线】发现新任务
        """
        self.main_doing_tasks[task_id] = 0

        self.put()

    def get_daily_tasks(self, level, vip, vip_card_data):
        """【日常任务】获取数据
        """
        another_day = common_helper.time_to_refresh(self.last_refresh_date, 5)
        if another_day:
            task_list = task_helper.prepare_daily_task(level, vip)
            for daily_task_id in task_list:
                self.daily_tasks[daily_task_id] = {"process": 0, "state": 0}

            self.last_refresh_date = time.strftime('%Y%m%d%H')

        for task_id, task in self.daily_tasks.items():
            task_cfg = game_config.task_daily_cfg.get(task_id)
            if task_cfg and task["state"] != static_const.TASK_STATE_SUBMITED:
                if task_cfg["type"] in static_const.TASK_DAILY_GET_ITEMS_TYPE:
                    result = self.task_time_to_award(task_id, task)
                    if result:
                        task["state"] = static_const.TASK_STATE_COMPLETED
                    else:
                        task["state"] = static_const.TASK_STATE_DOING

                elif task_cfg["type"] == static_const.TASK_DAILY_VIP_GET_DIAMOND_TYPE:
                    if vip_card_data["state"] >= task_cfg["target"]:
                        task["state"] = static_const.TASK_STATE_COMPLETED

                else:
                    pass

        self.put()

        return self.daily_tasks

    @staticmethod
    def task_time_to_award(task_id, task):
        """检查到时任务的最新状态

        Args:
            task_id 任务ID

        Returns:

        """
        if task["state"] == static_const.TASK_STATE_SUBMITED:
            return False

        cfg = game_config.task_daily_cfg.get(task_id)
        award_time = static_const.TASK_TIME_TO_AWARD_MAP[cfg["type"]]

        return common_helper.time_to_award(award_time)

    def complete_daily_task(self, task_id):
        """置为已完成
        """
        # 更新日常任务状态
        self.daily_tasks[task_id]["state"] = 2
        self.put()

    def _reset(self):
        """重置任务
        """
        self.last_refresh_date = 0
        self.daily_tasks = {}  # 日常任务

        self.main_completed_tasks = [] # 已经提交完的任务列表
        self.main_doing_tasks = {}  # 主线任务

        self.put()
