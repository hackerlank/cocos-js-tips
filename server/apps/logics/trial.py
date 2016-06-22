#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-20 10:20:19
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      试炼业务逻辑
# @end
# @copyright (C) 2015, kimech

import time
import random
import logging

from apps.misc import utils
from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.services.arena import ArenaService
from apps.services import rank as rank_service
from apps.services.notice import NoticeService

from apps.logics import user as user_logic
from apps.logics import package as pack_logic
from apps.logics.helpers import common_helper

from helpers import user_helper
from helpers import act_helper
from helpers import hero_helper
from helpers import trial_helper

PROCESS_FIGHT = 1
PROCESS_BUFF = 2
PROCESS_BOX = 3

BUFF_COND_LOSE_HP = 1
BUFF_COND_LOSE_HERO = 2

# 星级和积分加成对照表
STAR_SCORE_MAP = {1: 1, 2: 1.5, 3: 2.5}

# ========================= GAME API ==============================
def info(context):
    """请求试炼数据

    Args:

    Returns:
        stars                   # 积累的总星星数量
        array                   # 试炼阵容
        daily_yesterday_max     # 昨日爬到的最高层数，用来计算哪些战斗层数可以跳过
        history_scores          # 历史积分
        awarded_index           # 领取奖励列表
        daily_scores            # 累计获得积分
        daily_buffs             # 今日购买的buff. {1: [12001,12003], 2: [13001]}
        daily_fighters          # 今日匹配到的对手目标
        daily_current_process   # 今日当前爬到的层数
    """
    ki_user = context.user

    # if not ki_user.trial.daily_fighters:
    #     ki_user.trial.initial_daily_fighters(ki_user.sid, ki_user.uid, ki_user.hero.heros)

    datas = {}
    datas["stars"] = ki_user.trial.stars
    datas["array"] = ki_user.array.get_trial_array()
    datas["awarded_index"] = ki_user.trial.awarded_index
    datas["history_scores"] = ki_user.trial.history_scores
    datas["daily_scores"] = ki_user.trial.daily_scores
    datas["bought_buffs"] = ki_user.trial.daily_bought_buffs
    datas["current_process"] = ki_user.trial.daily_current_process
    datas["hero_states"] = ki_user.trial.daily_hero_states
    datas["daily_yesterday_max"] = ki_user.trial.daily_yesterday_max
    datas["current_rank"] = rank_service.trial_rank(ki_user.sid, ki_user.uid)

    # 根据当前层的类型来定制当前层的内容
    cur_process = ki_user.trial.daily_current_process
    cfg = game_config.trial_cfg.get(cur_process)
    if cfg["type"] == PROCESS_FIGHT:
        content = {}
        fighters = ki_user.trial.match_fighters(cur_process, ki_user.sid, ki_user.uid, ki_user.hero.heros)
        content["fighters"] = fighters
        content["chosed_fighter"] = ki_user.trial.tmp_current_fighter
        fighter_states = ki_user.trial.tmp_fighter_states
        # 传递对手当前的状态，可能会是残血状态
        if fighter_states:
            content["fighter_states"] = fighter_states
        else:
            # content["fighter_states"] = build_fighter_states(content["chosed_fighter"], fighters)
            # 默认传空 前端做满血处理
            content["fighter_states"] = {}

    elif cfg["type"] == PROCESS_BUFF:
        content = ki_user.trial.daily_buffs.get(cur_process, {})
    else:
        content = {}
        content["awards"] = ki_user.trial.daily_awards.get(cur_process, {})
        content["count"] = ki_user.trial.tmp_box_counter

    datas["content"] = content

    context.result["data"] = datas

def choose_fighter(context):
    """战斗层，挑选对手

    Args:
        fighter_id 选择的对手

    Returns:

    """
    ki_user = context.user

    fighter_id = context.get_parameter("fighter_id")

    cur_process = ki_user.trial.daily_current_process
    cfg = game_config.trial_cfg.get(cur_process)
    if cfg["type"] != PROCESS_FIGHT:
        context.result['mc'] = MsgCode['TrialWrongType']
        return

    cur_fighters = ki_user.trial.daily_fighters.get(cur_process, {})
    fighter_ids = [f["uid"] for f in cur_fighters.itervalues()]

    if fighter_id not in fighter_ids:
        context.result['mc'] = MsgCode['TrialFighterNotExist']
        return

    trial_array = ki_user.array.trial
    if trial_array.count(0) == 6:
        context.result['mc'] = MsgCode['ArrayCantEmpty']
        return

    if ki_user.trial.tmp_current_fighter:
        context.result['mc'] = MsgCode['TrialFighterChosen']
        return

    ki_user.trial.chose_fighter(fighter_id)

    context.result["mc"] = MsgCode['TrialChoseFighterSucc']

def fight(context):
    """战斗层，玩家发起挑战

    Args:
        process 发起挑战的当前进度
        fighter_id 挑战对手
        star 获得星星数量
        states 角色当前状态

    Returns:

    """
    ki_user = context.user

    fighter_id = context.get_parameter("fighter_id")
    star = context.get_parameter("star")
    my_states = context.get_parameter("my_states", "{}")  # 我方状态
    fighter_states = context.get_parameter("fighter_states", "{}")  # 敌方状态
    fight = context.get_parameter("fight")

    try:
        if fighter_id.strip() == "":
            raise

        my_states = eval(my_states)
        if star not in range(0,4):
            raise

        if star == 0:
            fighter_states = eval(fighter_states)
            states = [my_states, fighter_states]
        else:
            states = [my_states]

        for i in states:
            if (not isinstance(i, dict)):
                raise
            else:
                for state in i.itervalues():
                    if state < 0 or state > 1:
                        raise
        # 战队当前状态机甲必须是阵容的子集
        trial_array = ki_user.array.trial
        for hid in trial_array:
            if hid and str(hid) not in my_states:
                raise
    except Exception, e:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cur_process = ki_user.trial.daily_current_process
    cfg = game_config.trial_cfg.get(cur_process)
    if cfg["type"] != PROCESS_FIGHT:
        context.result['mc'] = MsgCode['TrialWrongType']
        return

    if fighter_id != ki_user.trial.tmp_current_fighter:
        context.result['mc'] = MsgCode['TrialFighterWrong']
        return

    # 战力校验
    if not user_helper.check_user_fight(ki_user, fight, 3):
        context.result['mc'] = MsgCode['UserFightCheckFailed']
        return

    # 保存当前我的阵容血量状态
    for hero_id, hp in my_states.items():
        ki_user.trial.daily_hero_states[int(hero_id)] = hp

    # 胜利之后，计算积分和星星数量
    if star:
        # 积分计算公式 基础分 * (1 + vip加成) * 星级加成
        try:
            cur_fighters = ki_user.trial.daily_fighters.get(cur_process)
            fighter_difficulty = count_fighter_difficulty(cur_fighters, fighter_id)
            rule = cfg["items"][fighter_difficulty][0]
        except:
            logging.error("trial keyerror, reason: process:%s fighter_difficulty:%s fighter_id:%s cur_fighters:%s" % (cur_process, fighter_difficulty, fighter_id, cur_fighters))
            context.result['mc'] = MsgCode['TrialFighterWrong']
            return

        fight_cfg = game_config.trial_fighter_rule_cfg.get(rule)
        vipcfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
        final_scores = int(fight_cfg["base_score"] * (1 + vipcfg["trial_score_percent"]) * STAR_SCORE_MAP[star])
        final_stars = fight_cfg["star_times"] * star

        next_process = ki_user.trial.daily_current_process + 1
        next_cfg = game_config.trial_cfg.get(next_process, {})
        if next_cfg:
            content = build_next_content(ki_user, next_process)
            ki_user.trial.update_next_content(next_process, next_cfg["type"], content)

            context.result["data"] = {}
            context.result["data"]["content"] = content

        ki_user.trial.add_scores_and_stars(final_scores, final_stars)
        # 更新排行榜数据
        rank_service.update_trial_rank(ki_user.sid, ki_user.uid, ki_user.trial.daily_current_process)
        # 更新活动【通关试炼指定层数&累计获得试炼积分达到指定数量】
        act_helper.update_after_trial_process(ki_user, cur_process, final_scores)

        try:
            if cur_process >= 40 and cur_process % 10 == 0:
                trigger = {'uid': ki_user.uid, 'name': ki_user.name}
                NoticeService.broadcast(ki_user.sid, 13, trigger, cur_process)
        except:
            logging.error("【试炼过关】炫耀广播发生错误。")
    else:
        # 失败了，保存对手的残血状态，保存当前对手ID
        ki_user.trial.tmp_current_fighter = fighter_id
        ki_user.trial.tmp_fighter_states = fighter_states

    ki_user.trial.put()

    context.result["mc"] = MsgCode["TrialFightSucc"]

def buy_buff(context):
    """购买Buff

    Args:
        index 索引位置
        buff_id

    Returns:

    """
    ki_user = context.user

    index = context.get_parameter("index")
    buff_id = context.get_parameter("buff_id")
    hero_id = context.get_parameter("hero_id")

    process = ki_user.trial.daily_current_process
    cfg = game_config.trial_cfg.get(process)
    if cfg["type"] != PROCESS_BUFF:
        context.result['mc'] = MsgCode['TrialWrongType']
        return

    buffs = ki_user.trial.daily_buffs.get(process)
    if buffs[int(index)] != buff_id or buff_id not in buffs.values():
        context.result['mc'] = MsgCode['TrialBuffNotInList']
        return

    key = "%s#%s" % (buff_id, index)
    bought_buffs = ki_user.trial.daily_bought_buffs.get(process, {})
    if key in bought_buffs:
        context.result['mc'] = MsgCode['TrialBuffAlreadyBuy']
        return

    buff_cfg = game_config.trial_buff_cfg.get(buff_id)
    my_stars = ki_user.trial.stars
    if my_stars < buff_cfg["consume"]:
        context.result['mc'] = MsgCode['TrialStarsNotEnough']
        return

    if buff_cfg["conds"] == BUFF_COND_LOSE_HP:
        # 给机甲回血
        hp = ki_user.trial.daily_hero_states.get(hero_id, None)
        # 机甲不存在或者没有上过阵，再或者已经死亡，没掉血
        if (not hp) or (hp == 1):
            context.result['mc'] = MsgCode['TrialHeroCantUseBuff']
            return
        else:
            hp_add = buff_cfg["effective"][buff_cfg["conds"]]
            ki_user.trial.daily_hero_states[hero_id] = hp + hp_add
    elif buff_cfg["conds"] == BUFF_COND_LOSE_HERO:
        # 复活机甲
        hp = ki_user.trial.daily_hero_states.get(hero_id, None)
        # 机甲不存在或者没有上过阵，再或者没死
        if hp != 0:
            context.result['mc'] = MsgCode['TrialHeroCantUseBuff']
            return
        else:
            hp_add = buff_cfg["effective"][buff_cfg["conds"]]
            ki_user.trial.daily_hero_states[hero_id] = hp + hp_add
    else:
        pass # 普通buff  直接放入已购买的buff列表

    if not bought_buffs:
        ki_user.trial.daily_bought_buffs[process] = [key]
    else:
        bought_buffs.append(key)

    ki_user.trial.stars -= buff_cfg["consume"]
    ki_user.trial.put()

    # 更新活动【通关试炼指定层数】
    act_helper.update_after_trial_process(ki_user, process)

    context.result["mc"] = MsgCode["TrialBuyBuffSucc"]

def open_box(context):
    """宝箱层，免费领取箱子里的道具

    Args:

    Returns:

    """
    ki_user = context.user

    process = ki_user.trial.daily_current_process
    _cfg = game_config.trial_cfg.get(process)
    if _cfg["type"] != PROCESS_BOX:
        context.result['mc'] = MsgCode['TrialWrongType']
        return

    # 首次开箱子免费，奖品取现成的
    loop_index = ki_user.trial.tmp_box_counter + 1

    cfg = game_config.user_buy_refresh_cfg.get(loop_index)
    if not cfg:
        last = max(game_config.user_buy_refresh_cfg.keys())
        cfg = game_config.user_buy_refresh_cfg.get(last)

    if not user_logic.check_game_values1(ki_user, diamond=cfg["trial_openbox_diamond"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    if loop_index == 1:
        awards = ki_user.trial.daily_awards.get(process)
        act_helper.update_after_trial_process(ki_user, process) # 更新活动【通关试炼指定层数】
    else:
        awards = random_awards(process, loop_index, ki_user.game_info.role_level)

    user_logic.consume_game_values1(ki_user, diamond=cfg["trial_openbox_diamond"])
    pack_logic.add_items(ki_user, awards) # 加物品

    # 更新这一层领取物品计数器
    ki_user.trial.incr_award_counter()

    context.result["data"] = {}
    context.result["data"]["awards"] = awards

def skip(context):
    """buff和宝箱层可调用此接口进入下一层

    Args:

    Returns:
        content 下一层内容
    """
    ki_user = context.user

    current_process = ki_user.trial.daily_current_process

    next_process = current_process + 1
    next_cfg = game_config.trial_cfg.get(next_process, {})
    if not next_cfg:
        context.result['mc'] = MsgCode['TrialProcessMax']
        return

    this_cfg = game_config.trial_cfg.get(current_process)
    # 战斗层跳过战斗过程限制规则：若玩家昨日通关层数为N，且该层数≤2n/3的整数倍
    if this_cfg["type"] == PROCESS_FIGHT:
        if current_process > int(ki_user.trial.daily_yesterday_max * 2 / 3):
            context.result['mc'] = MsgCode['TrialCantSkip']
            return
        else:
            # 可跳过战斗过程，直接给最高积分和星星数量
            # 积分计算公式 基础分 * (1 + vip加成) * 星级加成
            fight_rule_ids = this_cfg["items"].get(3)
            fight_cfg = game_config.trial_fighter_rule_cfg.get(fight_rule_ids[0])

            vipcfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
            final_scores = int(fight_cfg["base_score"] * (1 + vipcfg["trial_score_percent"]) * STAR_SCORE_MAP[3])
            final_stars = fight_cfg["star_times"] * 3

            ki_user.trial.add_scores_and_stars(final_scores, final_stars)

            # 更新活动【通关试炼指定层数】
            act_helper.update_after_trial_process(ki_user, current_process, final_scores)

    rank_service.update_trial_rank(ki_user.sid, ki_user.uid, current_process)
    content = build_next_content(ki_user, next_process)
    ki_user.trial.update_next_content(next_process, next_cfg["type"], content)

    if current_process >= 40 and current_process % 10 == 0:
        try:
            trigger = {'uid': ki_user.uid, 'name': ki_user.name}
            NoticeService.broadcast(ki_user.sid, 13, trigger, current_process)
        except:
            logging.error("【试炼过关】炫耀广播发生错误。")

    context.result["data"] = {}
    context.result["data"]["type"] = next_cfg["type"]
    context.result["data"]["content"] = content

def award(context):
    """领取积分奖励

    Args:
        index 奖励编号

    Returns:

    """
    ki_user = context.user

    index = context.get_parameter("index")

    award_cfg = game_config.trial_awards_cfg.get(index, {})
    if not award_cfg:
        context.result['mc'] = MsgCode['TrialGetAwardWrong']
        return

    scores = ki_user.trial.history_scores * 0.08 + ki_user.trial.daily_scores
    if scores < award_cfg["scores"]:
        context.result['mc'] = MsgCode['TrialScoresTooLow']
        return

    if index in ki_user.trial.awarded_index:
        context.result['mc'] = MsgCode['TrialAwarded']
        return

    pack_logic.add_items(ki_user, award_cfg["awards"])
    ki_user.trial.award(index)

    context.result["mc"] = MsgCode['TrialGetAwardSucc']

# ==============================================================================
def random_hero(had_hero_ids):
    """
        随机一层给一个稍微牛逼点的机甲
    """
    rand_lib = hero_helper.get_pick_rand_lib(14)  # 14固定

    choices = filter(lambda x: x.keys() and x.keys()[0] not in had_hero_ids, rand_lib["lib"])
    if choices:
        target = random.choice(choices)
    else:
        target = random.choice(rand_lib["lib"])

    return target

def random_buffs(hero_states, process):
    """
    """
    # TODO 判断当前试炼阵容是否有机甲生命值不满
    lose_hp = False
    for hero, hp in hero_states.items():
        if 0 < hp < 1:
            lose_hp = True

    # TODO 判断当前试炼阵容是否有机甲死亡
    lose_hero = False
    for hero, hp in hero_states.items():
        if hp == 0:
            lose_hero = True

    buffs = {}
    cfg = game_config.trial_cfg.get(process)
    for index, items in cfg["items"].items():
        rand_list = {}
        for item in items:
            buff_cfg = game_config.trial_buff_cfg.get(item)
            if not buff_cfg["conds"]:
                rand_list[item] = buff_cfg["weight"]
            else:
                if buff_cfg["conds"] == BUFF_COND_LOSE_HP and lose_hp:
                    rand_list[item] = buff_cfg["weight"]

                if buff_cfg["conds"] == BUFF_COND_LOSE_HERO and lose_hero:
                    rand_list[item] = buff_cfg["weight"]

        buff = common_helper.weight_random(rand_list)
        buffs[index] = buff

    return buffs

def random_awards(process, loop_index, role_level):
    """
    """
    cfg = game_config.trial_cfg.get(process)
    awards = []
    level_area = max([i for i in range(0,100,10) if role_level >= i])
    for index, items in cfg["items"].items():
        if items:
            ex_cfg = game_config.item_exchange_cfg.get(items[0])
            target = common_helper.weight_random(ex_cfg["lib_%s" % level_area])

            awards.append(game_config.item_pack_cfg.get(target))

    # 如果是第一次随机物品，则附赠额外的试炼点
    if loop_index == 1:
        awards.append(cfg["extra_award"])

    awards = common_helper.handle_pack_items(awards)

    return awards

def build_next_content(ki_user, process):
    """制定关卡的内容
    """
    daily_hero_states = ki_user.trial.daily_hero_states

    cfg = game_config.trial_cfg.get(process)
    if cfg["type"] == PROCESS_FIGHT:
        content = {}
        fighters = ki_user.trial.match_fighters(process, ki_user.sid, ki_user.uid, ki_user.hero.heros)
        content["fighters"] = fighters
        content["chosed_fighter"] = 0
        content["fighter_states"] = {}
    elif cfg["type"] == PROCESS_BUFF:
        content = random_buffs(daily_hero_states, process)   # 随机出三个buff
    else:
        role_level = ki_user.game_info.role_level
        content = random_awards(process, 1, role_level) # 给玩家送随机出来的物, ki_user.game_info.role_level品

    return content

def build_fighter_states(fighter_id, fighters):
    """构造对手的百分比血量
    """
    if not fighter_id:
        return {}

    # 如果当前对手是机器人
    if fighter_id.startswith("robot_"):
        robot_index = int(fighter_id[6:])
        cfg_key = min([index for index in game_config.arena_formation_index_cfg if index >= robot_index])
        cfg = game_config.arena_formation_cfg.get(cfg_key)

        return dict.fromkeys(cfg["robot_heros"], 1)
    else:
        # 真实玩家
        for index,fighter in fighters.items():
            if fighter["uid"] == fighter_id:
                hero_ids = [hero for hero in fighter["array"] if hero != 0]

        if isinstance(hero_ids, None):
            hero_ids = []

        return dict.fromkeys(hero_ids, 1)

def update_hero_states_after_array(user, array):
    """布阵后，更新今日上过阵的机甲状态
    """
    for hero in array:
        if hero not in user.trial.daily_hero_states and hero != 0:
            user.trial.daily_hero_states[hero] = 1

    user.trial.put()

def count_fighter_difficulty(fighters, fighter_id):
    """
    """
    final_difficulty = None
    for difficulty, fighter in fighters.items():
        if str(fighter["uid"]) == str(fighter_id):
            final_difficulty = difficulty

    return final_difficulty
