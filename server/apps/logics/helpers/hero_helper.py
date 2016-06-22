#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-18 12:43:11
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     卡牌(英雄)辅助接口
# @end
# @copyright (C) 2015, kimech

import random

from apps.configs import game_config
from .fight_helper import Fight
# 抽卡类型
GOLD_ONE = 1
GOLD_TEN = 2
DIAMOND_ONE = 3
DIAMOND_TEN = 4

# 随机类型
RAND_TYPE_1 = 1 # 金币单次

#################################
RAND_TYPE_2 = 2 # 金币连抽普通
RAND_TYPE_3 = 3 # 金币连抽必得
#################################

RAND_TYPE_4 = 4 # 金币免费
RAND_TYPE_5 = 5 # 金币免费必得
RAND_TYPE_6 = 6 # 钻石单次

#################################
RAND_TYPE_7 = 7 # 钻石连抽普通
#################################

RAND_TYPE_9 = 9 # 钻石免费
RAND_TYPE_10 = 10 # 钻石单次必得
RAND_TYPE_11 = 11 # 钻石首次连抽必得
RAND_TYPE_12 = 12 # 钻石首次
RAND_TYPE_13 = 13 # 钻石第二次

def max_six_fights(heros):
    """最强6人战力
    """
    fights = [hero["fight"] for hero in heros.values()]
    fights.sort(reverse=True)
    max_fight = sum(fights[:6]) # 最强六人战力

    return max_fight

def count_array_fight(hero_id, user):
    """给一个阵容 计算战力
    """
    hero = user.hero.heros[hero_id]

    equips = user.equip.get_by_hero_id(hero_id)
    skills = user.skill.get_skills_by_hero_id(hero_id)
    spirits = user.spirit.get_spirits_by_hero_id(hero_id)
    talents = user.talent.talents
    fates = build_hero_fates(hero_id, user.hero.heros, equips)
    favor_speed = count_favor_speed(hero_id, user.hero.heros)

    hero_fight = Fight(hero, equips, skills, spirits, fates, talents, user.warship.ships, favor_speed, user.game_info.role_level)

    return hero_fight.fight

def build_hero_fates(hero_id, heros, equips):
    """建造机甲的情缘
    """
    base_cfg = game_config.hero_base_cfg[hero_id]
    _fates = []
    for fate in [fate_id for fate_id in base_cfg["fates"] if fate_id]:
        fate_cfg = game_config.hero_fate_cfg.get(fate)
        is_open = True
        # 情缘关联机甲
        if fate_cfg["union_type"] == 1:
            if len(set(fate_cfg["union_data"]).difference(heros.keys())) != 0:
                is_open = False
        else:
            # 情缘关联装备觉醒
            for equip_id in fate_cfg["union_data"]:
                cfg = game_config.equip_cfg[equip_id]
                if equips[cfg["position"]]["star"] <= 0:
                    is_open = False

        if is_open:
            _fates.append(fate)

    return _fates

def count_favor_speed(hero_id, heros):
    """计算同系姬甲带来的速度值加成
    """
    cfg = game_config.hero_base_cfg.get(hero_id)
    f_cfg = game_config.favor_cfg.get(cfg["favor_type"], {})
    if not f_cfg:
        return 0
    else:
        speed = 0
        for hero in f_cfg["heros"]:
            h = heros.get(hero, {})
            if not h:
                continue
            else:
                favor_level = max([i for i,cfg in game_config.favor_level_cfg.items() if cfg["favor"] <= h["favor"]])
                c = game_config.favor_level_cfg.get(favor_level)
                speed += c["speed"]

    return speed

def fetch_warship_data(warship):
    """
    """
    online = {}
    for id,value in warship.ships.items():
        if id in warship.team:
            online[id] = value

    return online

def get_equip_pos_by_equip_id(equip_id, equips):
    """根据装备ID取得装
    """

def hero_exist(heros, hero_id):
    """检测单个英雄是否存在
    """
    return hero_batch_exist(heros, [hero_id])

def hero_batch_exist(heros, hero_ids):
    """批量检测英雄是否存在

    hero_ids = []
    """
    for hero_id in hero_ids:
        if hero_id not in heros:
            return False

    return True

def get_rand_type(is_free, ptype, pick_info, loop_index):
    """判断随机类型

    Args:
        ptype  抽奖类型  1-金币单次 2-金币连抽 3-钻石单次 4-钻石连抽
        is_free  是否免费，针对金币单次和钻石单次
        pick_info
            diamond_pick_times  确定钻石单次十抽必得3星卡牌
            diamond_ten_times   钻石第一次连抽必得4星卡牌
        loop_index 连抽第N次

    """
    rand_type = 0

    if ptype == GOLD_ONE:
        rand_type = RAND_TYPE_4 if is_free else RAND_TYPE_1
    elif ptype == GOLD_TEN:
        # 连抽特殊规则 ！！！！！
        rand_type = 109 - loop_index
    elif ptype == DIAMOND_ONE:
        if pick_info["diamond_pick_times"] == 0:
            rand_type = RAND_TYPE_12    # 新手引导
        elif pick_info["diamond_pick_times"] == 1:
            rand_type = RAND_TYPE_13    # 整个人抽第十三次
        elif pick_info["diamond_pick_times"] % 10 == 0:
            rand_type = RAND_TYPE_10    # 钻石单次抽卡必得
        else:
            rand_type = RAND_TYPE_9 if is_free else RAND_TYPE_6
    elif ptype == DIAMOND_TEN:
        if pick_info["diamond_ten_times"] == 0:
            if loop_index == 9:
                rand_type = RAND_TYPE_11   # 首次钻石连抽的第一次抽卡必得4星卡牌
            else:
                rand_type = 209 - loop_index   # 首次钻石连抽的第一次抽卡必得4星卡牌
        else:
            rand_type = 209 - loop_index
    else:
        pass

    return rand_type

def get_pick_rand_lib(rand_type):
    """获得随机类型对应的随机库

    Args:
        rand_type 随机类型 12种

    Return:
        {120000: 12}

    """
    cfgs = game_config.hero_pick_rand_cfg
    rand_list = filter(lambda x: x["type"] == rand_type, cfgs.itervalues())
    rand_lib_id = weighted_choice(rand_list)
    rand_lib = game_config.hero_pick_rand_cfg.get(rand_lib_id)

    return rand_lib

def weighted_choice(lists):
    """加权随机方法

    Args:
        [{"id": 10001, "weight": 40}, {"id": 10002, "weight": 50}]

    Return:
        {"id": 10002, "weight": 50}
    """
    # 从大到小排序可提高速度
    lists = sorted(lists, key=lambda x:x["weight"], reverse = True)
    rand_sum = sum([item["weight"] for item in lists])

    rand = random.randint(0, rand_sum)

    for item in lists:
        rand -= item["weight"]
        if rand <= 0:
            return item["id"]
