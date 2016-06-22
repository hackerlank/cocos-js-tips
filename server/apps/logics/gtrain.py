#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-12-30 21:11:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   公会训练所接口:
#
# @end
# @copyright (C) 2015, kimech

import time
import copy

from apps.configs import game_config
from apps.configs.msg_code import MsgCode
from apps.services.group import GroupService
from apps.logics import user as user_logic
from apps.logics import system as sys_logic

from apps.models.user import User

GROUP_TRAIN_HELP_TIMES = 6      # 主动帮助别人次数
GROUP_TRAIN_HELP_TIMES1 = 6     # 被别人帮助次数
GROUP_TRAIN_HELP_GOLD = 20000

# ========================= GAME API ==============================
def info(context):
    """训练所信息
    """
    ki_user = context.user
    group_id = ki_user.group.group_id

    if not judge_open_train(ki_user.sid, group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    group_data = GroupService.find(ki_user.sid, group_id)
    gcfg = game_config.group_cfg.get(group_data["level"])
    ids = [i for i in ki_user.group.train_list if i not in [0,-1]]

    data = {}
    data["hero_add_exps"] = sys_logic.handle_group_train_heros(ids, ki_user, gcfg["train_exp"])
    data["state"] = ki_user.group.train_list
    data["info"] = ki_user.group.train_dict

    context.result["data"] = data

def unlock(context):
    """解锁训练槽
    """
    ki_user = context.user

    slot = context.get_parameter("slot")

    if not judge_open_train(ki_user.sid, ki_user.group.group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    slot_id = slot - 1
    slot_state = ki_user.group.train_list[slot_id]
    if slot_state != -1:
        context.result['mc'] = MsgCode['GroupTrainSlotUnlocked']
        return

    cfg = game_config.group_tra_cfg.get(slot, {})
    if not cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if cfg["open_level"] > ki_user.game_info.role_level:
        context.result['mc'] = MsgCode['UserLevelTooLow']
        return

    if cfg["vip_level"] > ki_user.game_info.vip_level:
        context.result['mc'] = MsgCode['UserVipTooLow']
        return

    if not user_logic.check_game_values1(ki_user, diamond=cfg["diamond"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=cfg["diamond"]) # 扣款

    ki_user.group.open_train_slot(slot_id)

    context.result['mc'] = MsgCode['GroupTrainSlotUnlockSucc']

def fill(context):
    """填充
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    slot = context.get_parameter("slot")

    if not judge_open_train(ki_user.sid, ki_user.group.group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    slot_id = slot - 1
    slot_state = ki_user.group.train_list[slot_id]
    if slot_state == -1:
        context.result['mc'] = MsgCode['GroupTrainSlotLocked']
        return

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    ki_user.group.set_express_hero(ki_user.sid, ki_user.group.group_id, ki_user.uid, hero_id, slot_id)

    context.result['mc'] = MsgCode['GroupTrainFillSucc']

def group_train_info(context):
    """获取社团训练所面板数据
        1.当前已使用加速次数
        2.被动加速次数
        3.被加速日志
        4.成员列表
    """
    ki_user = context.user

    group_id = ki_user.group.group_id

    if not judge_open_train(ki_user.sid, group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    data = {}
    data["times"] = ki_user.daily_info.group_train_express_times
    data["times1"] = GroupService.get_train_pos_times(ki_user.sid, group_id, ki_user.uid)
    data["logs"] = GroupService.get_train_logs(ki_user.sid, group_id, ki_user.uid)
    data["members"] = GroupService.train_members(ki_user.sid, group_id, ki_user.uid)

    context.result["data"] = data

def members_train(context):
    """获取社团成员数据
    """
    ki_user = context.user

    uid = context.get_parameter("uid")

    group_id = ki_user.group.group_id
    if not judge_open_train(ki_user.sid, group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    member_data = GroupService.get_member_info_by_uid(ki_user.sid, group_id, uid)
    # 检测目标是否在公会
    if not member_data:
        context.result['mc'] = MsgCode['GroupMemberNotExist']
        return

    user = User.get(uid)
    if not isinstance(user, User):
        context.result['mc'] = MsgCode['UserNotExist']
        return
    else:
        data = {}
        data["state"] = user.group.train_list
        ids = [i for i in user.group.train_list if i not in [0,-1]]
        heros = {}
        group_data = GroupService.find(ki_user.sid, group_id)
        for hid in ids:
            heros[hid] = count_group_train_hero(hid, user, group_data["level"])

        data["heros"] = heros

        context.result["data"] = data

def help(context):
    """帮助其它社员加速
    """
    ki_user = context.user

    uid = context.get_parameter("uid")
    hero_id = context.get_parameter("hero_id")

    if not judge_open_train(ki_user.sid, ki_user.group.group_id):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    # 不能给自己加速啊！！！
    if ki_user.uid == uid:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if ki_user.daily_info.group_train_express_times >= GROUP_TRAIN_HELP_TIMES:
        context.result['mc'] = MsgCode['GroupTrainTimesMax']
        return

    group_id = ki_user.group.group_id
    member_data = GroupService.get_member_info_by_uid(ki_user.sid, group_id, uid)
    # 检测目标是否在公会
    if not member_data:
        context.result['mc'] = MsgCode['GroupMemberNotExist']
        return

    user = User.get(uid)
    if not isinstance(user, User):
        context.result['mc'] = MsgCode['UserNotExist']
        return
    else:
        helped_times = int(GroupService.get_train_pos_times(ki_user.sid, group_id, uid))
        if helped_times >= GROUP_TRAIN_HELP_TIMES1:
            context.result['mc'] = MsgCode['GroupTrainHisTimesMax']
            return

        if hero_id not in user.group.train_list:
            context.result['mc'] = MsgCode['GroupTrainHeroNotOn']
            return

        GroupService.update_train_express_times(ki_user.sid, group_id, uid, hero_id, ki_user.name)

        user_logic.add_game_values(ki_user, {1: GROUP_TRAIN_HELP_GOLD})

        ki_user.daily_info.group_train_express_times += 1
        ki_user.daily_info.put()

    context.result['mc'] = MsgCode['GroupTrainHelpOtherSucc']

# ========================= MODULE API ==============================

# ========================= INTERNAL API ==============================
def judge_open_train(sid, group_id):
    """判断训练所是否开启
    """
    group_data = GroupService.find(sid, group_id)
    if group_data:
        gcfg = game_config.group_cfg.get(group_data["level"], {})

        # return gcfg["open_train"] == 1
        return True
    else:
        return False

def count_group_train_hero(hero_id, user, group_level):
    """计算训练所姬甲当前经验
    """
    hero = user.hero.heros[hero_id]
    tmp_exp = hero["exp"]
    max_exp = game_config.hero_level_exp_cfg.get(hero["level"]+1, None)
    if not max_exp:
        return tmp_exp

    # 经验已经最大，更新时间改为当前
    if hero["level"] >= user.game_info.role_level and tmp_exp >= max_exp:
        return tmp_exp
    else:
        now = int(time.time())
        gcfg = game_config.group_cfg.get(group_level, {})
        if not gcfg:
            return tmp_exp

        interval_minutes = int(now - user.group.train_dict[hero_id]) / 60
        # 读取别人帮我加速的次数
        express_times = GroupService.get_train_hero_times(user.sid, user.group.group_id, user.uid, hero_id)
        add_exp = (interval_minutes + int(express_times) * 30) * gcfg["train_exp"]

        if tmp_exp + add_exp > max_exp:
            tmp_exp = max_exp
        else:
            tmp_exp += add_exp

        return tmp_exp
