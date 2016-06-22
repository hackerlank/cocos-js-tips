#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      副本逻辑
# @end
# @copyright (C) 2015, kimech

import time
import random
import logging

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import hero as hero_logic
from apps.logics import mall as mall_logic
from apps.logics import package as pack_logic

from apps.services import rank as rank_service
from apps.services.notice import NoticeService

from .helpers import act_helper
from .helpers import user_helper
from .helpers import common_helper
from .helpers import mission_helper

from apps.services.statistics import Statictics as stat_service

# 副本冷却时间30s
MISSION_CD = 10

# 随机商店冷却时间
MYSTERY_SHOP_CD = 6 * 3600

# 副本类型
MISSION_TYPE_PT = 1
MISSION_TYPE_JY = 2
MISSION_TYPE_EM = 3

def enter(context):
    """进入副本

    Args:
        mission_id 副本ID
    """
    ki_user = context.user
    mission_id = context.get_parameter("mission_id")
    fight = context.get_parameter("fight")

    extra = ki_user.mission.extra_data
    if extra["last_mission"] != 0:
        now = int(time.time())
        if now - extra["last_mission"] <= MISSION_CD:
            context.result['mc'] = MsgCode['MissionTooMany']
            return

    cfg = game_config.mission_base_cfg.get(mission_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['MissionNotExist']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    if not user_logic.check_game_values1(ki_user, energy=cfg["energy"]):
        context.result['mc'] = MsgCode['PowerNotEnough']
        return

    if cfg["need_level"] > ki_user.game_info.role_level:
        context.result['mc'] = MsgCode['UserLevelTooLow']
        return

    if cfg["need_mission"] and _check_need_mission(cfg["need_mission"], ki_user.mission.missions):
        context.result['mc'] = MsgCode['MissionCondsNotEnough']
        return

    if cfg["type"] in [MISSION_TYPE_JY, MISSION_TYPE_EM]:
        mission_daily_data = ki_user.daily_info.mission_info
        daily = mission_daily_data.get(mission_id, {})
        if daily and daily["past_times"] >= cfg["daily_limit"]:
            context.result['mc'] = MsgCode['MissionTimesError']
            return

    # 战力校验
    if (mission_id not in ki_user.mission.missions) and (not user_helper.check_user_fight(ki_user, fight)):
        context.result['mc'] = MsgCode['UserFightCheckFailed']
        return

    # 进入副本成功。更新数据
    ki_user.mission.enter(mission_id)

    # 失败或没打完同样扣体力，加经验。进入副本时预扣体力，防止玩家中途退出游戏
    energy_role_exp = cfg["energy"] / 3
    user_logic.consume_game_values1(ki_user, energy=energy_role_exp)
    user_logic.add_game_values(ki_user, {4: energy_role_exp})

    context.result['mc'] = MsgCode['MissionEnterSucc']

def past(context):
    """副本结算

    Args:
        mission_id  副本ID
        star  获得星星数量
    """
    ki_user = context.user
    mission_id = context.get_parameter("mission_id")
    star = context.get_parameter("star")

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    if star < 0 or star > 3:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    extra = ki_user.mission.extra_data
    if extra["last_mission"] != mission_id:
        context.result['mc'] = MsgCode['MissionNotIn']
        return

    # =========  检测完毕  ============
    # 获得物品
    cfg = game_config.mission_base_cfg.get(mission_id)
    # 随机获得物品数量
    awards_num = common_helper.weight_random(cfg["awards_num"])
    awards_pack_list = mission_helper.random_mission_award(cfg["awards_lib"], awards_num)
    awards = [game_config.item_pack_cfg.get(pack_id) for pack_id in awards_pack_list]

    # 扣除其余体力
    energy_role_exp = cfg["energy"] / 3 * 2

    # 增加玩家经验
    user_logic.consume_game_values1(ki_user, energy=energy_role_exp)
    user_logic.add_game_values(ki_user, {4: energy_role_exp, 1: cfg["gold"]})

    heros = [hero_id for hero_id in ki_user.array.mission if hero_id]
    hero_logic.hero_add_exp(ki_user, heros, cfg["hero_exp"])

    is_first_pass = mission_id not in ki_user.mission.missions
    # 第一次通关送机甲碎片和钻石
    if is_first_pass:
        awards.append(cfg["chips"])
        awards.append(cfg["diamonds"])

    pack_logic.add_items(ki_user, common_helper.handle_pack_items(awards))

    # 【日志统计】玩家副本通关进度
    try:
        if is_first_pass:
            stat_service.mission(ki_user, mission_id, cfg["type"])
    except Exception,e:
        logging.error(e)

    ki_user.mission.past(mission_id, star)
    # 精英和噩梦副本进入每日数据统计
    if cfg["type"] in [MISSION_TYPE_JY, MISSION_TYPE_EM] and star != 0:
        handle_daily_data(ki_user, mission_id, 1)

    # 更新副本得星排行库中的数据
    check_update_star_rank(ki_user)
    # 更新运维活动数据
    act_helper.update_after_past_mission(ki_user, mission_id)

    if cfg["type"] == MISSION_TYPE_EM and star >= 3:
        try:
            trigger = {'uid': ki_user.uid, 'name': ki_user.name}
            NoticeService.broadcast(ki_user.sid, 16, trigger, mission_id)
        except Exception,e:
            logging.error("【恶魔副本三星】炫耀广播发生错误。")

    show_mystery_shop = random_mystery_shop(ki_user.mall.mystery)
    if show_mystery_shop:
        # 刷新随机商店物品
        show_mystery_time = mall_logic.refresh_mission_mystery_shop(ki_user)
    else:
        show_mystery_time = 0

    context.result["data"] = {}
    context.result["data"]["mystery_shop"] = {"show": show_mystery_shop, "time": show_mystery_time}
    context.result["data"]["item_packs"] = awards_pack_list
    context.result["data"]["chips"] = cfg["chips"] if is_first_pass else {}
    context.result["data"]["diamonds"] = cfg["diamonds"] if is_first_pass else {}

def reset(context):
    """重置精英副本次数

    Args:
        mission_id  副本ID

    """
    ki_user = context.user
    mission_id = context.get_parameter("mission_id")

    cfg = game_config.mission_base_cfg.get(mission_id, {})
    if not cfg or cfg["type"] not in [MISSION_TYPE_JY, MISSION_TYPE_EM]:
        context.result['mc'] = MsgCode['MissionIllegal']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    mission_daily_data = ki_user.daily_info.mission_info
    daily = mission_daily_data.get(mission_id, {})
    if not daily or daily["past_times"] != cfg["daily_limit"]:
        context.result['mc'] = MsgCode['MissionTimesExist']
        return

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    if daily["reset_times"] >= vip_cfg["reset_mission_times"]:
        context.result['mc'] = MsgCode['MissionResetTimesEmpty']
        return

    consume_cfg = game_config.user_buy_refresh_cfg.get(daily["reset_times"]+1)
    if not consume_cfg:
        last = max(game_config.user_buy_refresh_cfg.keys())
        consume_cfg = game_config.user_buy_refresh_cfg.get(last)

    if not user_logic.check_game_values1(ki_user, diamond=consume_cfg["refresh_mission"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # =========  检测完毕  ============
    user_logic.consume_game_values1(ki_user, diamond=consume_cfg["refresh_mission"])
    ki_user.daily_info.reset_jy_mission(mission_id)

    context.result['mc'] = MsgCode['MissionResetSucc']

def mission_award(context):
    """领取副本首通就奖励和三星奖励

    Args:
        mission_id 副本ID
        award_type 奖励类型 1-首通礼包 2-三星礼包
    """
    ki_user = context.user
    mission_id = context.get_parameter("mission_id")
    award_type = context.get_parameter("award_type")

    if award_type not in [1,2]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cfg = game_config.mission_base_cfg.get(mission_id, {})
    if not cfg:
        context.result['mc'] = MsgCode['MissionNotExist']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    ms_data = ki_user.mission.get_mission_by_id(mission_id)
    if not ms_data:
        context.result['mc'] = MsgCode['MissionNoPass']
        return

    if award_type == 1:
        if ms_data["first_award"]:
            context.result['mc'] = MsgCode['MissionFirstAwarded']
            return
        else:
            pack_logic.add_items(ki_user, cfg["first_award"])
            ki_user.mission.get_mission_award(mission_id, award_type)
    else:
        if ms_data["best_award"]:
            context.result['mc'] = MsgCode['MissionBestAwarded']
            return
        else:
            pack_logic.add_items(ki_user, cfg["best_award"])
            ki_user.mission.get_mission_award(mission_id, award_type)

    context.result['mc'] = MsgCode['MissionAwardSucc']

def chapter_award(context):
    """领取章节星星奖品箱子

    Args:
        chapter_type 章节类型
        chapter_id 章节ID
        star 几星奖品
    """
    ki_user = context.user

    chapter_type = context.get_parameter("chapter_type")
    chapter_id = context.get_parameter("chapter_id")
    star = context.get_parameter("star")

    key = "%s-%s" % (chapter_type, chapter_id)
    cfg = game_config.mission_main_cfg.get(key, {})
    if (not cfg) or (not cfg["awards"].get(star, {})):
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if not _check_module_open(chapter_type, ki_user.game_info.role_level, 2):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    data = ki_user.mission.get_chapter_by_type_id(chapter_type, chapter_id)
    if not data:
        context.result['mc'] = MsgCode['MissionChapterNull']
        return

    if star > data["star"]:
        context.result['mc'] = MsgCode['MissionStarNotEnough']
        return

    if star in data["got_award"]:
        context.result['mc'] = MsgCode['MissionChapterAwarded']
        return

    awards = game_config.item_pack_cfg.get(cfg["awards"][star])
    pack_logic.add_items(ki_user, awards)
    ki_user.mission.get_chapter_awards(key, star)

    context.result['mc'] = MsgCode['MissionAwardSucc']

def hangup(context):
    """挂机扫荡

    Args:
        mission_id   扫荡目标副本ID
        htimes   扫荡次数
    """
    ki_user = context.user

    mission_id = context.get_parameter("mission_id")
    htimes = context.get_parameter("htimes")

    cfg = game_config.mission_base_cfg.get(mission_id)
    if (not cfg) or (cfg["type"] not in [MISSION_TYPE_PT, MISSION_TYPE_JY]) or \
       (htimes > 10) or (htimes <= 0):
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if not _check_module_open(mission_id, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    if htimes > 1 and not vip_cfg["open_ten_hangup"]:
        context.result['mc'] = MsgCode['UserVipTooLow']
        return

    need_energy = cfg["energy"] * htimes
    if not user_logic.check_game_values1(ki_user, energy=need_energy):
        context.result['mc'] = MsgCode['MissionEnergyNotEnough']
        return

    mdata = ki_user.mission.get_mission_by_id(mission_id)
    if not mdata or mdata["star"] != 3:
        context.result['mc'] = MsgCode['MissionStarNotEnough']
        return

    if cfg["type"] in [MISSION_TYPE_JY]:
        mission_daily_data = ki_user.daily_info.mission_info
        daily = mission_daily_data.get(mission_id, {})
        used_times = 0 if not daily else daily["past_times"]
        if used_times + htimes > cfg["daily_limit"]:
            context.result['mc'] = MsgCode['MissionTimesError']
            return

    # 计算收获
    total_awards = {}
    _total_awards = []
    show_mystery_shop = 0
    for i in xrange(htimes):
        # 副本正常掉落
        _awards_num = common_helper.weight_random(cfg["awards_num"])
        _awards1 = mission_helper.random_mission_award(cfg["awards_lib"], _awards_num)

        # 副本扫荡额外掉落
        _awards2 = []
        for award in cfg["hangup_awards_lib"]:
            rate = cfg["hangup_awards_lib"][award]
            if random.random() <= rate:
                _awards2.append(award)

        for pack in _awards1 + _awards2:
            _total_awards.append(game_config.item_pack_cfg.get(pack))

        if not show_mystery_shop:
            show_mystery_shop = random_mystery_shop(ki_user.mall.mystery)

        total_awards[i+1] = {}
        total_awards[i+1]["normal"] = _awards1
        total_awards[i+1]["extra"] = _awards2

    user_logic.consume_game_values1(ki_user, energy=need_energy)    # 扣除体力
    pack_logic.add_items(ki_user, common_helper.handle_pack_items(_total_awards))   #  增加物品
    user_logic.add_game_values(ki_user, {4: need_energy, 1: htimes * cfg["gold"]})   # 加经验，金币

    # 更新运维活动数据
    act_helper.update_after_hangup_mission(ki_user, mission_id, htimes)

    # 精英和噩梦副本进入每日数据统计
    if cfg["type"] in [MISSION_TYPE_JY]:
        handle_daily_data(ki_user, mission_id, htimes)

    # 刷新随机商店物品
    if show_mystery_shop:
        show_mystery_time = mall_logic.refresh_mission_mystery_shop(ki_user)
    else:
        show_mystery_time = 0

    context.result["data"] = {}
    context.result["data"]["mystery_shop"] = {"show": show_mystery_shop, "time": show_mystery_time}
    context.result["data"]["goods"] = total_awards

# ========================= MODULE API =============================
def _check_module_open(arg, role_level, check_type=1):
    """检测功能是否开启

    Args:
        arg :副本ID or 章节类型
        role_level :玩家等级

    Return:
        bool
    """
    if check_type == 1:
        cfg = game_config.mission_base_cfg.get(arg)
        ctype = cfg["type"]
    else:
        ctype = arg

    if ctype == MISSION_TYPE_PT:
        func_id = 4000
    elif ctype == MISSION_TYPE_JY:
        func_id = 4001
    else:
        func_id = 4002

    open_level = game_config.user_func_cfg.get(func_id, 999)
    if open_level > role_level:
        return False
    else:
        return True

def handle_daily_data(user, mission_id, times):
    """处理需要进入每日数据统计的数据

    比如精英副本和噩梦副本的每日通关次数，包含扫荡

    Args:
        user  用户
        mission_id  副本Id
        times  次数
    """
    mission_daily_data = user.daily_info.mission_info
    daily = mission_daily_data.get(mission_id, {})
    if daily:
        daily["past_times"] += times
    else:
        daily_data = {}
        daily_data["past_times"] = times
        daily_data["reset_times"] = 0

        mission_daily_data[mission_id] = daily_data

    user.daily_info.put()

def _check_need_mission(need_missions, past_missions):
    for need in need_missions:
        if need and need not in past_missions:
            return True

    return False

def check_update_star_rank(user):
    """更新副本得星排行库中的数据
    """
    total_stars = sum([mdata["star"] for mdata in user.mission.missions.itervalues()])
    rank_service.update_rank(user.sid, rank_service.RANK_MISSION_STAR, user.uid, total_stars)

def random_mystery_shop(old):
    """
    """
    now = int(time.time())
    if old["last_refresh"] + MYSTERY_SHOP_CD >= now:
        return 0

    # 出现概率0.05
    return 1 if random.random() <= 0.05 else 0

