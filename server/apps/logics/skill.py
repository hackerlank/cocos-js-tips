#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-21 15:46:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   技能业务逻辑接口
# @end
# @copyright (C) 2015, kimech

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics import user as user_logic
from apps.logics import equip as equip_logic

# ========================= GAME API ==============================
def intensify(context):
    """升级技能

    技能等级受机甲等级限制

    Args:
        hero_id 机甲ID
        skill_id 技能ID

    Returns:

    """
    ki_user = context.user

    hero_id = context.get_parameter("hero_id")
    skill_id = context.get_parameter("skill_id")
    level = context.get_parameter("level")

    if level not in range(1,101):
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    skills = ki_user.skill.get_skills_by_hero_id(hero_id)
    if skill_id not in skills:
        context.result['mc'] = MsgCode['SkillNotWeaken']
        return

    if skills[skill_id]+level > hero["level"]:
        context.result['mc'] = MsgCode['SkillLevelMax']
        return

    consume = {1:0, 9:0}
    current_level = skills[skill_id]
    base_cfg = game_config.skill_cfg.get(skill_id)
    for i in range(current_level+1, current_level+level+1):
        level_cfg = game_config.skill_intensify_cfg.get("%s-%s" % (base_cfg["type"], i))
        if not level_cfg:
            context.result['mc'] = MsgCode['SkillLevelFull']
            return
        else:
            consume[1] += level_cfg["gold"]
            consume[9] += level_cfg["skill_point"]

    # 检查金币是否足够
    if not user_logic.check_game_values1(ki_user, gold=consume[1]):
        context.result['mc'] = MsgCode['GoldNotEnough']
        return
    # 检查技能点是否足够
    if not user_logic.check_game_values1(ki_user, skill_point=consume[9]):
        context.result['mc'] = MsgCode['SkillPointNotEnough']
        return

    user_logic.consume_game_values1(ki_user, gold=consume[1], current_skill_point=consume[9])
    ki_user.skill.intensify(hero_id, skill_id, level)

    context.result['mc'] = MsgCode['SkillLevelUpSucc']

# ========================= MODULE API =============================
def append_hero_skill(user, hero_id, hero_star, instant_save=True):
    """更新机甲的技能

    获得机甲和机甲升星的时候调用此接口

    """
    cfg = game_config.hero_base_cfg.get(hero_id)
    for index, skill_id in enumerate(cfg["skills"].itervalues()):
        skill_cfg = game_config.skill_cfg.get(skill_id)
        had_skills = user.skill.get_skills_by_hero_id(hero_id)
        # 技能符合觉醒条件
        if (hero_star >= skill_cfg["weak_star"]) and (skill_id not in had_skills):
            if index != 1:
                user.skill.append_skill(hero_id, skill_id)
            else:
                # 如果要增加必杀技能时，需要检测武器是否已觉醒（0-1星），觉醒前和觉醒后的技能不一样
                equip = user.equip.get_by_hero_position(hero_id, equip_logic.EQUIP_POSITION_WEAPON)
                if equip["star"] >= 1:
                    if cfg["weapon_weak_skill"] not in had_skills:
                        user.skill.append_skill(hero_id, cfg["weapon_weak_skill"])
                else:
                    user.skill.append_skill(hero_id, skill_id)

    if instant_save:
        user.skill.put()

def replace_bs_skill(user, hero_id, update=True):
    """武器觉醒(0星 - 1星)替换机甲的必杀技能

    武器第一次升星的时候调用
    Tip: 武器觉醒的时候，机甲还未获得必杀技能

    Args:
        hero_id 机甲ID
        update 升级 & 降级
    """
    cfg = game_config.hero_base_cfg.get(hero_id)
    old_skill_id = cfg["skills"]["bs"]
    new_skill_id = cfg["weapon_weak_skill"]

    had_skills = user.skill.get_skills_by_hero_id(hero_id)
    if update:
        if old_skill_id in had_skills and new_skill_id != 0:
            user.skill.replace_skill(hero_id, old_skill_id, new_skill_id)
    else:
        if new_skill_id in had_skills:
            user.skill.replace_skill(hero_id, new_skill_id, old_skill_id)
