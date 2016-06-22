#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-21 16:44:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       试炼助手
# @end
# @copyright (C) 2015, kimech

import copy
import random
import logging

from apps.models.user import User
from apps.services.arena import ArenaService
from apps.services import rank as rank_service

from apps.configs import game_config

from . import hero_helper
from . import user_helper

from libs.rklib.core import app

def initial_daily_fighters(sid, uid, heros):
    """初始化每日试炼对手数据

    Args:
        sid 角色ID
        heros 机甲数据
    """
    fight_process = [process for process,cfg in game_config.trial_cfg.items() if cfg["type"] == 1]

    all_fighters, chosen_list = {}, []
    for process in fight_process:
        fighters = match_daily_fighters(sid, uid, heros, process, chosen_list)
        all_fighters[process] = fighters

        chosen_list.extend([fighter["uid"] for fighter in fighters.values()])

    return all_fighters

def match_daily_fighters(sid, uid, heros, process, chosen_list=[]):
    """匹配每日试炼对手数据

    Args:
        uid 角色ID
        heros 机甲数据
        process 进度
        chosen_list 已经被选中的对手需要排重
    """
    cfg = game_config.trial_cfg.get(process)
    max_fight = hero_helper.max_six_fights(heros)

    fighters = []
    chosen_uids = copy.copy(chosen_list)

    for index, item in cfg["items"].items():
        fighter_rule_cfg = game_config.trial_fighter_rule_cfg.get(item[0])
        matchers = [
                        "match_fighter_from_fight_rank(sid, uid, max_fight, fighter_rule_cfg, chosen_uids)",
                        "match_fighter_from_arena(sid, uid, fighter_rule_cfg, chosen_uids)",
                        "match_fighter_from_arena_last(sid, uid, chosen_uids)",
                    ]

        fighter_id, match_index = None, 0
        while (not fighter_id) and (match_index <= 2):
            fighter_id = eval(matchers[match_index])
            match_index += 1

        fighter = build_trial_fighter_data(sid, fighter_id)
        chosen_uids.append(fighter_id)
        fighters.append(fighter)

    fighters = sorted(fighters, key=lambda x:x["fight"])
    final_fighters = {} # {1: fighters[0], 2: fighters[1], 3: fighters[2]}
    for index, fighter in enumerate(fighters):
        final_fighters[index+1] = fighter

    return final_fighters

def match_fighter_from_fight_rank(sid, my_uid, fight, fighter_rule_cfg, chosen_uids):
    """从竞技场战力榜上匹配对手
    """
    start, end = fighter_rule_cfg["fight_rule"][0] * fight, fighter_rule_cfg["fight_rule"][1] * fight
    uid_list = rank_service.get_trial_fighters(sid, start, end)

    if not uid_list:
        return None
    else:
        uids = [uid for uid in uid_list if uid != my_uid and uid not in chosen_uids]
        if not uids:
            return None
        else:
            return random.choice(uids)

def match_fighter_from_arena(sid, my_uid, fighter_rule_cfg, chosen_uids):
    """从竞技场匹配对手
    """
    myrank = ArenaService.get_user_rank(sid, my_uid)
    start, end = myrank + fighter_rule_cfg["arena_rank_rule"][0], myrank + fighter_rule_cfg["arena_rank_rule"][1]

    uid_list = ArenaService.get_trial_fighters(sid, start, end)

    if not uid_list:
        return None
    else:
        uids = [uid for uid in uid_list if (uid != my_uid) and (uid not in chosen_uids)]
        if not uids:
            return None
        else:
            return random.choice(uids)

def match_fighter_from_arena_last(sid, my_uid, chosen_uids):
    """指定竞技场的最后对手
    """
    uid_list = ArenaService.get_trial_fighters2(sid)

    if not uid_list:
        return None
    else:
        uids = [uid for uid in uid_list if uid != my_uid and (uid not in chosen_uids)]
        if not uids:
            return None
        else:
            return random.choice(uids)

def build_trial_fighter_data(sid, uid):
    """构造试炼对手数据
    """
    fighter = {}
    fighter["uid"] = uid

    # 判断是否是机器人
    if uid.startswith("robot_"):
        robot_data = ArenaService.get_robot_data(sid, uid)
        fighter["name"] = robot_data["name"]

        robot_index = int(uid[6:])
        cfg_key = min([index for index in game_config.arena_formation_index_cfg if index >= robot_index])

        fighter["fight"] = game_config.arena_formation_fight_cfg[cfg_key]
    else:
        user = User.get(uid)
        if isinstance(user, User):
            fighter['name'] = user.name
            fighter['avatar'] = user.avatar
            fighter['array'] = user_helper.build_arena_hero_euqip_skill(user)
            fighter['talents'] = user.talent.talents
            fighter['warship'] = user_helper.build_warship_data(user.warship.ships, user.warship.team)
            fighter['fight'] = user.arena.fight

    return fighter
