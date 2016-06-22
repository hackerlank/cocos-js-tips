#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-09-23 19:46:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   战舰业务逻辑接口
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

# ========================= GAME API ==============================
def intensify(context):
    """战舰升级

    战舰等级受战队等级和品质限制

    Args:
        ship_id 战舰ID
        to_level 到达的等级

    Returns:
        code 成功 | 失败
    """
    ki_user = context.user

    ship_id = context.get_parameter("ship_id")
    to_level = context.get_parameter("to_level")

    ship = ki_user.warship.get_warship_by_id(ship_id)
    if not ship:
        context.result['mc'] = MsgCode['WarshipNotExist']
        return

    if to_level <= ship["level"] or to_level > game_config.warship_max_level:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    quality_key = "%s-%s" % (ship_id, ship["quality"])
    quality_cfg = game_config.warship_upgrade_cfg[quality_key]
    if to_level > quality_cfg["max_level"]:
        context.result['mc'] = MsgCode['WarshipLevelOverLimit']
        return

    need_items = [game_config.warship_intensify_cfg[level] for level in range(ship["level"]+1, to_level + 1)]
    need_items1 = pack_logic.amend_goods(need_items)

    # 检查升级材料是否足够
    if not pack_logic.check_items_enough(ki_user, need_items1):
        import logging
        logging.error("%s -> %s need: %s need2: %s" % (ship["level"], to_level, need_items, need_items1))
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    ki_user.warship.intensify(ship_id, to_level)
    pack_logic.remove_items(ki_user, need_items1)

    context.result['mc'] = MsgCode['WarshipIntensifySucc']

def upgrade(context):
    """战舰升品

    Args:
        ship_id 战舰ID

    Returns:
        code 成功 | 失败
    """
    ki_user = context.user

    ship_id = context.get_parameter("ship_id")

    ship = ki_user.warship.get_warship_by_id(ship_id)
    if not ship:
        context.result['mc'] = MsgCode['WarshipNotExist']
        return

    if ship["quality"] >= game_config.warship_max_quality:
        context.result['mc'] = MsgCode['WarshipQualityMax']
        return

    quality_cfg = game_config.warship_upgrade_cfg["%s-%s" % (ship_id, ship["quality"]+1)]
    if ship["level"] < quality_cfg["need_level"] or \
        ki_user.game_info.role_level < quality_cfg["need_user_level"]:
        context.result['mc'] = MsgCode['WarshipLimitsNotEnough']
        return

    # 检查材料是否足够
    if not pack_logic.check_items_enough(ki_user, quality_cfg["material"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    pack_logic.remove_items(ki_user, quality_cfg["material"])
    ki_user.warship.upgrade(ship_id)

    context.result['mc'] = MsgCode['WarshipUpgradeSucc']

def weak(context):
    """战舰升星

    升级战斗星星，战舰觉醒技能或技能品级相应增加
    即战舰星级=战舰技能品级

    Args:
        ship_id 战舰ID

    Returns:
        code 成功 | 失败
    """
    ki_user = context.user

    ship_id = context.get_parameter("ship_id")

    ship = ki_user.warship.get_warship_by_id(ship_id)
    if not ship:
        context.result['mc'] = MsgCode['WarshipNotExist']
        return

    if ship["star"] >= game_config.warship_max_star:
        context.result['mc'] = MsgCode['WarshipStarMax']
        return

    weak_cfg = game_config.warship_weak_cfg["%s-%s" % (ship_id, ship["star"]+1)]
    # 检查材料是否足够
    if not pack_logic.check_items_enough(ki_user, weak_cfg["material"]):
        context.result['mc'] = MsgCode['PackageItemNotEnough']
        return

    pack_logic.remove_items(ki_user, weak_cfg["material"])
    ki_user.warship.weak(ship_id)

    # 升星成功之后监测是否开启战舰技能
    update_warship_skills(ki_user, ship_id, ship["star"])

    context.result['mc'] = MsgCode['WarshipWeakSucc']

def intensify_skill(context):
    """战舰技能升级

    Args:
        ship_id 战舰ID
        skill_id 战舰技能ID

    Returns:
        code 成功 | 失败
    """
    ki_user = context.user

    ship_id = context.get_parameter("ship_id")
    skill_id = context.get_parameter("skill_id")

    ship = ki_user.warship.get_warship_by_id(ship_id)
    if not ship:
        context.result['mc'] = MsgCode['WarshipNotExist']
        return

    if skill_id not in ship["skills"]:
        context.result['mc'] = MsgCode['WarshipSkillUnlock']
        return

    current_level = ship["skills"][skill_id]
    if current_level >= game_config.skill_max_level:
        context.result['mc'] = MsgCode['WarshipSkillLevelMax']
        return

    base_cfg = game_config.skill_cfg.get(skill_id)
    cfg_key = "%s-%s" % (base_cfg["type"], current_level+1)

    intensify_cfg = game_config.skill_intensify_cfg.get(cfg_key)
    # 检查材料是否足够
    if not user_logic.check_game_values1(ki_user, gold=intensify_cfg["gold"]):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return

    user_logic.consume_game_values1(ki_user, gold=intensify_cfg["gold"])
    ki_user.warship.intensify_skill(ship_id, skill_id)

    context.result['mc'] = MsgCode['WarshipSkillIntensifySucc']

def set_position(context):
    """战舰摆阵

    Args:
        ship_id 战舰ID
        position 战舰队形位置

    Returns:
        code 成功 | 失败
    """
    ki_user = context.user

    team = context.get_parameter("team", "[]")

    try:
        team = eval(team)
        if (not isinstance(team, list)) or (len(team) != 3):
            raise 1
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    for ship_id in team:
        if ship_id != 0 and ship_id not in ki_user.warship.ships:
            context.result['mc'] = MsgCode['WarshipNotExist']
            return

    # 更新数据库
    ki_user.warship.team = team
    ki_user.warship.put()

    context.result['mc'] = MsgCode['WarshipSetPositionSucc']

# ========================= MODULE API =============================
def unlock_ship(user, ship_id):
    """检测解锁战舰

    玩家升级后调用

    Args:
        user 用户对象
        level 用户最新等级
    """
    cfg_key = "%s-%s" % (ship_id, 0)
    unlock_skills = [skill for skill in game_config.warship_weak_cfg[cfg_key]["skills"] if skill]
    user.warship.unlock(ship_id, dict.fromkeys(unlock_skills, 1), False)

    # 如果队伍里还有位置，直接往上扔
    team = user.warship.team
    if 0 in team:
        empty_pos = team.index(0)
        user.warship.team[empty_pos] = ship_id

    user.warship.put()

def update_warship_skills(user, ship_id, ship_star):
    """升星战舰之后，更新战舰的技能

    Args:
        user 玩家对象
        ship_id 战舰ID
        ship_star 战舰当前星级
    """
    prev_cfg = game_config.warship_weak_cfg.get("%s-%s" % (ship_id, ship_star-1))
    cfg = game_config.warship_weak_cfg.get("%s-%s" % (ship_id, ship_star))

    ship = user.warship.get_warship_by_id(ship_id)
    for index in range(3):
        old_skill = prev_cfg["skills"][index]
        new_skill = cfg["skills"][index]
        # 前一品级的技能已学会
        if old_skill:
            level = ship["skills"][old_skill]
            del ship["skills"][old_skill]
            ship["skills"][new_skill] = level
        else:
            # 前一品级的技能未学会, 当前品级的技能不为空则
            # 解锁为新技能，为空则此星级没有解锁任何技能
            if new_skill:
                ship["skills"][new_skill] = 1

    user.warship.put()
