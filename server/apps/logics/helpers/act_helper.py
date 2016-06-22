#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-18 12:43:11
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     运维活动辅助接口
# @end
# @copyright (C) 2015, kimech

import time

from apps.misc import utils
from libs.rklib.core import app
from apps.configs import game_config
from apps.services import act as act_service
from apps.services.mail import MailService
from .act_class import *

TYPE_CLASS_MAPPING = {
    100: ActLogin,
    101: ActLoginSendMail,
    202: ActArenaRank,
    302: ActHaveHeros,
    303: ActReachStandardA,
    306: ActReachStandardA,
    310: ActReachStandardB,
    311: ActReachStandardB,
    320: ActReachStandardB,
    321: ActReachStandardB,
    322: ActReachStandardB,
    323: ActReachStandardB,
    324: ActReachStandardB,
    325: ActReachStandardA,
    326: ActReachStandardA,
    327: ActReachStandardA,
    328: ActReachStandardB,
    400: ActPassMission,
    401: ActTrial,

    309: ActReachStandardB,
    329: ActReachStandardB,
    701: ActChargeAct1,
    702: ActChargeAct1,
    900: ActDailySale,
    901: ActChargeLevelFund,

    501: ActDiamondGamble,

    330: ActReachStandardA,
    331: ActReachStandardA,
    332: ActReachStandardA,
    333: ActReachStandardA,
    334: ActReachStandardA,

    # 2016-05-19
    335: ActComplexTargets,
}

# 和登录操作挂钩的活动，比如登录有好礼
LOGIN_ACTS = [100,101,900]
# 和副本挂钩的活动，比如通关副本领奖
MISSION_ACTS = [400]
# 通关普通副本次数活动
MISSION_ACTS1 = [322]
# 通关精英副本次数活动
MISSION_ACTS2 = [323]
# 和消耗钻石挂钩的活动
USE_DIAMOND_ACTS = [310]
# 觉醒宝箱连连抽
MALL_PICK_ACTS = [311]
# 和挑战竞技场挂钩的活动
ARENA_FIGHT_ACTS = [320]
# 和挑战竞技场挑战积分挂钩的活动
ARENA_FIGHT_SCORE_ACTS = [324]
# 竞技场排名奖励
ARENA_RANK_ACTS = [202]
# 累计获得试炼积分达到指定数量
TRIAL_GOT_SCORES = [321]
# 完成其他活动计数达到一定数量
ACT_COMPLETE_NUMS = [328]
# 通关试炼指定层数
TRIAL_UPDATE_PROCESS = [401]

# 复杂类相关
COMPLEX_ACTS = [335]

# 钻石抽取姬甲达到指定数量
DIAMOND_PICK_HERO = [329]
# 累计充值钻石达到指定数量
CUMULATIVE_CHARGE_DIAMOND = [309]
# 累计充值人民币达到指定数量
CUMULATIVE_CHARGE_RMB = [334]
# 每日充值60领取奖品，非连续充值5日，每日达到60后，领取大奖
CHARGE_60_EVERY_DAY = [701]
# 每日充值RMB领取奖品，非连续充值5日，每日达到指定金额后，领取大奖
CHARGE_RMB_EVERY_DAY = [702]
# 特卖活动
PRIVATE_SALE_ACT = [900]
# 等级基金达到指定等级返利
LEVEL_FUND_ACT = [901]
# 钻石赌博
DIAMOND_GAMBLE = [501]

# 只展示活动面板 不用服务器计数
SPECIAL_ACTS = [200,201,300,600,902,903,904]
# 更新任务时  需要借助SID查询一些相关数据的活动
ACT_UPDATE_NEED_SID = [701,702,900]

# 充值活动列表
CHARGE_ACTS = [329,701,900,901]
# 只在领奖时检测任务完成条件的活动，平时不会主动更新数据状态
SPECIAL_ACTS1 = [302,303,306,325,326,327,330,331,332,333,901]

ACT_FINISHED = 1
# ====================================================================
def update_after_login(ki_user):
    """登录操作触发活动数据更新
    """
    data = utils.today()
    update_after_action(LOGIN_ACTS, ki_user, data)
    update_after_arena_rank_update(ki_user, ki_user.arena.max_rank)
    # 更新隔天状态
    update_after_charge(ki_user, 0, 0)

def update_after_past_mission(ki_user, data):
    """通关副本操作触发活动数据更新

    Args:
        data 副本ID
    """
    update_after_action(MISSION_ACTS, ki_user, data)
    cfg = game_config.mission_base_cfg.get(data, {})
    # 普通副本
    if cfg and cfg["type"] == 1:
        update_after_action(MISSION_ACTS1, ki_user, 1)
    elif cfg and cfg["type"] == 2:
        update_after_action(MISSION_ACTS2, ki_user, 1)
    else:
        pass

def update_after_hangup_mission(ki_user, mission_id, htimes):
    """通关普通、精英副本次数活动

    Args:
        mission_id 副本ID
        htimes 扫荡次数
    """
    update_after_action(MISSION_ACTS, ki_user, mission_id)
    cfg = game_config.mission_base_cfg.get(mission_id, {})
    # 普通副本
    if cfg and cfg["type"] == 1:
        update_after_action(MISSION_ACTS1, ki_user, htimes)
    elif cfg and cfg["type"] == 2:
        update_after_action(MISSION_ACTS2, ki_user, htimes)
    else:
        pass

def update_after_arena_fight(ki_user, result):
    """挑战竞技场触发刷新活动操作

    """
    update_after_action(ARENA_FIGHT_ACTS, ki_user, 1)
    score = 1 if not result else 2
    update_after_action(ARENA_FIGHT_SCORE_ACTS, ki_user, score)

def update_after_arena_rank_update(ki_user, new_rank):
    """挑战竞技场触发刷新活动操作

    """
    update_after_action(ARENA_RANK_ACTS, ki_user, new_rank)

def update_after_trial_process(ki_user, new_process, new_scores=0):
    """爬塔晋级&试炼积分

    """
    update_after_action(TRIAL_UPDATE_PROCESS, ki_user, new_process)
    if new_scores:
        update_after_action(TRIAL_GOT_SCORES, ki_user, new_scores)

def update_after_use_diamond(ki_user, data):
    """使用钻石操作触发活动数据更新

    Args:
        data 使用钻石数量
    """
    update_after_action(USE_DIAMOND_ACTS, ki_user, data)

def update_after_diamond_pick_hero(ki_user, data):
    """钻石抽取姬甲达到指定数量

    Args:
        data 钻石抽卡次数
    """
    update_after_action(DIAMOND_PICK_HERO, ki_user, data)

def update_after_mall_pick(ki_user, data):
    """觉醒宝箱抽卡次数达到指定数量

    Args:
        data 觉醒宝箱抽卡次数
    """
    update_after_action(MALL_PICK_ACTS, ki_user, data)

def update_after_charge(ki_user, diamond, money):
    """充值元宝

    Args:
        diamond 充值元宝数量（包含额外赠送的元宝）
        money 充值人民币
    """
    update_after_action(CHARGE_60_EVERY_DAY, ki_user, int(diamond))
    update_after_action(CUMULATIVE_CHARGE_DIAMOND, ki_user, int(diamond))

    update_after_action(CHARGE_RMB_EVERY_DAY, ki_user, int(money))
    update_after_action(CUMULATIVE_CHARGE_RMB, ki_user, int(money))

def update_after_buy_level_fund(ki_user, state):
    """等级基金

    Args:
        state 基金是否激活状态 0 - 未激活 1 - 激活
    """
    update_after_action(LEVEL_FUND_ACT, ki_user, state)

def update_after_diamond_gamble(ki_user):
    """钻石赌博
    """
    update_after_action(DIAMOND_GAMBLE, ki_user, 1)

def update_union_acts(ki_user, union_acts, data):
    """更新关联活动数据
    """
    for act_id in union_acts:
        act_cfg = game_config.activity_cfg.get(act_id, None)
        if not act_cfg:
            continue

        act_data = ki_user.activity.acts.get(act_id, {})
        if act_data and _check_need_update(ki_user.sid, act_id, act_data):
            TYPE_CLASS_MAPPING[act_cfg["type"]].update_after_action(act_id, act_data, data)

    # 更新之后保存数据
    ki_user.activity.put()

def update_complex_acts(ki_user, data):
    """装备升品后更新
    """
    update_after_action(COMPLEX_ACTS, ki_user, data)

def update_after_action(act_types, ki_user, data):
    """
    """
    acts = ki_user.activity.acts

    effective_acts = []
    for atype in act_types:
        effective_acts += game_config.activity_type_cfg.get(atype, [])

    for act_id in effective_acts:
        act_data = acts.get(act_id, {})
        if act_data and _check_need_update(ki_user.sid, act_id, act_data):
            act_cfg = game_config.activity_cfg.get(act_id)
            if act_cfg["type"] in ACT_UPDATE_NEED_SID:
                TYPE_CLASS_MAPPING[act_cfg["type"]].update_after_action(act_id, act_data, ki_user.sid, data)
            else:
                TYPE_CLASS_MAPPING[act_cfg["type"]].update_after_action(act_id, act_data, data)

            # # 圣诞活动，上线邮件发奖励
            # if act_cfg["type"] == 101 and act_data["canget"] != 0:
            #     step = 1
            #     award_cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, step))
            #     if award_cfg:
            #         MailService.send_game(ki_user.uid, 3002, [], award_cfg["awards"])
            #         act_data["awarded"] += act_data["canget"]
            #         act_data["canget"] = 0

            # 更新之后保存数据
            ki_user.activity.put()

def get_active_acts(sid, role_level):
    """获得激活状态中的活动
    """
    now = int(time.time())
    all_acts = act_service.all(sid)

    def is_valid(act_id):
        act_info = all_acts[act_id]
        cfg = game_config.activity_cfg.get(int(act_id), {})

        if act_info["start1"] <= now < act_info["end1"] and cfg and role_level >= cfg["open_level"]:
            return True
        else:
            return False

    filtered_acts = filter(is_valid, all_acts)

    return [int(act_id) for act_id in filtered_acts]

def get_active_act_info(sid, role_level):
    """获得激活状态中的活动信息
    """
    all_acts = act_service.all(sid)
    now = int(time.time())

    def is_valid(act_id):
        act_info = all_acts[act_id]
        cfg = game_config.activity_cfg.get(int(act_id), {})
        if act_info["start1"] <= now < act_info["end1"] and cfg and role_level >= cfg["open_level"]:
            return True
        else:
            return False

    filtered_acts = {}
    for act_id in all_acts:
        if is_valid(act_id):
            filtered_acts[act_id] = all_acts[act_id]

    return filtered_acts

def new_act_data_from_id(act_id):
    """根据活动ID初始化对应活动数据

    Args:
        act_id 活动ID

    Returns:
        act_data {}
    """
    act_cfg = game_config.activity_cfg.get(act_id)
    new_act_data = TYPE_CLASS_MAPPING[act_cfg["type"]].new()

    return new_act_data

def check_award_repeat(act_id, act_data, index):
    """检查是否重复领取奖励

    Args:
        act_id :活动ID
        act_data :活动数据
        index :奖项编号

    Returns:
        True / False
    """
    act_cfg = game_config.activity_cfg.get(act_id)
    result = TYPE_CLASS_MAPPING[act_cfg["type"]].check_award_repeat(act_data, index)

    return result

def check_award_can_get(act_id, act_data, index):
    """检测领取奖励条件是否以满足

    Args:
        act_id :活动ID
        act_data :活动数据
        index :奖项编号

    Returns:
        True / False
    """
    act_cfg = game_config.activity_cfg.get(act_id)
    result = TYPE_CLASS_MAPPING[act_cfg["type"]].check_award_can_get(act_data, index)

    return result

def update_after_award(act_id, act_data, index):
    act_cfg = game_config.activity_cfg.get(act_id)
    new_act = TYPE_CLASS_MAPPING[act_cfg["type"]].update_after_award(act_data, index)

    return new_act

# =========================== ACT CHECKER ============================
# 此处方法均用在需要玩家领取奖励时验证完成条件是否满足的任务
# 如：收集指定机甲，战力达标，等级达标等
def act_checker_300(player, cfg):
    """战力达标活动，前后端战力计算误差，暂时以前端的为准

    """
    return True

def act_checker_302(player, cfg):
    """收集指定机甲
    """
    conds = filter(lambda x: x, [cfg[attr] for attr in cfg.keys() if attr.startswith("cond_")])
    have_heros = [hero_id for hero_id in player.hero.heros]

    return len(set(conds).difference(have_heros)) == 0

def act_checker_303(player, cfg):
    """等级达标活动
    """
    return player.game_info.role_level >= cfg["cond_a"]

def act_checker_306(player, cfg):
    """获得4个3星格斗家
    """
    count = 0
    for hero in player.hero.heros.values():
        if hero["star"] >= cfg["cond_a"]:
            count += 1

    return count >= cfg["cond_b"]

def act_checker_326(player, cfg):
    """3个姬甲升级至绿+1品质
    """
    count = 0
    for hero in player.hero.heros.values():
        if hero["quality"] >= cfg["cond_a"]:
            count += 1

    return count >= cfg["cond_b"]

def act_checker_327(player, cfg):
    """10件装备升级至绿+1品质
    """
    count = 0
    for hero_equip in player.equip.equips.values():
        for equip in hero_equip.values():
            if equip["quality"] >= cfg["cond_a"]:
                count += 1

    return count >= cfg["cond_b"]

def act_checker_325(player, cfg):
    """20件装备升级到1星
    """
    count = 0
    for hero_equip in player.equip.equips.values():
        for equip in hero_equip.values():
            if equip["star"] >= cfg["cond_a"]:
                count += 1

    return count >= cfg["cond_b"]

def act_checker_901(player, cfg):
    """等级基金
    """
    return act_checker_303(player, cfg)

def act_checker_330(player, cfg):
    """S级姬甲星级达到指定数量
    """
    count = 0
    for hid, hero  in player.hero.heros.items():
        hcfg = game_config.hero_base_cfg.get(hid)
        if hcfg["talent"] >= cfg["cond_c"] and hero["star"] >= cfg["cond_a"]:
            count += 1

    return count >= cfg["cond_b"]

def act_checker_331(player, cfg):
    """A级姬甲星级达到指定数量
    """
    return act_checker_330(player, cfg)

def act_checker_332(player, cfg):
    """单个姬甲战力达到
    """
    return True

def act_checker_333(player, cfg):
    """副本得星总数
    """
    count = 0
    for mdata in player.mission.missions.values():
        count += mdata["star"]

    return count >= cfg["cond_a"]

# ====================================================================
def _check_act_type(cfg, types, data):
    """
    """
    return (cfg["type"] not in SPECIAL_ACTS1) and (cfg["type"] in types)

def _check_need_update(sid, act_id, act_data):
    """检查是否更新活动数据

    更新活动数据的条件有四个
        1.活动存在
        2.操作在有效时间范围内
        3.任务没有全部完成
    """
    now = int(time.time())
    act_info = act_service.get_act_info(sid, act_id)
    if (not act_info) or (act_info["start"] > now) or (now >= act_info["end"]):
        return False

    # 更新钻石赌博这类的活动 在ActDetailConfig中 没有配置 但需要更新数据
    index_list = game_config.act_sample_detail_cfg.get(act_id, [])
    if not index_list:
        return True

    if pow(2, len(index_list)) - 1 > act_data["canget"] + act_data["awarded"]:
        return True
    else:
        return False
