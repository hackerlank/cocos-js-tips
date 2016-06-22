#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-18 14:30:43
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      游戏业务共用工具函数
# @end
# @copyright (C) 2015, kimech

import random
import datetime

from apps.misc import utils

def time_to_refresh(old_refresh, refresh_hour):
    """计算数据是否刷新

    Args:
        old_refresh 上次刷新日期和小时 2015092404
        refresh_hour 刷新小时时间点

    Returns:
        True / False

    """
    if old_refresh == 0:
        return True

    cur_hour = datetime.datetime.now().hour
    if isinstance(old_refresh, int):
        old_refresh = "%s" % old_refresh

    if int(old_refresh[:-2]) != utils.today():
        # 已经不是同一天了，然后判断当前的小时是否已经到了指定的刷新时间点后面
        if cur_hour >= refresh_hour:
            return True
        else:
            return False
    else:
        # 判断是否是当天5点前创建账号
        if int(old_refresh[-2:]) < refresh_hour and cur_hour >= refresh_hour:
            return True
        else:
            return False

def time_to_award(award_time):
    """计算当前时间是否已经到点了

    使用场景：
        1.【日常任务】到点领物品,超过两小时不可领取

    Args:
        award_time : (5,0,0) 发物品时间

    Returns:
        True / False

    """
    start_time, end_time = award_time[0], award_time[1]

    cur_hour = datetime.datetime.now().hour
    cur_min = datetime.datetime.now().minute

    if cur_hour > start_time[0] and cur_hour < end_time[0]:
        return True
    elif cur_hour == start_time[0] and cur_min >= start_time[1]:
        return True
    elif cur_hour == end_time[0] and cur_min <= end_time[1]:
        return True
    else:
        return False

def get_level_by_exp(config, exp):
    """根据经验计算相应等级

    经验 =》 等级

    Args:
        config 经验等级对照配置表
        exp 经验

    Returns:
        level 当前等级

    """
    config = sorted(config.iteritems(), key=lambda d:d[0])
    l = [item[1] for item in config if item[0] <= exp]

    return 0 if not l else max(l)

def get_award_by_data(config, data):
    """根据相应数值获得相应物品
    """
    indexes = sorted(config.iteritems(), key=lambda d:d[0])
    l = [i[0] for i in indexes if i[0] >= data]

    if not l:
        return {}
    else:
        return config.get(max(l), {})

def handle_pack_items(items):
    """处理道具包

    此接口主要是为了保护dict.update方法相同key，value会被赋予新值
    如:
        d = {120001: 1, 120002: 2}
        d.update({1200001: 3})
        => d 变成 {1200001: 3, 120002: 2}

    Args:
        user 用户
        items [{item_id: num, item_id1: num1}, {item_id: num2}, ]
    """
    new_items = {}
    for d in items:
        for key, value in d.iteritems():
            if key not in new_items:
                new_items[key] = value
            else:
                new_items[key] += value

    return new_items

def weight_random(rand_lib):
    """权值随机数

    Args:
        {
            1: 0.898,
            2: 0.05,
            3: 0.05,
            5: 0.001,
            10: 0.001,
        }

    Returns:
        1
    """
    rand_sum = sum(rand_lib.values())
    rand = random.random() * rand_sum

    for key, value in rand_lib.items():
        rand -= value
        if rand <= 0:
            return key
