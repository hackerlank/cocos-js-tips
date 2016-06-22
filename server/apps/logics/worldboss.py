#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 19:46:56
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     世界BOSS业务接口
# @end
# @copyright (C) 2015, kimech

import time

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.services.mail import MailService
from apps.services.worldboss import BossService

from .helpers import user_helper
from .helpers import common_helper

from apps.configs import rediskey_config
from apps.logics import user as user_logic

WORLD_BOSS_CD = 60
WORLD_BOSS_ARRAY_TYPE = 9
WORLD_BOSS_CLEAN_CD_DIAMOND = 20
WORLD_BOSS_SUPPORT_GOLD = 10000
WORLD_BOSS_START_TIME = 2130
WORLD_BOSS_CONTINU_MINUTES = 15

# ========================= GAME API ==============================
def info(context):
    """世界BOSS信息
    """
    ki_user = context.user

    data = {}
    data["info"] = build_boss_info_s2c(BossService.get(ki_user.sid))
    data["etimes"] = ki_user.daily_info.boss_encourage_times
    data["cd"] = ki_user.daily_info.boss_last_fight
    data["supported"] = ki_user.daily_info.boss_supported
    data["array"] = ki_user.array.get_worldboss_array()

    context.result["data"] = data

def rank(context):
    """获取排行榜数据

    Args:
        rtype 排行榜类型 1 - 今日排名 2 - 总排名 3 - 英雄圣殿 4 - 昨日榜单
        start 排行榜起始位置
        end 排行榜结束位置
    """
    ki_user = context.user

    rtype = context.get_parameter("rtype")
    start = context.get_parameter("start")
    end = context.get_parameter("end")

    data = {}
    data["rank_data"] = BossService.rank(rtype, ki_user.sid, start, end)
    data["myrank"], data["mydmg"] = BossService.myrank(rtype, ki_user.sid, ki_user.uid)

    context.result["data"] = data

def enter(context):
    """开始挑战
    """
    ki_user = context.user

    cd = ki_user.daily_info.boss_last_fight
    if int(time.time()) <= cd + WORLD_BOSS_CD:
        context.result['mc'] = MsgCode['BossInCD']
        return

    if int(time.strftime("%H%M")) < WORLD_BOSS_START_TIME:
        context.result['mc'] = MsgCode['BossNotStart']
        return

    alive = BossService.alive(ki_user.sid)
    if not alive or (WORLD_BOSS_START_TIME + WORLD_BOSS_CONTINU_MINUTES <= int(time.strftime("%H%M"))):
        context.result['mc'] = MsgCode['BossEnd']
        return

    fight = context.get_parameter("fight")
    if not user_helper.check_user_fight(ki_user, fight, WORLD_BOSS_ARRAY_TYPE):
        context.result['mc'] = MsgCode['UserFightCheckFailed']
        return

    ki_user.ext_info.boss_enter_tag = 1
    ki_user.ext_info.put()

    context.result['mc'] = MsgCode['BossEnterSucc']

def fight(context):
    """挑战
    """
    ki_user = context.user

    enter_tag = ki_user.ext_info.boss_enter_tag
    if not enter_tag:
        context.result['mc'] = MsgCode['InvalidOperation']
        return

    dmg = context.get_parameter("dmg")
    BossService.fight(ki_user.sid, ki_user.uid, dmg)

    pack_logic.add_items(ki_user, {1: 50000 + int(dmg / 10)})

    ki_user.daily_info.boss_last_fight = int(time.time())
    ki_user.daily_info.put()

    ki_user.ext_info.boss_enter_tag = 0
    ki_user.ext_info.put()

    context.result['mc'] = MsgCode['BossFightSucc']

def encourage(context):
    """鼓舞
    """
    ki_user = context.user

    alive = BossService.alive(ki_user.sid)
    if not alive:
        context.result['mc'] = MsgCode['BossEnd']
        return

    times = ki_user.daily_info.boss_encourage_times
    cfg = game_config.boss_encourage_cfg.get(times+1, {})
    if not cfg:
        context.result['mc'] = MsgCode['BossEncourageFailed']
        return

    if not user_logic.check_game_values1(ki_user, diamond=cfg["diamond"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=cfg["diamond"]) # 扣款

    ki_user.daily_info.boss_encourage_times += 1
    ki_user.daily_info.put()

    context.result['mc'] = MsgCode['BossEncourageSucc']

def cleancd(context):
    """清除CD
    """
    ki_user = context.user

    alive = BossService.alive(ki_user.sid)
    if not alive:
        context.result['mc'] = MsgCode['BossEnd']
        return

    if int(time.time()) > ki_user.daily_info.boss_last_fight + WORLD_BOSS_CD:
        context.result['mc'] = MsgCode['BossCleanCDFailed']
        return

    if not user_logic.check_game_values1(ki_user, diamond=WORLD_BOSS_CLEAN_CD_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=WORLD_BOSS_CLEAN_CD_DIAMOND) # 扣款

    ki_user.daily_info.boss_last_fight = 0
    ki_user.daily_info.put()

    context.result['mc'] = MsgCode['BossCleanCDSucc']

def support(context):
    """支持昨日排行榜的玩家
    """
    ki_user = context.user

    now = int(time.strftime('%H%M'))
    if now >= WORLD_BOSS_START_TIME:
        context.result['mc'] = MsgCode['BossSupportEnd']
        return

    if ki_user.daily_info.boss_supported:
        context.result['mc'] = MsgCode['BossSupportRepeated']
        return

    if not user_logic.check_game_values1(ki_user, gold=WORLD_BOSS_SUPPORT_GOLD):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return

    uid = context.get_parameter("uid")
    result = BossService.support(ki_user.sid, uid, ki_user.uid)
    if not result:
        context.result['mc'] = MsgCode['BossSupportFailed']
        return

    user_logic.consume_game_values1(ki_user, gold=WORLD_BOSS_SUPPORT_GOLD) # 扣款

    ki_user.daily_info.boss_supported = uid
    ki_user.daily_info.put()

    context.result['mc'] = MsgCode['BossSupportSucc']

# =========================================================================
def build_boss_info_s2c(data):
    """
    """
    data_s2c = {}
    for k,v in data.items():
        if k in ["id", "type", "hp", "lose_hp", "days", "name", "level"]:
            data_s2c[k] = v

    return data_s2c
