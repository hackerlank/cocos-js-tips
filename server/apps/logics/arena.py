#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-14 18:42:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     竞技场业务逻辑
# @end
# @copyright (C) 2015, kimech

import time
import logging

from apps.misc import utils
from apps.models.user import User
from apps.configs import game_config
from apps.configs import static_const
from apps.configs.msg_code import MsgCode
from apps.services.arena import ArenaService
from apps.services.group import GroupService
from apps.services.notice import NoticeService

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

from .helpers import act_helper
from .helpers import user_helper

ARENA_FIGHTING_CD = 600
ARENA_FIGHTING_DEFAULT_TIMES = 5
ARENA_CLEAN_CD_DIAMOND = 10

# ========================= GAME API ==============================
def info(context):
    """请求竞技场数据

    Args:

    Returns:
        myrank 玩家当前名次
        tops 当前竞技场前十名数据
        fighters 匹配到的4个对手数据
        challenge_times 今日挑战次数
        add_times 今日购买挑战次数
        admire_list 今日膜拜对手数据
        refresh_times 今日“换一批”次数
        last_fight 上次挑战时间戳
    """
    ki_user = context.user

    rank = ArenaService.get_user_rank(ki_user.sid, ki_user.uid)
    tops = ArenaService.top_ten(ki_user.sid)

    datas = {}
    datas["myrank"] = rank
    datas["array"] = ki_user.array.get_arena_array()

    #  ======================== update =======================
    # datas["challenge_times"] = ki_user.arena.daily_challenge_times
    # datas["add_times"] = ki_user.arena.daily_add_times
    # datas["last_fight"] = ki_user.arena.last_fight
    # datas["refresh_times"] = ki_user.arena.daily_refresh_times
    # datas["admire_list"] = ki_user.arena.daily_admire_list
    # datas["awarded_index"] = ki_user.arena.awarded_index
    # datas["daily_awarded_index"] = ki_user.arena.daily_awarded_index
    # datas["daily_scores"] = ki_user.arena.daily_scores
    # datas["max_rank"] = ki_user.arena.max_rank
    #  ======================== update =======================

    datas["tops"] = tops

    fighters = ki_user.arena.effective_fighters
    if not fighters:
        fighters = ArenaService.match_fighters(ki_user.sid, ki_user.uid, rank, ki_user.arena.win_times)
        ki_user.arena.put_fighters(fighters)

    datas["fighters"] = fighters

    # ki_user.arena.update_heartbeat_sign()

    context.result["data"] = datas

def admire(context):
    """膜拜某个前十对手

    Args:
        fighter_id 膜拜对象的UID

    Returns:
    """
    ki_user = context.user

    fighter_id = context.get_parameter("fighter_id")

    if fighter_id in ki_user.arena.daily_admire_list:
        context.result['mc'] = MsgCode['ArenaAlreadyAdmired']
        return

    ArenaService.admire(ki_user.sid, fighter_id)
    ki_user.arena.admire(fighter_id)
    pack_logic.add_items(ki_user, {1:2000})

    context.result["mc"] = MsgCode['ArenaAdmireSucc']

# def start(context):
#     """向别人发起挑战
#     """
#     ki_user = context.user

#     fighter_id = context.get_parameter("fighter_id")
#     fighter_rank = context.get_parameter("fighter_rank")

#     # 挑战CD尚未冷却,如果是购买的次数，取消CD，直接挑战
#     vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
#     if ki_user.arena.daily_add_times == 0 and now - ki_user.arena.last_fight < vip_cfg["arena_fight_cd"]:
#         context.result['mc'] = MsgCode['ArenaFightCD']
#         return

#     # 挑战次数已经用尽
#     total_times = ARENA_FIGHTING_DEFAULT_TIMES + ki_user.arena.daily_add_times
#     if ki_user.arena.daily_challenge_times >= total_times:
#         context.result['mc'] = MsgCode['ArenaFightTimesUseUp']
#         return

#     tmp_fighters = ki_user.arena.effective_fighters
#     fighter_ids = [f["uid"] for f in tmp_fighters]
#     myrank = ArenaService.get_user_rank(ki_user.sid, ki_user.uid)
#     if fighter_id not in fighter_ids:
#         if (myrank <= 20) and (fighter_rank <= 10):
#             if fighter_id not in ki_user.arena.daily_admire_list:
#                 context.result['mc'] = MsgCode['ArenaFighterNotAdmiredList']
#                 return
#         else:
#             context.result['mc'] = MsgCode['ArenaFighterNotInList']
#             return

#     is_matched = ArenaService.check_fighter_rank_matched(ki_user.sid, fighter_id, fighter_rank)
#     # 对手的排名已经变更，需要重新选择对手
#     if not is_matched:
#         index = fighter_ids
#         new_fighter = {}

#         context.result["data"] = {}
#         context.result["data"]["new_fighter"] = new_fighter
#         return

#     # 把对手和自己加入对战列表，防止中途有人挑战

def fighter_data(context):
    """获取对手的竞技场数据

    Args:
        fighter_id  # 对手的uid

    """
    fighter_id = context.get_parameter("fighter_id")

    if fighter_id.startswith("robot_"):
        context.result['mc'] = MsgCode['UserNotExist']
        return

    player = User.get(fighter_id)
    if not isinstance(player, User):
        context.result['mc'] = MsgCode['UserNotExist']
        return
    else:
        fighter = {}
        fighter['level'] = player.game_info.role_level
        fighter['array'] = user_helper.build_arena_hero_euqip_skill(player)
        fighter['talents'] = player.talent.talents
        fighter['warship'] = user_helper.build_warship_data(player.warship.ships, player.warship.team)
        fighter['group_name'] = GroupService.get_name_by_id(player.sid, player.group.group_id)

        context.result["data"] = fighter

def fight(context):
    """挑战结算

    当玩家向某人发起挑战时，对手的排名可能和最新的排名不同，
    则需要玩家重新请求对手数据

    Args:
        fighter_id  # 对手的uid
        fighter_rank  # 对手的当前排名
        result # 挑战结果
        logs # 挑战日志

    Returns:

    """
    ki_user = context.user

    fighter_id = context.get_parameter("fighter_id")
    fighter_rank = context.get_parameter("fighter_rank")
    result = context.get_parameter("result")
    logs = context.get_parameter("logs")
    fight = context.get_parameter("fight")

    now = int(time.time())
    # 不能挑战自己啊！！！
    if ki_user.uid == fighter_id:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    # 挑战CD尚未冷却,如果是购买的次数，取消CD，直接挑战
    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    if ki_user.arena.daily_add_times == 0 and now - ki_user.arena.last_fight < vip_cfg["arena_fight_cd"]:
        context.result['mc'] = MsgCode['ArenaFightCD']
        return

    # 挑战次数已经用尽
    total_times = ARENA_FIGHTING_DEFAULT_TIMES + ki_user.arena.daily_add_times
    if ki_user.arena.daily_challenge_times >= total_times:
        context.result['mc'] = MsgCode['ArenaFightTimesUseUp']
        return

    # 如果玩家在竞技场前二十名，膜拜完前十名之后可以直接挑战
    tmp_fighters = ki_user.arena.effective_fighters
    fighter_ids = [f["uid"] for f in tmp_fighters]
    myrank = ArenaService.get_user_rank(ki_user.sid, ki_user.uid)
    if fighter_id not in fighter_ids:
        if (myrank <= 20) and (fighter_rank <= 10):
            if fighter_id not in ki_user.arena.daily_admire_list:
                context.result['mc'] = MsgCode['ArenaFighterNotAdmiredList']
                return
        else:
            context.result['mc'] = MsgCode['ArenaFighterNotInList']
            return

    # 挑战结果在胜负之间
    if result not in [0,1]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    # 战力校验
    if not user_helper.check_user_fight(ki_user, fight, 2):
        context.result['mc'] = MsgCode['UserFightCheckFailed']
        return

    is_matched = ArenaService.check_fighter_rank_matched(ki_user.sid, fighter_id, fighter_rank)
    if not is_matched:
        # 对手的排名已经变更,并且对手不在前10名，找到该名次当前的对手数据
        if fighter_rank > 10:
            new_fighter = ArenaService.get_fighter_by_rank(ki_user.sid, fighter_rank)
            ki_user.arena.update_fighters(fighter_rank, new_fighter)

        context.result['mc'] = MsgCode['ArenaFighterRankChanged']
        return

    ki_user.arena.challenge(now, result)
     # 保存时玩家和对手当时的阵容数据
    ArenaService.save_replay(ki_user.sid, ki_user.uid, ki_user.name, ki_user.avatar, fighter_id, result, logs)

    # 胜利之后才会通知竞技服务去处理
    if result:
        best = ki_user.arena.max_rank
        new_rank = ArenaService.fight(ki_user.sid, ki_user.uid, fighter_id, result)
        new_fighters = ArenaService.match_fighters(ki_user.sid, ki_user.uid, new_rank, ki_user.arena.win_times+1)
        ki_user.arena.win(new_rank, new_fighters)

        # 更新活动中竞技场排名数据 达到新的名次高度
        if new_rank <= best:
            act_helper.update_after_arena_rank_update(ki_user, new_rank)

        try:
            if new_rank <= 10 and myrank != new_rank:
                trigger = {'uid': ki_user.uid, 'name': ki_user.name}
                NoticeService.broadcast(ki_user.sid, 15, trigger, new_rank)
        except:
            logging.error("【竞技场进入前十】炫耀广播发生错误。")

    # 挑战竞技场的活动
    act_helper.update_after_arena_fight(ki_user, result)

    context.result["mc"] = MsgCode['ArenaStartFightSucc']

def refresh(context):
    """刷新当前对手数据

    Args:

    Returns:
        tops 当前竞技场前十名数据
        fighters 匹配到的4个对手数据
    """
    ki_user = context.user

    used_times = ki_user.arena.daily_refresh_times
    consume_cfg = game_config.user_buy_refresh_cfg.get(used_times + 1, {})
    if not consume_cfg:
        last = max(game_config.user_buy_refresh_cfg.keys())
        consume_cfg = game_config.user_buy_refresh_cfg.get(last)

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    if (not consume_cfg) or (used_times >= vip_cfg["arena_refresh_times"]):
        context.result['mc'] = MsgCode['ArenaRefreshTimesUseUp']
        return

    if not user_logic.check_game_values1(ki_user, diamond=consume_cfg["arena_refresh"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 扣除消耗钻石
    user_logic.consume_game_values1(ki_user, diamond=consume_cfg["arena_refresh"])

    rank = ArenaService.get_user_rank(ki_user.sid, ki_user.uid)
    fighters = ArenaService.match_fighters(ki_user.sid, ki_user.uid, rank, ki_user.arena.win_times)
    ki_user.arena.refresh(fighters)

    datas = {}
    datas["myrank"] = rank
    datas["fighters"] = fighters
    datas["tops"] = ArenaService.top_ten(ki_user.sid)

    context.result["data"] = datas

def clean_cd(context):
    """清除挑战CD

    Args:

    Returns:

    """
    ki_user = context.user

    if not ki_user.arena.last_fight:
        context.result['mc'] = MsgCode['ArenaNotInCD']
        return

    if not user_logic.check_game_values1(ki_user, diamond=ARENA_CLEAN_CD_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 扣除消耗钻石
    user_logic.consume_game_values1(ki_user, diamond=ARENA_CLEAN_CD_DIAMOND)
    ki_user.arena.clean_cd()

    context.result["mc"] = MsgCode['ArenaCleanCDSucc']

def add_times(context):
    """购买竞技场挑战次数

    Args:

    Returns:
        mc
    """
    ki_user = context.user

    add_times = ki_user.arena.daily_add_times
    consume_cfg = game_config.user_buy_refresh_cfg.get(add_times + 1, {})
    if not consume_cfg:
        last = max(game_config.user_buy_refresh_cfg.keys())
        consume_cfg = game_config.user_buy_refresh_cfg.get(last)

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)

    if (not consume_cfg) or (add_times >= vip_cfg["arena_add_times"]):
        context.result['mc'] = MsgCode['ArenaAddTimesUseUp']
        return

    total_times = ARENA_FIGHTING_DEFAULT_TIMES + ki_user.arena.daily_add_times
    if total_times > ki_user.arena.daily_challenge_times:
        context.result['mc'] = MsgCode['ArenaChallengeTimesExist']
        return

    if not user_logic.check_game_values1(ki_user, diamond=consume_cfg["arena_add_times"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 扣除消耗钻石
    user_logic.consume_game_values1(ki_user, diamond=consume_cfg["arena_add_times"])
    ki_user.arena.add_times()

    context.result["mc"] = MsgCode['ArenaAddTimesSucc']

def award(context):
    """领取排名奖励

    Args:
        index 排名奖励索引

    Returns:
        mc
    """
    ki_user = context.user

    index = context.get_parameter("index")
    award_cfg = game_config.arena_awards_cfg.get(index, {})
    if not award_cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if award_cfg["need_rank"] < ki_user.arena.max_rank:
        context.result['mc'] = MsgCode['ArenaRankTooLow']
        return

    awarded = ki_user.arena.awarded_index
    if index in awarded:
        context.result['mc'] = MsgCode['ArenaAwarded']
        return

    pack_logic.add_items(ki_user, award_cfg["awards"])
    ki_user.arena.award(index)

    context.result["mc"] = MsgCode['ArenaGetAwardSucc']

def daily_award(context):
    """领取竞技场每日积分奖励

    Args:
        index 排名奖励索引
    Returns:
        mc
    """
    ki_user = context.user

    index = context.get_parameter("index")
    award_cfg = game_config.arena_daily_awards_cfg.get(index, {})
    if not award_cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if award_cfg["need_score"] > ki_user.arena.daily_scores:
        context.result['mc'] = MsgCode['ArenaScoreNotEnough']
        return

    awarded = ki_user.arena.daily_awarded_index
    if index in awarded:
        context.result['mc'] = MsgCode['ArenaAwarded']
        return

    pack_logic.add_items(ki_user, award_cfg["awards"])
    ki_user.arena.daily_award(index)

    context.result["mc"] = MsgCode['ArenaGetAwardSucc']

def history(context):
    """历史战报

    Args:

    Returns:
        history []
    """
    ki_user = context.user

    logs = ArenaService.get_replay(ki_user.sid, ki_user.uid)

    data = {}
    data["fight_logs"] = logs

    context.result["data"] = data

def replay(context):
    """播放战斗录像

    Args:

    Returns:

    """
    ki_user = context.user

    log_id = context.get_parameter("log_id")

    data = {}
    data["content"] = ArenaService.get_single_replay(ki_user.sid, ki_user.uid, log_id)

    context.result["data"] = data
