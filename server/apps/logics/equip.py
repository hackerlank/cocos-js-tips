#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-20 11:13:32
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     装备业务逻辑:
#        1.强化升级
#        2.升品
#        3.升星
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic
from apps.logics.helpers import common_helper

SPECIAL_EQUIP_EXP_ITEM_1 = 2
SPECIAL_EQUIP_EXP_ITEM_2 = 3

EQUIP_POSITION_WEAPON = 1

# ========================= GAME API ==============================
def intensify(context):
    """强化，升级

    升级强化分为一键升级和普通升级
    最后两个装备的强化的升级流程特殊

    Args:
        hero_id
        position  装备部位
        to_level  到达的等级

    Raises:
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    position = context.get_parameter("position")
    to_level = context.get_parameter("to_level")

    if hero_id not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    equip_data = ki_user.equip.get_by_hero_position(hero_id, position)
    if not equip_data:
        context.result['mc'] = MsgCode['EquipNotExist']
        return

    if position >= 5:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if equip_data["level"] >= to_level or to_level > game_config.equip_max_level:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    equip_quality_cfg_key = "%s-%s" % (position, equip_data["quality"])
    equip_quality_cfg = game_config.equip_upgrade_cfg.get(equip_quality_cfg_key)

    if to_level > equip_quality_cfg["equip_max_level"]:
        context.result['mc'] = MsgCode['EquipLvOverLimit']
        return

    # 检查材料是否足够
    gold = 0
    for level in range(equip_data["level"]+1, to_level + 1):
        cfg = game_config.equip_intensify_cfg["%s-%s" % (position, level)]
        gold += cfg["gold"]

    if not user_logic.check_game_values1(ki_user, gold=gold):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return

    ki_user.equip.intensify(hero_id, position, to_level)
    user_logic.consume_game_values1(ki_user, gold=gold)

    context.result['mc'] = MsgCode['EquipIntensifySucc']

def intensify2(context):
    """两特殊装备加经验

    Args:
        hero_id
        position  装备部位
        items 经验道具 []

    Raises:
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    position = context.get_parameter("position")
    items = context.get_parameter("items", [])

    try:
        items = eval(items)
        if not isinstance(items, list):
            raise 1

        if position < 5:
            context.result['mc'] = MsgCode['ParamIllegal']
            return
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if hero_id not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    equip_data = ki_user.equip.get_by_hero_position(hero_id, position)
    if not equip_data:
        context.result['mc'] = MsgCode['EquipNotExist']
        return

    equip_quality_cfg_key = "%s-%s" % (position, equip_data["quality"])
    equip_quality_cfg = game_config.equip_upgrade_cfg.get(equip_quality_cfg_key)
    if equip_data["level"] > equip_quality_cfg["equip_max_level"]:
        context.result['mc'] = MsgCode['EquipLvOverLimit']
        return

    add_exp = 0
    exp_item_type = SPECIAL_EQUIP_EXP_ITEM_1 if position == 5 else SPECIAL_EQUIP_EXP_ITEM_2

    # 检查材料是否足够
    items = pack_logic.amend_goods([{item_id: 1} for item_id in items if item_id])

    if not pack_logic.check_items_enough(ki_user, items):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    for item_id,num in items.items():
        item_cfg = game_config.item_cfg.get(item_id)
        if not item_cfg:
            context.result['mc'] = MsgCode['GameConfigNotExist']
            return

        if item_cfg["type"] != exp_item_type:
            context.result['mc'] = MsgCode['ParamIllegal']
            return

        add_exp += item_cfg["effect_value"] * num

    total_exp = equip_data["exp"] + add_exp
    if not user_logic.check_game_values1(ki_user, gold=add_exp*50):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return

    level = level_checker(position, equip_data["quality"], total_exp)
    ki_user.equip.intensify(hero_id, position, level, total_exp)

    if items:
        pack_logic.remove_items(ki_user, items)
        user_logic.consume_game_values1(ki_user, gold=add_exp*50)

    context.result['mc'] = MsgCode['EquipIntensifySucc']

def upgrade(context):
    """提升品质

    Args:
        hero_id
        position  装备部位
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    position = context.get_parameter("position")

    if hero_id not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    equip_data = ki_user.equip.get_by_hero_position(hero_id, position)
    if not equip_data:
        context.result['mc'] = MsgCode['EquipNotExist']
        return

    if equip_data["quality"] >= game_config.equip_max_quality:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if not _check_module_open(position, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    equip_quality_cfg_key = "%s-%s" % (position, equip_data["quality"]+1)
    equip_quality_cfg = game_config.equip_upgrade_cfg.get(equip_quality_cfg_key)

    if equip_data["level"] < equip_quality_cfg["need_equip_level"]:
        context.result['mc'] = MsgCode['EquipQualityLevelLimit']
        return

    if ki_user.game_info.role_level < equip_quality_cfg["need_user_level"]:
        context.result['mc'] = MsgCode['EquipQualityLevelLimit']
        return

    # 检查材料是否足够
    if not pack_logic.check_items_enough(ki_user, equip_quality_cfg["material"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    ki_user.equip.upgrade(hero_id, position)
    level = level_checker(position, equip_data["quality"], equip_data["exp"])
    if position >= 5 and level != equip_data["level"]:
        ki_user.equip.intensify(hero_id, position, level, equip_data["exp"])

    pack_logic.remove_items(ki_user, equip_quality_cfg["material"])

    context.result['mc'] = MsgCode['EquipUpgradeSucc']

def weak(context):
    """觉醒，提升星级

    Args:
        hero_id
        position  装备部位
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    position = context.get_parameter("position")

    if not _check_module_open(position, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    if hero_id not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    equip_data = ki_user.equip.get_by_hero_position(hero_id, position)
    if not equip_data:
        context.result['mc'] = MsgCode['EquipNotExist']
        return

    if equip_data["star"] >= game_config.equip_max_star:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cfg_key = "%s-%s" % (equip_data["equip_id"], equip_data["star"]+1)
    cfg = game_config.equip_weak_cfg.get(cfg_key)
    if not cfg:
        context.result['mc'] = MsgCode['GameConfigNotExist']
        return

    # 检查材料是否足够
    if not pack_logic.check_items_enough(ki_user, cfg["material"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    ki_user.equip.weak(hero_id, position)
    pack_logic.remove_items(ki_user, cfg["material"])

    # 武器第一次觉醒时，更新该机甲的必杀技能
    if position == EQUIP_POSITION_WEAPON and equip_data["star"] == 1:
        from apps.logics import skill as skill_logic
        skill_logic.replace_bs_skill(ki_user, hero_id)

    context.result['mc'] = MsgCode['EquipWeakSucc']

def anti_weak(context):
    """降星 - 升星的逆操作

    Args:
        hero_id
        position  装备部位
    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    position = context.get_parameter("position")

    if not _check_module_open(position, ki_user.game_info.role_level):
        context.result['mc'] = MsgCode['UserModuleNotOpen']
        return

    if hero_id not in ki_user.hero.heros:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    equip_data = ki_user.equip.get_by_hero_position(hero_id, position)
    if not equip_data:
        context.result['mc'] = MsgCode['EquipNotExist']
        return

    # 0星你降个鸡毛啊
    if equip_data["star"] == 0:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cfg_key = "%s-%s" % (equip_data["equip_id"], equip_data["star"])
    cfg = game_config.equip_weak_cfg.get(cfg_key)
    if not cfg:
        context.result['mc'] = MsgCode['GameConfigNotExist']
        return

    # 检查消耗是否足够
    need_diamond = 30
    if not user_logic.check_game_values1(ki_user, diamond=need_diamond):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 返还材料
    pack_logic.add_items(ki_user, cfg["material"])
    ki_user.equip.anti_weak(hero_id, position)
    user_logic.consume_game_values1(ki_user, diamond=need_diamond)

    # 武器第一次觉醒时，更新该机甲的必杀技能， 如果1星降到0星，必杀技能被替换掉
    if position == EQUIP_POSITION_WEAPON and equip_data["star"] == 0:
        from apps.logics import skill as skill_logic
        skill_logic.replace_bs_skill(ki_user, hero_id, False)

    context.result['mc'] = MsgCode['EquipAntiWeakSucc']

# ========================= MODULE API =============================
def _check_module_open(position, role_level):
    """检测功能是否开启

    Args:
        position :装备位置
        role_level :玩家等级

    Return:
        bool
    """
    if position >= 5:
        func_id = 2104
    else:
        func_id = 2101

    open_level = game_config.user_func_cfg.get(func_id, 999)
    if open_level > role_level:
        return False
    else:
        return True

def level_checker(position, quality, exp):
    """等级修正器

    一次性吃太多经验造成的问题
    装备等级被装备品质限制

    """
    level = common_helper.get_level_by_exp(game_config.equip_exp_level_cfg, exp)
    quality_cfg = game_config.equip_upgrade_cfg.get("%s-%s" % (position, quality))

    return min(quality_cfg["equip_max_level"], level)
