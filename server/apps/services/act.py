#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-25 13:16:46
# @Author : Jiank (http://jiankg.github.com)
# @doc
#    排行榜服务
# @end
# @copyright (C) 2015, kimech

import time
from apps.misc import utils
import cPickle as pickle

from libs.rklib.core import app

from apps.configs import game_config
from apps.configs import rediskey_config
from apps.misc.global_info import Server

from torngas.settings_manager import settings

redis_client = app.get_storage_engine('redis').client.current

def fasten_activities(sid):
    """查找当前服的那些固定开启的活动
    """
    server = Server.get_server_by_id(sid)
    open_date = utils.timestamp2string(server["open_time"]) # 20160218
    open_date_zero_stamp = utils.datestamp(open_date)

    server_open_acts = {}
    for id, act in game_config.act_fasten_cfg.items():
        server_open_acts[id] = {
                "start": open_date_zero_stamp + int(act["start"] * 86400),
                "end": open_date_zero_stamp + int(act["days"] * 86400),
                "start1": open_date_zero_stamp + int(act["start1"] * 86400),
                "end1": open_date_zero_stamp + int(act["days1"] * 86400),
            }

    return server_open_acts

def all(sid):
    """查找当前所有活动的配置数据

    迭代性的活动从redis中查询 开服活动从固定配置表中读取

    Args:
        sid 服务器ID

    Returns:
        {}
    """
    act_key = rediskey_config.ACT_KEY_PREFIX % sid
    acts = redis_client.hgetall(act_key)

    for act_id, act in acts.items():
        acts[act_id] = pickle.loads(act)

    acts1 = fasten_activities(sid)
    # 把开服活动也给带上
    acts1.update(acts)

    return acts1

def get_act_info(sid, act_id):
    """查找活动的配置数据

    Args:
        sid 服务器ID

    Returns:
        {}
    """
    act_key = rediskey_config.ACT_KEY_PREFIX % sid
    result = redis_client.hget(act_key, act_id)

    if not result:
        fastenacts = fasten_activities(sid)
        return fastenacts.get(act_id, {})
    else:
        return pickle.loads(result)

def get_all_private_sale_num(sid, act_id):
    """获取特卖活动已经卖出的数量
    """
    key = rediskey_config.ACT_PRIVATE_SALE_PREFIX % (sid, act_id)
    result = redis_client.hgetall(key)
    if not result:
        return {}
    else:
        for k,v in result.items():
            result[k] = int(v)

        return result

def get_private_sale_num(sid, act_id, index):
    """获取特卖活动已经卖出的数量
    """
    key = rediskey_config.ACT_PRIVATE_SALE_PREFIX % (sid, act_id)
    result = redis_client.hget(key, index)

    return int(result) if result else 0

def update_private_sale_num(sid, act_id, index):
    """更新特卖活动已经卖出的数量
    """
    key = rediskey_config.ACT_PRIVATE_SALE_PREFIX % (sid, act_id)
    redis_client.hincrby(key, index, 1)

def add_diamond_gamble_records(sid, act_id, record):
    """增加钻石赌博记录
    """
    key = rediskey_config.ACT_DIAMOND_GAMBLE_KEY % (sid, act_id)
    redis_client.lpush(key, pickle.dumps(record))
    redis_client.ltrim(key, 0, 2)  # 记录只保存3条

def get_diamond_gamble_records(sid, act_id):
    """获取钻石赌博记录
    """
    key = rediskey_config.ACT_DIAMOND_GAMBLE_KEY % (sid, act_id)
    results = redis_client.lrange(key, 0, -1)

    return [pickle.loads(r) for r in results]
