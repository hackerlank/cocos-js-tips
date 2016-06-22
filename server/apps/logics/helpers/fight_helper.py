#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-12 20:02:24
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   战力计算处理器
# @end
# @copyright (C) 2015, kimech

import copy

from apps.configs import game_config
from apps.configs import static_const

# attrs_dict = {
#     1001: "HERO_ATTR_HP_BASE",
#     1002: "HERO_ATTR_HP_GROWTH",
#     1003: "HERO_ATTR_HP_PERCENT",
#     1004: "HERO_ATTR_ATTACK_BASE",
#     1005: "HERO_ATTR_ATTACK_GROWTH",
#     1006: "HERO_ATTR_ATTACK_PERCENT",
#     1007: "HERO_ATTR_DEFEND_BASE",
#     1008: "HERO_ATTR_DEFEND_GROWTH",
#     1009: "HERO_ATTR_DEFEND_PERCENT",
#     1010: "HERO_ATTR_SKILL_BASE",
#     1011: "HERO_ATTR_SKILL_GROWTH",
#     1012: "HERO_ATTR_SKILL_PERCENT",
#     1013: "HERO_ATTR_HIT_BASE",
#     1014: "HERO_ATTR_HIT_GROWTH",
#     1015: "HERO_ATTR_HIT_PERCENT",
#     1016: "HERO_ATTR_MISS_BASE",
#     1017: "HERO_ATTR_MISS_GROWTH",
#     1018: "HERO_ATTR_MISS_PERCENT",
#     1019: "HERO_ATTR_SPEED_BASE",
#     1020: "HERO_ATTR_SPEED_GROWTH",
#     1021: "HERO_ATTR_SPEED_PERCENT",
#     1048: "HERO_ATTR_HELP_RATE",
#     1025: "HERO_ATTR_HELP_SELF_HP",
#     1026: "HERO_ATTR_HELP_ENEMY_PARAM",
#     1027: "HERO_ATTR_HELP_ROUND",
#     1028: "HERO_ATTR_CRIT_RATE",
#     1029: "HERO_ATTR_CRIT_COEFF",
#     1030: "HERO_ATTR_DMG_ADD",
#     1031: "HERO_ATTR_DMG_REDUCE",
#     1033: "HERO_ATTR_DMG_VALVE",
#     1032: "HERO_ATTR_MAGIC_RATE",
#     1046: "HERO_ATTR_MAGIC_SELF_HP",
#     1047: "HERO_ATTR_MAGIC_ROUND",

#     1034: "HERO_ATTR_PT_SKILL_EFFECT",
#     1035: "HERO_ATTR_BS_SKILL_EFFECT",
#     1036: "HERO_ATTR_YZ_SKILL_EFFECT",
#     1037: "HERO_ATTR_DC_SKILL_EFFECT",

#     1038: "HERO_ATTR_PT_SKILL_DEFEND",
#     1039: "HERO_ATTR_BS_SKILL_DEFEND",
#     1040: "HERO_ATTR_YZ_SKILL_DEFEND",
#     1041: "HERO_ATTR_DC_SKILL_DEFEND",

#     1042: "HERO_ATTR_PT_SKILL_LEVEL",
#     1043: "HERO_ATTR_BS_SKILL_LEVEL",
#     1044: "HERO_ATTR_YZ_SKILL_LEVEL",
#     1045: "HERO_ATTR_DC_SKILL_LEVEL",
# }

def _get_attr_base_value(hero, attr_id):
    attr_value = 0
    # 来自属性
    type_attr = hero.base_cfg["type_attr"]
    attr_cfg = game_config.hero_rand_attr_cfg.get(type_attr)
    # attr_value += attr_cfg["value"] if attr_cfg["attr_id"] == attr_id else 0
    # print "attr_value1: ", attr_cfg["value"]
    # 来自品质提升
    upgrade_cfg = game_config.hero_upgrade_cfg.get("%s-%s" % (hero.base_cfg["type"], hero.quality))
    if attr_id in upgrade_cfg["attrs"]:
        # print "attr_value2: ", upgrade_cfg["attrs"][attr_id]
        attr_value += upgrade_cfg["attrs"][attr_id]

    # 来自星级提升
    weak_cfg = game_config.hero_weak_cfg.get("%s-%s" % (hero.hero_id, hero.star))
    if attr_id in weak_cfg["attrs"]:
        # print "attr_value3: ", weak_cfg["attrs"][attr_id]
        attr_value += weak_cfg["attrs"][attr_id]

    return attr_value

def _get_attr_from_equip(hero, attr_id, level):
    attr_value = 0

    for equip_pos, equip_data in hero.equips.items():
        if equip_pos >= 5 and level < game_config.user_func_cfg[static_const.USER_FUNC_EQUIP_SPECIAL]:
            continue
        else:
            base_cfg = game_config.equip_cfg.get(equip_data["equip_id"])
            if attr_id in base_cfg["attrs"]:
                attr_pos = base_cfg["attrs"].index(attr_id)
                # 来自品质，强化部分
                key = "%s-%s-%s" % (base_cfg["type"], equip_data["quality"], equip_data["level"])
                attr_cfg = game_config.equip_attr_cfg.get(key)
                attr_value += attr_cfg["attr_values"][attr_pos]
                # print "attr_value: %s %s" % (equip_pos, attr_cfg["attr_values"][attr_pos])
                # 来自星级部分
                key1 = "%s-%s" % (equip_data["equip_id"], equip_data["star"])
                weak_cfg = game_config.equip_weak_cfg.get(key1)
                attr_value += weak_cfg["attr_values"][attr_pos]
                # print "attr_value: %s %s" % (equip_pos, weak_cfg["attr_values"][attr_pos])

    return attr_value

def _get_attr_from_fate(hero, attr_id):
    attr_value = 0
    for fate in hero.fates:
        fate_cfg = game_config.hero_fate_cfg.get(fate)
        if fate_cfg["attr_id"] == attr_id:
            attr_value += fate_cfg["attr_value"]

    return attr_value

def _get_attr_from_skill(hero, attr_id):
    attr_value = 0

    psv_skills = [hero.base_cfg["skills"]["bd1"], hero.base_cfg["skills"]["bd2"]]
    for skill_id in psv_skills:
        if skill_id and skill_id in hero.skills:
            skill_level = hero.skills.get(skill_id, 0)
            skill_cfg = game_config.skill_cfg.get(skill_id)
            for skill_effect_id in skill_cfg["attrs"]:
                if skill_effect_id:
                    skill_effect_cfg = game_config.skill_effect_cfg.get(skill_effect_id)
                    if skill_effect_cfg["attr_id"] == attr_id:
                        attr_base = skill_effect_cfg["attr_base_value"] + (skill_level - 1) * skill_effect_cfg["attr_base_growth"]
                        attr_coeff_b = skill_effect_cfg["skill_coeff_b"] + (skill_level - 1) * skill_effect_cfg["skill_coeff_b_growth"]

                        attr_value = attr_base + hero.skill * attr_coeff_b

    return attr_value

def _get_attr_from_talent(hero, attr_id):
    attr_value = 0
    for talent_id in hero.talents:
        talent_cfg = game_config.talent_detail_cfg.get(talent_id)
        if talent_cfg["attr_a"] == attr_id:
            attr_value += talent_cfg["attr_a_value"] + (hero.talents[talent_id] - 1) * talent_cfg["attr_a_growth"]

    return attr_value

def _get_attr_from_spirit(hero, attr_id):
    attr_value = 0
    for spirit_id, data in hero.spirits.items():
        cfg = game_config.spirit_cfg.get(spirit_id)
        if cfg["attrs"]["id"] == attr_id:
            attr_value += cfg["attrs"]["value"] + (data["level"] - 1) * cfg["attrs"]["growth"]

    return attr_value

def _get_attr_from_warship(hero, attr_id, level):
    attr_value = 0
    if level < game_config.user_func_cfg[static_const.USER_FUNC_WARSHIP_ATTR]:
        return attr_value

    for id, ship_data in hero.warships.items():
        base_cfg = game_config.warship_cfg.get(id)
        if attr_id in base_cfg["attrs"]:
            attr_pos = base_cfg["attrs"].index(attr_id)
            # 星级 强化部分
            weak_cfg = game_config.warship_weak_cfg.get("%s-%s" % (id, ship_data["star"]))
            attr_growth = weak_cfg["attr_growths"][attr_pos]
            # 品质部分
            quality_cfg = game_config.warship_upgrade_cfg.get("%s-%s" % (id, ship_data["quality"]))
            attr_value += weak_cfg["attrs"][attr_pos] + (ship_data["level"] - 1) * attr_growth + quality_cfg["attrs"][attr_pos]

    return attr_value

def _get_attr_from_favor(hero, attr_id):
    attr_value = 0
    favor_level = max([(i, cfg["level"]) for i,cfg in game_config.favor_level_cfg.items() if cfg["favor"] <= hero.favor])

    cfg = game_config.favor_level_cfg.get(favor_level[0])

    if attr_id in cfg["attr_a"].keys():
        attr_value += cfg["attr_a"][attr_id]
    elif attr_id in cfg["attr_b"].keys():
        attr_value += cfg["attr_b"][attr_id]
    elif attr_id in cfg["attr_c"].keys():
        attr_value += cfg["attr_c"][attr_id]
    elif attr_id in cfg["attr_d"].keys():
        attr_value += cfg["attr_d"][attr_id]
    elif attr_id in cfg["attr_e"].keys():
        attr_value += cfg["attr_e"][attr_id]
    else:
        pass

    # 速度值还要加上同系姬甲好感度增加值
    if attr_id == static_const.HERO_ATTR_SPEED_BASE:
        return attr_value + hero.favor_speed
    elif attr_id == static_const.HERO_ATTR_SPEED_PERCENT and hero.marry != 0:
        marry_cfg = game_config.favor_marry_cfg.get(hero.marry)
        return marry_cfg["attr"][attr_id] + attr_value
    else:
        return attr_value

class Fight(object):
    """计算机甲战力类
    """
    def __init__(self, hero, equips, skills, spirits, fates, talents, warships, favor_speed, role_level):
        self.hero_id = hero["hero_id"]
        self.exp = hero["exp"]
        self.level = hero["level"]
        self.star = hero["star"]
        self.quality = hero["quality"]
        self.favor = hero["favor"]
        self.marry = hero["marry_id"]
        self.role_level = role_level

        self.favor_speed = favor_speed  # 同系姬甲带来的速度值增长

        # 最终计算值
        self._fight = 0

        self.base_cfg = copy.deepcopy(game_config.hero_base_cfg.get(self.hero_id))
        self.equips = copy.deepcopy(equips)
        self.skills = copy.deepcopy(skills)
        self.spirits = copy.deepcopy(spirits)
        self.talents = copy.deepcopy(talents)
        self.warships = copy.deepcopy(warships)
        self.fates = fates

        self._hp = 0             # 面板生命 * 面板生命系数
        self._attack = 0             # 面板攻击 * 面板攻击系数
        self._defend = 0             # 面板防御 * 面板防御系数
        self._skill = 0              # 面板技巧 * 面板技巧系数
        self._hit = 0            # 面板命中 * 面板命中系数
        self._miss = 0               # 面板闪避 * 面板闪避系数
        self._speed = 0              # 面板速度 * 面板速度系数
        self._help_rate = 0              # 援助概率 * 援助概率系数
        self._help_self_hp = 0               # 援助自身血量系数 * 援助自身血量系数系数
        self._help_round = 0             # 援助回合系数 * 援助回合系数系数
        self._magic_rate = 0             # 奥义概率 * 奥义概率系数
        self._magic_self_hp = 0              # 奥义自身血量系数 * 奥义自身血量系数系数
        self._magic_round = 0            # 奥义回合系数 * 奥义回合系数系数
        self._crit_rate = 0              # 暴击概率 * 暴击概率系数
        self._crit_coeff = 0             # 暴击系数 * 暴击系数系数
        self._dmg_add = 0            # 伤害加成 * 伤害加成系数
        self._dmg_reduce = 0             # 伤害减少 * 伤害减少系数
        self._base_coeff = 0            # 机甲基础系数 觉醒前 / 觉醒后

        self._pt_skill_effect = 0            # 普通技能效果 * 普通技能效果系数
        self._bs_skill_effect = 0            # 奥义技能效果 * 奥义技能效果系数
        self._yz_skill_effect = 0            # 援助技能效果 * 援助技能效果系数
        self._dc_skill_effect = 0            # 登场技能效果 * 登场技能效果系数

        self._pt_skill_defend = 0            # 普通技能抗性 * 普通技能抗性系数
        self._bs_skill_defend = 0            # 奥义技能抗性 * 奥义技能抗性系数
        self._yz_skill_defend = 0            # 援助技能抗性 * 援助技能抗性系数
        self._dc_skill_defend = 0            # 登场技能抗性 * 登场技能抗性系数

    @property
    def fight(self):
        if not self._fight:
            # print "hero_id:        %s" % self.hero_id

            a = self.hp + self.attack + self.defend + self.skill

            # print "a:%s, %s, %s, %s" % (self.hp, self.attack, self.defend, self.skill)

            b = self.hit + self.miss + self.speed + self.help_rate + \
                self.help_self_hp + self.help_round + self.magic_rate + \
                self.magic_self_hp + self.magic_round + self.crit_rate + \
                self.crit_coeff + self.dmg_add + self.dmg_reduce

            # print "b:%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" % (self.hit, self.miss, self.speed, self.help_rate, self.help_self_hp, self.help_round, self.magic_rate, self.magic_self_hp, self.magic_round, self.crit_rate, self.crit_coeff, self.dmg_add, self.dmg_reduce)

            c = self.pt_skill_effect + self.bs_skill_effect + self.yz_skill_effect + \
                self.dc_skill_effect + self.pt_skill_defend + self.bs_skill_defend + \
                self.yz_skill_defend + self.dc_skill_defend

            pt_skill_level = self.get_skill_level(self, "pt")
            bs_skill_level = self.get_skill_level(self, "bs")
            dc_skill_level = self.get_skill_level(self, "dc")
            yz_skill_level = self.get_skill_level(self, "yz")


            d = self.base_coeff * (1 + (pt_skill_level + bs_skill_level + \
                dc_skill_level + yz_skill_level) * 0.0005) * 0.1

            # print "a.", a
            # print "b.", b
            # print "c.", c
            # print "base_coeff %s %s %s %s %s " % (self.base_coeff, pt_skill_level, bs_skill_level, dc_skill_level, yz_skill_level)
            # print "d.", d
            self._fight = int((a + 100) * (1 + 0.3 * b) * (d + 0.3 * c))

            # print "fight: ", self._fight
        return self._fight

    @property
    def base_coeff(self):
        if not self._base_coeff:
            # 武器觉醒前和武器觉醒后两个不同的基础值
            weapon_star = self.equips[1]["star"]
            weak_cfg = game_config.hero_weak_cfg.get("%s-%s" % (self.hero_id, self.star))
            self._base_coeff = weak_cfg["base_coeff_b"] if weapon_star > 0 else weak_cfg["base_coeff_a"]

        return self._base_coeff

    @property
    def hp(self):
        if not self._hp:
            value_id = static_const.HERO_ATTR_HP_BASE
            growth_id = static_const.HERO_ATTR_HP_GROWTH
            percent_id = static_const.HERO_ATTR_HP_PERCENT

            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1001)

            self._hp = base * coeff

        return self._hp

    @property
    def attack(self):
        if not self._attack:
            value_id = static_const.HERO_ATTR_ATTACK_BASE
            growth_id = static_const.HERO_ATTR_ATTACK_GROWTH
            percent_id = static_const.HERO_ATTR_ATTACK_PERCENT
            # print "ATTACK:"
            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1004)
            # 最终值 = 值 * 系数
            self._attack = base * coeff

        return self._attack

    @property
    def defend(self):
        if not self._defend:
            value_id = static_const.HERO_ATTR_DEFEND_BASE
            growth_id = static_const.HERO_ATTR_DEFEND_GROWTH
            percent_id = static_const.HERO_ATTR_DEFEND_PERCENT
            # print "DEFFEND:"
            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1007)
            # 最终值 = 值 * 系数
            self._defend = base * coeff

        return self._defend

    @property
    def skill(self):
        if not self._skill:
            value_id = static_const.HERO_ATTR_SKILL_BASE
            growth_id = static_const.HERO_ATTR_SKILL_GROWTH
            percent_id = static_const.HERO_ATTR_SKILL_PERCENT
            # print "SKILL:"
            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1010)
            # 最终值 = 值 * 系数
            self._skill = base * coeff

        return self._skill

    @property
    def hit(self):
        if not self._hit:
            value_id = static_const.HERO_ATTR_HIT_BASE
            growth_id = static_const.HERO_ATTR_HIT_GROWTH
            percent_id = static_const.HERO_ATTR_HIT_PERCENT

            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1013)
            # 最终值 = 值 * 系数
            self._hit = base * coeff
            # print ">>>>>>>>>>>>>>>>> hit: %s * %s = %s" %(base, coeff, base * coeff)

        return self._hit

    @property
    def miss(self):
        if not self._miss:
            value_id = static_const.HERO_ATTR_MISS_BASE
            growth_id = static_const.HERO_ATTR_MISS_GROWTH
            percent_id = static_const.HERO_ATTR_MISS_PERCENT

            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1016)
            # 最终值 = 值 * 系数
            self._miss = base * coeff
            # print ">>>>>>>>>>>>>>>>> miss: %s * %s = %s" %(base, coeff, base * coeff)

        return self._miss

    @property
    def speed(self):
        if not self._speed:
            value_id = static_const.HERO_ATTR_SPEED_BASE
            growth_id = static_const.HERO_ATTR_SPEED_GROWTH
            percent_id = static_const.HERO_ATTR_SPEED_PERCENT

            base = self.get_attr_1(self, value_id, growth_id, percent_id)
            coeff = game_config.fight_coeff_cfg.get(1019)
            # 最终值 = 值 * 系数
            self._speed = base * coeff
            # print ">>>>>>>>>>>>>>>>> speed: %s * %s = %s" %(base, coeff, base * coeff)

        return self._speed

    @property
    def help_rate(self):
        if not self._help_rate:
            value_id = static_const.HERO_ATTR_HELP_RATE
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1048)
            # 最终值 = 值 * 系数
            self._help_rate = base * coeff

        return self._help_rate

    @property
    def help_self_hp(self):
        if not self._help_self_hp:
            value_id = static_const.HERO_ATTR_HELP_SELF_HP
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1025)
            # 最终值 = 值 * 系数
            self._help_self_hp = base * coeff

        return self._help_self_hp

    @property
    def help_round(self):
        if not self._help_round:
            value_id = static_const.HERO_ATTR_HELP_ROUND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1027)
            # 最终值 = 值 * 系数
            self._help_round = base * coeff

        return self._help_round

    @property
    def magic_rate(self):
        if not self._magic_rate:
            value_id = static_const.HERO_ATTR_MAGIC_RATE
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1032)
            # 最终值 = 值 * 系数
            self._magic_rate = base * coeff

        return self._magic_rate

    @property
    def magic_self_hp(self):
        if not self._magic_self_hp:
            value_id = static_const.HERO_ATTR_MAGIC_SELF_HP
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1046)
            # 最终值 = 值 * 系数
            self._magic_self_hp = base * coeff

        return self._magic_self_hp

    @property
    def magic_round(self):
        if not self._magic_round:
            value_id = static_const.HERO_ATTR_MAGIC_ROUND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1047)
            # 最终值 = 值 * 系数
            self._magic_round = base * coeff

        return self._magic_round

    @property
    def crit_rate(self):
        if not self._crit_rate:
            value_id = static_const.HERO_ATTR_CRIT_RATE
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1028)
            # 最终值 = 值 * 系数
            self._crit_rate = base * coeff

        return self._crit_rate

    @property
    def crit_coeff(self):
        if not self._crit_coeff:
            value_id = static_const.HERO_ATTR_CRIT_COEFF
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1029)
            # 最终值 = 值 * 系数
            self._crit_coeff = base * coeff

        return self._crit_coeff

    @property
    def dmg_add(self):
        if not self._dmg_add:
            value_id = static_const.HERO_ATTR_DMG_ADD
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1030)
            # 最终值 = 值 * 系数
            self._dmg_add = base * coeff

        return self._dmg_add

    @property
    def dmg_reduce(self):
        if not self._dmg_reduce:
            value_id = static_const.HERO_ATTR_DMG_REDUCE
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1031)
            # 最终值 = 值 * 系数
            self._dmg_reduce = base * coeff

        return self._dmg_reduce

    @property
    def pt_skill_effect(self):
        if not self._pt_skill_effect:
            value_id = static_const.HERO_ATTR_PT_SKILL_EFFECT
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1034)
            # 最终值 = 值 * 系数
            self._pt_skill_effect = base * coeff

        return self._pt_skill_effect

    @property
    def bs_skill_effect(self):
        if not self._bs_skill_effect:
            value_id = static_const.HERO_ATTR_BS_SKILL_EFFECT
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1035)
            # 最终值 = 值 * 系数
            self._bs_skill_effect = base * coeff

        return self._bs_skill_effect

    @property
    def yz_skill_effect(self):
        if not self._yz_skill_effect:
            value_id = static_const.HERO_ATTR_YZ_SKILL_EFFECT
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1036)
            # 最终值 = 值 * 系数
            self._yz_skill_effect = base * coeff

        return self._yz_skill_effect

    @property
    def dc_skill_effect(self):
        if not self._dc_skill_effect:
            value_id = static_const.HERO_ATTR_DC_SKILL_EFFECT
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1037)
            # 最终值 = 值 * 系数
            self._dc_skill_effect = base * coeff

        return self._dc_skill_effect

    @property
    def pt_skill_defend(self):
        if not self._pt_skill_defend:
            value_id = static_const.HERO_ATTR_PT_SKILL_DEFEND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1038)
            # 最终值 = 值 * 系数
            self._pt_skill_defend = base * coeff

        return self._pt_skill_defend

    @property
    def bs_skill_defend(self):
        if not self._bs_skill_defend:
            value_id = static_const.HERO_ATTR_BS_SKILL_DEFEND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1039)
            # 最终值 = 值 * 系数
            self._bs_skill_defend = base * coeff

        return self._bs_skill_defend

    @property
    def yz_skill_defend(self):
        if not self._yz_skill_defend:
            value_id = static_const.HERO_ATTR_YZ_SKILL_DEFEND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1040)
            # 最终值 = 值 * 系数
            self._yz_skill_defend = base * coeff

        return self._yz_skill_defend

    @property
    def dc_skill_defend(self):
        if not self._dc_skill_defend:
            value_id = static_const.HERO_ATTR_DC_SKILL_DEFEND
            base = self.get_attr_2(self, value_id)
            coeff = game_config.fight_coeff_cfg.get(1041)
            # 最终值 = 值 * 系数
            self._dc_skill_defend = base * coeff

        return self._dc_skill_defend

    @staticmethod
    def get_attr_1(hero, attr_value_id, attr_growth_id, attr_percent_id):
        """机甲基础数值 【生命，攻击，防御，技巧，命中，闪避，速度】
        """
        # 基础属性值主要来自机甲类型属性值
        # 强化等级 * 成长
        # print attr_value_id
        weak_cfg = game_config.hero_weak_cfg.get("%s-%s" % (hero.hero_id, hero.star))
        value_from_intensify = (hero.level - 1) * weak_cfg["attrs"][attr_growth_id]

        value_base = _get_attr_base_value(hero, attr_value_id)
        # print "value_base:", value_base
        value_from_equip = _get_attr_from_equip(hero, attr_value_id, hero.role_level)
        # print "value_from_equip:", value_from_equip
        value_from_fate = _get_attr_from_fate(hero, attr_value_id)
        # print "value_from_fate:", value_from_fate
        value_from_skill = _get_attr_from_skill(hero, attr_value_id)
        # print "value_from_skill:", value_from_skill
        value_from_talent = _get_attr_from_talent(hero, attr_value_id)
        value_from_warship = _get_attr_from_warship(hero, attr_value_id, hero.role_level)
        value_from_favor = _get_attr_from_favor(hero, attr_value_id)
        value_from_spirit = _get_attr_from_spirit(hero, attr_value_id)

        # print "基础:%s 等级:%s 装备:%s 情缘:%s 技能:%s 天赋:%s 战舰:%s 好感度:%s 战魂:%s" % (value_base, value_from_intensify, value_from_equip, value_from_fate, value_from_skill, value_from_talent, value_from_warship, value_from_favor, value_from_spirit)

        percent_base = _get_attr_base_value(hero, attr_percent_id)
        # print "percent_base:", percent_base
        percent_from_equip = _get_attr_from_equip(hero, attr_percent_id, hero.role_level)
        # print "percent_from_equip:", percent_from_equip
        percent_from_fate = _get_attr_from_fate(hero, attr_percent_id)
        # print "percent_from_fate:", percent_from_fate
        percent_from_skill = _get_attr_from_skill(hero, attr_percent_id)
        # print "percent_from_skill:", percent_from_skill
        percent_from_talent = _get_attr_from_talent(hero, attr_percent_id)
        percent_from_warship = _get_attr_from_warship(hero, attr_percent_id, hero.role_level)
        percent_from_favor = _get_attr_from_favor(hero, attr_percent_id)
        percent_from_spirit = _get_attr_from_spirit(hero, attr_percent_id)

        # print "基础:%s 装备:%s 情缘:%s 技能:%s 天赋:%s 战舰:%s 好感度:%s 战魂:%s" % (percent_base, percent_from_equip, percent_from_fate, percent_from_skill, percent_from_talent, percent_from_warship, percent_from_favor, percent_from_spirit)

        value_total = value_base + value_from_equip + value_from_fate + value_from_intensify + \
                      value_from_skill + value_from_talent + value_from_warship + value_from_favor + value_from_spirit

        percent_total = percent_base + percent_from_equip + percent_from_fate + percent_from_skill + \
                        percent_from_talent + percent_from_warship + percent_from_favor + percent_from_spirit

        # print "value_total * (1 + percent_total):", value_total, percent_total, value_total * (1 + percent_total)

        return value_total * (1 + percent_total)

    @staticmethod
    def get_attr_2(hero, attr_value_id):
        """机甲高级数值 【援助概率，援助自身血量系数，援助回合系数，奥义概率，奥义自身血量系数，
                        奥义回合系数，暴击概率，暴击系数，伤害加成，伤害减少，普通技能效果，奥义技能效果，
                        援助技能效果，登场技能效果，普通技能抗性，奥义技能抗性，援助技能抗性，登场技能抗性】
        """
        # print "attr_value_id", attr_value_id
        # print "attr_value_id", attr_value_id
        value_from_equip = _get_attr_from_equip(hero, attr_value_id, hero.role_level)
        # print "value_from_equip", value_from_equip
        value_from_fate = _get_attr_from_fate(hero, attr_value_id)
        # print "value_from_fate", value_from_fate
        value_from_skill = _get_attr_from_skill(hero, attr_value_id)
        # print "value_from_skill", value_from_skill
        value_from_talent = _get_attr_from_talent(hero, attr_value_id)
        value_from_warship = _get_attr_from_warship(hero, attr_value_id, hero.role_level)
        value_from_favor = _get_attr_from_favor(hero, attr_value_id)
        value_from_spirit = _get_attr_from_spirit(hero, attr_value_id)

        # print attrs_dict[attr_value_id]
        # print value_from_equip, value_from_fate, value_from_skill, value_from_talent, value_from_warship, value_from_favor, value_from_spirit
        # print "装备:%s 情缘:%s 技能:%s 天赋:%s 战舰:%s 好感度:%s 战魂:%s" % (value_from_equip, value_from_fate, value_from_skill, value_from_talent, value_from_warship, value_from_favor, value_from_spirit)

        value_total = value_from_equip + value_from_fate + value_from_skill + value_from_talent + \
                      value_from_warship + value_from_favor + value_from_spirit
        # print "===================2====================="
        return value_total

    @staticmethod
    def get_skill_level(hero, skill_type):
        # 奥义技能需要判断玩家武器是否觉醒，觉醒后是否会更换奥义技能
        if skill_type == "bs":
            weapon_star = hero.equips[1]["star"]
            weak_skill_id = hero.base_cfg["weapon_weak_skill"]
            if weapon_star > 0 and weak_skill_id != 0:
                skill_id = weak_skill_id
            else:
                skill_id = hero.base_cfg["skills"]["bs"]
        else:
            skill_id = hero.base_cfg["skills"][skill_type]

        # print skill_id, hero.skills.get(skill_id, 0)

        return hero.skills.get(skill_id, 0)

