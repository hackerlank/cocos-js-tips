#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-25 13:16:46
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   玩家名字服务，验证玩家名字是否重复，是否包含敏感字词
# @end
# @copyright (C) 2015, kimech

import time
import random

from libs.tinygfw import GFW
from libs.rklib.core import app

from apps.configs import game_config
from apps.configs import rediskey_config

gfw = GFW()
gfw.set(game_config.sensitive_char_cfg.values())

redis_client = app.get_storage_engine('redis').client.current

def build_robot_name():
    """
    """
    name = "%s%s%s" % (random.choice(game_config.first_name_cfg),
                        random.choice(game_config.middle_name_cfg),
                            random.choice(game_config.last_name_cfg))

    return name

def check_sensitive_character(name):
    """检测玩家名字是否包含敏感字符

    Args:
        name str 待查询名字
    Returns:
        bool  是否包含敏感字符

    """
    return False if gfw.check(name) else True

def get_uid_by_name(name):
    """根据玩家名称获取uid

    Args:
        name str 待查询名字

    """
    return redis_client.hget(rediskey_config.USER_REGISTERED_NAME, name)

def check_name_repeated(name, name_type=1):
    """检测玩家名字是否重复

    Args:
        name str 待查询名字
        name_type 名字类型  1-玩家名称 2-公会名称
    Returns:
        bool  是否重复

    """
    if name_type == 1:
        key = rediskey_config.USER_REGISTERED_NAME
    else:
        key = rediskey_config.GROUP_CREATED_NAME

    return redis_client.hexists(key, name) == 1

def add_registered_name(register_name, uid):
    """新增已经注册名字

    Args:
        register_name str  新增注册的角色名字
        uid  str  名字对应的用户id

    """
    try:
        key = rediskey_config.USER_REGISTERED_NAME
        redis_client.hset(key, register_name, uid)
    except:
        print "Error: add_registered_name error."

def add_created_group_name(created_name, group_id):
    """新增已经创建的公会名字

    Args:
        created_name str  新增注册的公会名字
        group_id int 公会ID

    """
    try:
        key = rediskey_config.GROUP_CREATED_NAME
        redis_client.hset(key, created_name, group_id)
    except:
        print "Error: add_registered_name error."

def get_group_id_by_name(created_name):
    """新增已经创建的公会名字

    Args:
        created_name str  新增注册的公会名字
        group_id int 公会ID

    """
    try:
        key = rediskey_config.GROUP_CREATED_NAME
        result = redis_client.hget(key, created_name)
        if result:
            return int(result)
        else:
            return 0
    except:
        return 0
