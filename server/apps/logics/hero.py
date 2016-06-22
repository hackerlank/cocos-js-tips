#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      机甲(卡牌)业务逻辑:
#       1.抽卡
#       2.升品
#       3.升级
#       4.升星
#       5.合成
#       6.万能碎片兑换
#       7.讨好喂食
#       8.许誓
#       9.分手
#
#       每个玩家只能最多只能拥有一个同名的卡牌
#       如果玩家抽到已拥有的卡牌，则自动转换为卡牌碎片放入玩家的背包
#       升级卡牌星级需要同名的卡牌碎片
# @end
# @copyright (C) 2015, kimech

import copy
import time
import random
import logging

from .helpers import act_helper
from .helpers import hero_helper
from .helpers import common_helper

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import package as pack_logic
from apps.logics import user as user_logic
from apps.logics import skill as skill_logic
from apps.logics import spirit as spirit_logic

from apps.services.notice import NoticeService
from apps.services import rank as rank_service

from apps.misc import utils

# 抽卡类型
GOLD_ONE = 1
GOLD_TEN = 2
DIAMOND_ONE = 3
DIAMOND_TEN = 4

# 转换万能碎片的类型
CHIP_EXCHANGE_ONE = 1
CHIP_EXCHANGE_TEN = 2

# 万能碎片ID
SPECIAL_CHIP_ID = 120602

# 抽奖获得物品类型
PICK_ITEM_HERO = 1
PICK_ITEM_ITEM = 2

# 机甲经验物品类型
SPECIAL_HERO_EXP_ITEM_TYPE = 1

# 机甲许誓需求好感度称号ID
HERO_MARRY_TITLE_ID = 3
# ========================= GAME API ==============================
def pick(context):
    """玩家抽卡

    背包是否已满 -》今日免费抽取次数是否用完 -》cd是否冷却 -》
    钱够不够 -》 抽卡 -》 抽到的卡片是否已拥有 -》加物品 -》 扣除消耗 -》 更新数据
    -》 返回抽到的物品

    Args:
        ptype 抽奖类型  1-金币单次 2-金币连抽 3-钻石单次 4-钻石连抽

    Returns:
        {"heros":[hero_id, ], "items": {item_id: item_num, }}  获得物品

    Raises:
        MsgCode['ParamIllegal']
        MsgCode['PackageIsFull']
        MsgCode['GoldNotEnough']
        MsgCode['DiamondNotEnough']
    """
    ki_user = context.user

    ptype = context.get_parameter("ptype")
    if ptype not in [1,2,3,4]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cur_package_len = len(ki_user.package.items)
    if cur_package_len >= pack_logic.PACKAGE_MAX_SLOTS:
        context.result['mc'] = MsgCode['PackageIsFull']
        return

    hero_daily_info = ki_user.daily_info.hero_pick_info
    pick_info = ki_user.hero.pick_info

    cfg = game_config.hero_pick_cfg[ptype]

    now = int(time.time())
    is_free = False

    if ptype == GOLD_ONE and \
       hero_daily_info["gold"] < cfg["limit_times"] and \
       now > pick_info["gold_cd"] + cfg["cd"]:
       is_free = True

    # if ptype == DIAMOND_ONE and \
    #    hero_daily_info["diamond"] < cfg["limit_times"] and \
    #    now > pick_info["diamond_cd"] + cfg["cd"]:
    if ptype == DIAMOND_ONE and hero_daily_info["diamond"]:
       is_free = True

    if not is_free and not pack_logic.check_items_enough(ki_user, cfg["consume"]):
        context.result['mc'] = MsgCode['GoldNotEnough'] if ptype in [GOLD_ONE, GOLD_TEN] else MsgCode['DiamondNotEnough']
        return

    # 十连抽 or 单次
    loop_index = 0 if ptype in [GOLD_ONE, DIAMOND_ONE] else 9

    picked_items = {}
    picked_items["heros"] = []
    picked_items["items"] = []

    while loop_index >= 0:
        rand_type = hero_helper.get_rand_type(is_free, ptype, pick_info, loop_index)
        rand_lib = hero_helper.get_pick_rand_lib(rand_type)

        # 随机出获得的物品
        target = random.choice(rand_lib["lib"])
        target_type = rand_lib["lib_type"]

        if target_type == PICK_ITEM_HERO:
            picked_items["heros"].append(target)
        else:
            picked_items["items"].append(target)

        loop_index -= 1

    # 加物品&扣除消耗品
    if not is_free:
        pack_logic.remove_items(ki_user, cfg["consume"])

    add_heros(ki_user, picked_items["heros"])  # 加抽到的机甲卡牌

    srv_add_items = copy.copy(picked_items["items"])
    srv_add_items.append(cfg["goods"])
    pack_logic.add_items(ki_user, common_helper.handle_pack_items(srv_add_items))   # 加抽到的物品

    # 更新数据
    if is_free and ptype == GOLD_ONE:
        ki_user.daily_info.hero_pick_info["gold"] += 1
        ki_user.daily_info.put()

        ki_user.hero.pick_info["gold_cd"] = now
        ki_user.hero.put()

    elif is_free and ptype == DIAMOND_ONE:
        ki_user.daily_info.hero_pick_info["diamond"] = 0
        ki_user.daily_info.put()

        ki_user.hero.pick_info["diamond_pick_times"] += 1
        ki_user.hero.put()

    elif not is_free and ptype == DIAMOND_ONE:
        ki_user.hero.pick_info["diamond_pick_times"] += 1
        ki_user.hero.put()

    elif ptype == DIAMOND_TEN:
        ki_user.hero.pick_info["diamond_ten_times"] += 1
        ki_user.hero.put()

    else:
        pass

    # 整理抽奖所得物品
    # picked_items["items"] = common_helper.handle_pack_items(picked_items["items"])

    # 更新运维活动数据
    try:
        if ptype == DIAMOND_ONE:
            act_helper.update_after_diamond_pick_hero(ki_user, 1)
        elif ptype == DIAMOND_TEN:
            act_helper.update_after_diamond_pick_hero(ki_user, 10)
        else:
            pass
    except:
        logging.error("【钻石抽取姬甲达到指定数量】活动更新失败")

    context.result["data"] = picked_items

def intensify(context):
    """卡牌升级

    升级操作为玩家吞食经验道具，道具类型分为几等
    卡牌等级受主角总等级限制

    Args:
        卡牌ID hero_id int
        经验道具ID item_id int
        经验道具数量 item_num int

    Returns:
        bool 成功 or 失败

    Raises:
        MsgCode['PackageItemNotEnough']
        MsgCode['HeroNotExist']
        MsgCode['HeroUpLevelFail']

    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    items = context.get_parameter("items", "{}")

    try:
        items = eval(items)
        if not isinstance(items, dict):
            raise 1

        for v in items.values():
            if v <= 0:
                raise e
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    if hero["level"] >= ki_user.game_info.role_level:
        context.result['mc'] = MsgCode['HeroUserLevelLimit']
        return

    if not pack_logic.check_items_enough(ki_user, items):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    total_add_exp = 0
    for item_id, item_num in items.iteritems():
        item_cfg = game_config.item_cfg.get(item_id)
        if not item_cfg:
            context.result['mc'] = MsgCode['GameConfigNotExist']
            return

        if item_cfg["type"] != SPECIAL_HERO_EXP_ITEM_TYPE:
            context.result['mc'] = MsgCode['ParamIllegal']
            return
        else:
            total_add_exp = item_cfg["effect_value"] * item_num

    after_exp = hero["exp"] + total_add_exp
    after_level = common_helper.get_level_by_exp(game_config.hero_exp_level_cfg, after_exp)

    ki_user.hero.update_exp_level(hero_id, after_exp, min(ki_user.game_info.role_level, after_level))
    pack_logic.remove_items(ki_user, items)

    context.result['mc'] = MsgCode['HeroIntensifySucc']

def upgrade(context):
    """卡牌升级品质

    卡牌初始等级为0，凑齐四样材料并且达到对应等级之后可以升级卡牌的品质

    Args:
        卡牌ID hero_id int

    Returns:
        bool 成功 or 失败

    Raises:
        MsgCode['HeroNotExist']
        MsgCode['HeroMaxQuality']
        MsgCode['HeroQualityLvLimit']
        MsgCode['PackageItemNotEnough']

    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    hero_cfg = game_config.hero_base_cfg.get(hero_id)

    quality_key = "%s-%s" % (hero_cfg["type"], hero["quality"] + 1)
    quality_cfg = game_config.hero_upgrade_cfg.get(quality_key, {})
    if not quality_cfg:
        context.result['mc'] = MsgCode['HeroMaxQuality']
        return

    if hero["level"] < quality_cfg["need_level"]:
        context.result['mc'] = MsgCode['HeroQualityLvLimit']
        return

    if not pack_logic.check_items_enough(ki_user, quality_cfg["material"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    ki_user.hero.update_quality(hero_id)
    pack_logic.remove_items(ki_user, quality_cfg["material"])
    # 更新战魂信息
    spirit_logic.append_hero_spirit(ki_user, hero_id, hero["quality"])

    context.result['mc'] = MsgCode['HeroUpgradeSucc']

def weak(context):
    """卡牌升级星等

    卡牌升级星星，需要对应的碎片升级
    升级星星成功后，更换hero_base_cfg中对应的hero_id，卡牌属性等级保留
    消耗碎片数量走配置表

    Args:
        hero_id  当前星级卡牌对应的hero_id

    Returns:
        bool 成功 or 失败

    Raises:
        MsgCode['HeroNotExist']
        MsgCode['HeroMaxStar']
        MsgCode['PackageItemNotEnough']

    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    next_star_cfg = game_config.hero_weak_cfg.get("%s-%s" % (hero_id, hero["star"]+1), {})
    if not next_star_cfg:
        context.result['mc'] = MsgCode['HeroMaxStar']
        return

    need_chip_id = next_star_cfg["chip"]["id"]
    need_chip_num = next_star_cfg["chip"]["up_star_num"]

    if not pack_logic.check_items_enough(ki_user, {need_chip_id: need_chip_num, 1: next_star_cfg["consume_gold"]}):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    pack_logic.remove_items(ki_user, {need_chip_id: need_chip_num, 1: next_star_cfg["consume_gold"]})
    ki_user.hero.update_hero_star(hero_id)

    # 更新技能信息
    skill_logic.append_hero_skill(ki_user, hero_id, hero["star"])

    if hero["star"] >= 5:
        try:
            trigger = {'uid': ki_user.uid, 'name': ki_user.name}
            data = {'hero_id': hero_id, 'star': hero["star"], 'quality': hero["quality"]}
            NoticeService.broadcast(ki_user.sid, 12, trigger, data)
        except:
            logging.error("升星炫耀时发生错误。")

    context.result['mc'] = MsgCode['HeroWeakSucc']

def synthesis(context):
    """碎片合成机甲

    Args:
        合成目标机甲ID int

    Returns:
        bool 成功 or 失败
    Raises:
        MsgCode['HeroAlreadyExist']
        MsgCode['PackageItemNotEnough']

    """
    ki_user = context.user

    index = context.get_parameter("index")
    synt_cfg = game_config.hero_synt_cfg.get(index)
    if not synt_cfg:
        context.result['mc'] = MsgCode['GameConfigNotExist']
        return

    if synt_cfg["hero_id"] in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroAlreadyExist']
        return

    if not pack_logic.check_items_enough(ki_user, {synt_cfg["chip_id"]: synt_cfg["num"]}):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    add_heros(ki_user, [{synt_cfg["hero_id"]: synt_cfg["star"]}])
    pack_logic.remove_items(ki_user, {synt_cfg["chip_id"]: synt_cfg["num"]})

    context.result['mc'] = MsgCode['HeroSynthesisSucc']

def exchange_chip(context):
    """转换万能碎片，万能碎片 -》 机甲碎片

    规则：
        将万能碎片转换成普通碎片，只能用于升级星等
        转换类型分为转换1个和10个
        如果选择转换10个，若当前数量小于等于10个，则全部转换

    Args:
        target_chip_id 目标碎片道具ID int
        exchange_type 转换类型 （转换一个或者转换十个）

    Raises:
        MsgCode['ParamIllegal']
        MsgCode['HeroNotExist']
        MsgCode['PackageItemNotExist']

    """
    ki_user = context.user

    target_chip_id = context.get_parameter("target_chip_id")
    exchange_type = context.get_parameter("exchange_type")

    if exchange_type not in [CHIP_EXCHANGE_ONE, CHIP_EXCHANGE_TEN]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    chip_cfg = game_config.item_cfg.get(target_chip_id, {})
    if not chip_cfg:
        context.result['mc'] = MsgCode['GameConfigNotExist']
        return

    # 判断是否有这个碎片对应的机甲
    if chip_cfg["chip_hero_id"] not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    if not pack_logic.check_items_enough(ki_user, {SPECIAL_CHIP_ID: 1}):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    num = 1
    if exchange_type == CHIP_EXCHANGE_TEN:
        had_num = ki_user.package.get_item_num_by_id(SPECIAL_CHIP_ID)
        num = 10 if had_num >= 10 else had_num

    pack_logic.add_items(ki_user, {target_chip_id: num})
    pack_logic.remove_items(ki_user, {SPECIAL_CHIP_ID: num})

    context.result['mc'] = MsgCode['HeroExchangeChipSucc']

def feed(context):
    """喂食增加好感度

    Args:
        hero_id 姬甲ID
        items 物品列表 {item_id: item_num, }
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    items = context.get_parameter("items", "{}")

    try:
        items = eval(items)
        if not isinstance(items, dict):
            raise 1

        for v in items.values():
            if v <= 0:
                raise e
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    hero_cfg = game_config.hero_base_cfg.get(hero_id)
    fav_cfg = game_config.favor_cfg.get(hero_cfg["favor_type"])

    for item_id in items:
        if item_id not in fav_cfg["items"]:
            context.result['mc'] = MsgCode['HeroFoodTypeError']
            return

    total_favor = 0
    for item_id, num in items.items():
        item_cfg = game_config.item_cfg.get(item_id)
        if not item_cfg["effect_value"]:
            context.result['mc'] = MsgCode['ParamIllegal']
            return
        else:
            total_favor += item_cfg["effect_value"] * num

    after_favor = hero["favor"] + total_favor
    if after_favor > max(game_config.favor_level_cfg.iterkeys()):
        context.result['mc'] = MsgCode['HeroFavorAlreadyMax']
        return

    if not total_favor:
        context.result['mc'] = MsgCode['InvalidOperation']
        return

    cfg_key = max([exp for exp in game_config.favor_level_cfg if exp <= hero["favor"]])
    pre_favor_title = game_config.favor_level_cfg[cfg_key].get("title_id")

    cfg_key1 = max([exp for exp in game_config.favor_level_cfg if exp <= after_favor])
    post_favor_title = game_config.favor_level_cfg[cfg_key1].get("title_id")

    if post_favor_title > pre_favor_title:
        add_awards = game_config.favor_title_cfg[post_favor_title]["awards"]
        pack_logic.add_items(ki_user, add_awards)

    pack_logic.remove_items(ki_user, items) # 扣除物品
    ki_user.hero.add_favor(hero_id, total_favor) # 添加好感度

    context.result['mc'] = MsgCode['HeroFeedSucc']

def marry(context):
    """与机甲许下誓言

    Args:
        hero_id 姬甲ID
        marry_id 契约ID
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    marry_id = context.get_parameter("marry_id")

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    # 是否满足等级条件
    title_id = _get_title_by_favor(hero["favor"])
    if title_id < HERO_MARRY_TITLE_ID:
        context.result['mc'] = MsgCode['HeroMarryFavorNotEnough']
        return

    # 是否重复誓言
    if hero["marry_id"]:
        context.result['mc'] = MsgCode['HeroAlreadyMarried']
        return

    # 检测消耗
    marry_cfg = game_config.favor_marry_cfg.get(marry_id)
    if not pack_logic.check_items_enough(ki_user, marry_cfg["items"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    pack_logic.remove_items(ki_user, marry_cfg["items"]) # 扣除物品
    ki_user.hero.marry(hero_id, marry_id) # 许誓

    context.result['mc'] = MsgCode['HeroFavorMarrySucc']

def divorce(context):
    """与机甲解除誓言

    Args:
        hero_id 姬甲ID
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    # 是否已经许誓
    if not hero["marry_id"]:
        context.result['mc'] = MsgCode['HeroFavorNoMarried']
        return

    marry_cfg = game_config.favor_marry_cfg.get(hero["marry_id"])
    if not user_logic.check_game_values1(ki_user, diamond=marry_cfg["break_need_diamond"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=marry_cfg["break_need_diamond"])
    # 解除契约，戒指通过邮箱返还玩家
    from apps.services.mail import MailService
    marry_cfg = game_config.favor_marry_cfg.get(hero["marry_id"])
    MailService.send_game(ki_user.uid, 2000, [], marry_cfg["items"])

    ki_user.hero.divorce(hero_id) # 解除契约

    context.result['mc'] = MsgCode['HeroFavorDivorceSucc']

# ========================= MODULE API =============================
def add_heros(user, heros):
    """新增机甲

    如果存在相同序列号的机甲，则将机甲兑换成对应数量的机甲碎片

    Args:
        user 用户对象
        heros 机甲列表 [{机甲ID: 星级}, {机甲ID: 星级}]
    """
    own = user.hero.heros

    _add_heros = {}
    _add_chips = {}

    for item in heros:
        for hid, star in item.iteritems():
            if (hid not in own) and (hid not in _add_heros):
                _add_heros[hid] = star
            else:
                cfg = game_config.hero_weak_cfg.get("%s-%s" % (hid, star))
                chip_id = cfg["chip"]["id"]
                if chip_id not in _add_chips:
                    _add_chips[chip_id] = cfg["chip"]["destroy_star_num"]
                else:
                    _add_chips[chip_id] += cfg["chip"]["destroy_star_num"]

    if _add_heros:
        for hid, star in _add_heros.iteritems():
            cfg = game_config.hero_base_cfg.get(hid, {})
            if cfg:
                user.hero.add_hero(hid, star)
                user.equip.add_hero(hid, cfg["equips"])
                skill_logic.append_hero_skill(user, hid, star, False)

                try:
                    if len([h for h in user.array.mission if h]) == 1:
                        user.array.mission[2] = hid
                        user.array.put()
                except:
                    logging.error("引导抽取第一个机甲，放置时出现错误。")

                try:
                    trigger = {'uid': user.uid, 'name': user.name}
                    data = {'hero_id': hid, 'star': star, 'quality': 0}
                    NoticeService.broadcast(user.sid, 11, trigger, data)
                except Exception,e:
                    raise e
                    logging.error("获得炫耀时发生错误")

        user.hero.put()
        user.equip.put()
        user.skill.put()

        # 更新机甲拥有数量排行
        rank_service.update_rank(user.sid, rank_service.RANK_HERO_COUNT, user.uid, len(user.hero.heros))

    if _add_chips:
        pack_logic.add_items(user, _add_chips)

def hero_add_exp(user, heros, exp):
    """机甲通过副本获得经验调用方法

    Args:
        heros  机甲ID列表
        exp  获得经验值
    """
    for hero_id in heros:
        hero = user.hero.get_by_hero_id(hero_id)

        after_exp = hero["exp"] + exp
        after_level = common_helper.get_level_by_exp(game_config.hero_exp_level_cfg, after_exp)

        user.hero.update_exp_level(hero_id, after_exp, min(user.game_info.role_level, after_level), False)

    user.hero.put()

def _get_title_by_favor(favor):
    """根据姬甲好感度确定所达到的好感度称号等级
    """
    tmp = max([f for f in game_config.favor_level_cfg if f <= favor])
    cfg = game_config.favor_level_cfg.get(tmp)

    return cfg["title_id"]
