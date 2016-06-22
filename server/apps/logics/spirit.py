#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-24 11:20:09
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   战魂业务接口
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

SPIRIT_EXP_PRICE = 250

# ========================= GAME API ==============================
def intensify(context):
    """强化升级战魂

    Args:
        hero_id 姬甲ID
        spirit_id 战魂ID
        items 物品列表 {item_id: item_num, }
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    spirit_id = context.get_parameter("spirit_id")
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

    spirit = ki_user.spirit.get_spirit(hero_id, spirit_id)
    if not spirit:
        context.result['mc'] = MsgCode['SpiritNotWeaken']
        return

    if spirit["level"] >= max(game_config.spirit_exp_level_cfg.values()):
        context.result['mc'] = MsgCode['SpiritLevelMax']
        return

    total_exp = 0
    for item_id, num in items.items():
        item_cfg = game_config.item_cfg.get(item_id)
        if not item_cfg["spirit_exp"]:
            context.result['mc'] = MsgCode['ParamIllegal']
            return
        else:
            total_exp += item_cfg["spirit_exp"] * num

    need_gold = total_exp * SPIRIT_EXP_PRICE
    # 检查金币是否足够
    if not user_logic.check_game_values1(ki_user, gold=need_gold):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return

    if not total_exp:
        context.result['mc'] = MsgCode['InvalidOperation']
        return

    pack_logic.remove_items(ki_user, items) # 扣除物品
    user_logic.consume_game_values1(ki_user, gold=need_gold)  # 扣除金币
    ki_user.spirit.add_exp(hero_id, spirit_id, total_exp) # 添加经验

    context.result['mc'] = MsgCode['SpiritLevelUpSucc']

def intensify2(context):
    """钻石强化升级战魂

    Args:
        hero_id 姬甲ID
        spirit_id 战魂ID
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    spirit_id = context.get_parameter("spirit_id")

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    spirit = ki_user.spirit.get_spirit(hero_id, spirit_id)
    if not spirit:
        context.result['mc'] = MsgCode['SpiritNotWeaken']
        return

    lack_exp = 0
    for exp, level in game_config.spirit_exp_level_cfg.items():
        if level == spirit["level"]+1:
            lack_exp = exp - spirit["exp"]

    need_diamond = lack_exp * 5
    # 检查材料是否足够
    if not user_logic.check_game_values1(ki_user, diamond=need_diamond):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    ki_user.spirit.add_exp(hero_id, spirit_id, lack_exp)
    user_logic.consume_game_values1(ki_user, diamond=need_diamond)

    context.result['mc'] = MsgCode['SpiritLevelUpSucc']

# ========================= MODULE API =============================
def append_hero_spirit(user, hero_id, hero_quality):
    """更新机甲的战魂

    机甲提升品质的时候调用此接口

    """
    cfg = game_config.hero_base_cfg.get(hero_id)
    for spirit_id in cfg["spirits"]:
        spirit_cfg = game_config.spirit_cfg.get(spirit_id)
        spirit = user.spirit.get_spirit(hero_id, spirit_id)
        if (hero_quality >= spirit_cfg["weak_quality"]) and (not spirit):
            user.spirit.append_spirit(hero_id, spirit_id)

    user.spirit.put()
