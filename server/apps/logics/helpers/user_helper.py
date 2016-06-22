#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-24 11:21:52
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   用户游戏数据检测等杂项逻辑
# @end
# @copyright (C) 2015, kimech

import copy
import time
import logging

from apps.models.user import User
from apps.configs import game_config

from . import hero_helper
from .fight_helper import Fight
from apps.configs import static_const

def build_hero_euqip_skill(user):
    """组装机甲的装备，技能数据
    """
    hero_datas = copy.deepcopy(user.hero.heros)
    equip_datas = copy.deepcopy(user.equip.equips)
    skill_datas = copy.deepcopy(user.skill.skills)
    spirit_datas = copy.deepcopy(user.spirit.spirits)

    for hero_id, hero_data in hero_datas.iteritems():
        if equip_datas:
            hero_data["equips"] = equip_datas.get(hero_id, {})

        if skill_datas:
            hero_data["skills"] = skill_datas.get(hero_id, {})

        if spirit_datas:
            hero_data["spirits"] = spirit_datas.get(hero_id, {})

    return hero_datas

def build_arena_hero_euqip_skill(user):
    """组装竞技场阵型中机甲的装备，技能数据
    """
    datas = []

    hero_datas = copy.deepcopy(user.hero.heros)
    equip_datas = copy.deepcopy(user.equip.equips)
    skill_datas = copy.deepcopy(user.skill.skills)
    spirit_datas = copy.deepcopy(user.spirit.spirits)

    if user.array.arena == [0]*6:
        array = user.array.mission
    else:
        array = user.array.arena

    # 处理当创建角色时出现了问题，玩家没有正确的机甲阵容
    # 而试炼 竞技场却匹配到了这个玩家做对手  则使用默认的数据
    for hero_id in array:
        if hero_id:
            hero_data = copy.deepcopy(hero_datas.get(hero_id))
            hero_data["equips"] = equip_datas.get(hero_id, {})
            hero_data["skills"] = skill_datas.get(hero_id, {})
            hero_data["spirits"] = spirit_datas.get(hero_id, {})
            hero_data["fates"] = hero_helper.build_hero_fates(hero_id, hero_datas, hero_data["equips"])

            datas.append(hero_data)
        else:
            datas.append(0)

    return datas

def build_arena_hero_snapshot(uid):
    """竞技场replay 玩家当时快照
    """
    datas = []

    if uid.startswith("robot_"):
        pass
    else:
        user = User.get(uid)
        if isinstance(user, User):
            hero_datas = copy.deepcopy(user.hero.heros)
            if user.array.arena == [0]*6:
                array = user.array.mission
            else:
                array = user.array.arena

            for hero_id in array:
                if hero_id:
                    hero_data = copy.deepcopy(hero_datas.get(hero_id))
                    datas.append(hero_data)
                else:
                    datas.append(0)

    return datas

def check_user_fight(ki_user, client_fight, atype=1):
    """立即计算玩家战斗力

    Args:
        atype   1: "mission",
                2: "arena",
                3: "trial",
                4: "act_gold",
                5: "act_exp",
                6: "act_fire",
                7: "act_ice",
                8: "act_phantom",
                9: "worldboss",
    """
    client_fight = eval(client_fight)
    if isinstance(client_fight, int):
        return True

    adict = {1: "mission", 2: "arena", 3: "trial", 4: "act_gold", 5: "act_exp", 6: "act_fire", 7: "act_ice", 8: "act_phantom", 9: "worldboss"}
    array = eval("ki_user.array.%s" % adict[atype])
    fight = eval("ki_user.array.%s_fight" % adict[atype])

    total_client_fight = sum(client_fight.values())
    a, b = total_client_fight * (1 - 0.05), total_client_fight * (1 + 0.05)
    if a <= fight <= b:
        return True

    array_fight = {}
    for hero_id in array:
        if not hero_id:
            continue

        array_fight[hero_id] = hero_helper.count_array_fight(hero_id, ki_user)

    total_array_fight = sum(array_fight.values())
    ki_user.array.update_fight(atype, total_array_fight)

    a, b = total_client_fight * (1 - 0.05), total_client_fight * (1 + 0.05)

    if total_client_fight != total_array_fight:
        logging.error("【 fight check failed 】uid:%s atype:%s s:%s c:%s s1:%s c1:%s result: %s" % (ki_user.uid,
                      atype, array_fight, client_fight, sum(array_fight.values()), sum(client_fight.values()),
                      a <= total_array_fight <= b))

    return a <= total_array_fight <= b

def build_array_hero_data(array, heros):
    """筛选上阵机甲的数据【请求其他玩家数据时调用】
    """
    array_heros = []
    for hero in [hero_id for hero_id in array if hero_id]:
        array_heros.append(heros[hero])

    return array_heros

def build_warship_data(warships, team):
    """组装竞技场对手的战舰数据，阵容和战舰结合
    """
    datas = []
    for warship_id in team:
        if warship_id:
            warship = copy.deepcopy(warships.get(warship_id))
            warship["warship_id"] = warship_id
            datas.append(warship)
        else:
            datas.append(0)

    return datas
