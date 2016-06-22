#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   游戏静态配置文件
# @end
# @copyright (C) 2015, kimech

# ===============   GAME   =====================

# 角色初始化数据
USER_DEFAULT_HERO = 100050  # 头像跟随玩家拥有的机甲库而定，玩家头像在机甲头像中选择
# end

# 特殊道具ID
GOLD = 1            # 金币
DIAMOND = 2         # 钻石
ENERGY = 3          # 体力
ROLE_EXP = 4        # 玩家经验
ROLE_LEVEL = 5      # 玩家等级
VIP_EXP = 6         # VIP经验
VIP_LEVEL = 7       # VIP等级
HONOR_POINT = 8     # 荣誉
SKILL_POINT = 9     # 技能点
TALENT_POINT = 10   # 天赋点
TRIAL_POINT = 11    # 试炼币
GROUP_POINT = 12    # 帮贡
WEAK_POINT = 13     # 觉醒碎片
BOX_KEY = 14        # 宝箱钥匙
CLONE_POINT = 15    # 克隆币

# 特殊道具id列表
SPECIAL_ITEMS_LIST = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

# 特殊道具[id - 标识]映射表
SPECIAL_ITEMS_MAPPING = {
    1: "gold",
    2: "diamond",
    3: "current_energy",
    4: "role_exp",
    5: "role_level",
    6: "vip_exp",
    7: "vip_level",
    8: "honor_point",
    9: "current_skill_point",
    10: "talent_point",
    11: "trial_point",
    12: "group_point",
    13: "weak_point",
    14: "box_key",
    15: "clone_point",
}

# 等级达到才 战斗力计算才加这些属性
USER_FUNC_EQUIP_SPECIAL = 2104
USER_FUNC_WARSHIP_ATTR = 2205

USER_FUNC_MAPPING = {
    "hero.synthesis": 2000,
    "hero.exchange_chip": 2000,
    "hero.pick": 1110,
    "hero.intensify": 2001,
    "hero.upgrade": 2002,
    "hero.weak": 2003,
    "hero.feed": 1070,
    "hero.marry": 1070,
    "hero.divorce": 1070,

    "user.cdkey": 1090,
    "user.buy_skill_point": 1090,
    "user.buy_energy": 1100,
    "user.buy_gold": 1101,
    "user.skip_guide": 1090,

    "skill.intensify": 2004,

    "spirit.intensify": 2005,
    "spirit.intensify2": 2005,

    "array.update": 2006,

    "equip.intensify": 2101,
    "equip.intensify2": 2104,

    "arena.admire": 4030,
    "arena.start": 4030,
    "arena.fighter_data": 4030,
    "arena.fight": 4030,
    "arena.refresh": 4030,
    "arena.clean_cd": 4030,
    "arena.add_times": 4030,
    "arena.award": 4030,
    "arena.daily_award": 4030,
    "arena.history": 4030,
    "arena.replay": 4030,

    "talent.intensify": 1060,
    "talent.reset": 1060,

    "warship.intensify": 2202,
    "warship.upgrade": 2200,
    "warship.weak": 2201,
    "warship.intensify_skill": 2203,
    "warship.set_position": 2200,

    "mall.pick": 2204,

    "task.submit": 1120,
    "task.daily_submit": 1121,

    "chat.send": 1000,

    "mail.read": 1020,
    "mail.get_attachments": 1020,

    "sign.sign": 1030,
    "sign.award": 1030,
    "sign.resign": 1030,

    "package.use": 1090,
    "package.sale": 1090,
    "package.express_buy": 1090,

    "activity.award": 1050,
    "activity.info1": 1050,
    "activity.buy_level_fund": 1050,
    "activity.gamble": 1050,
    "activity.online_awards": 1050,

    "vip.charge": 1080,
    "vip.buy": 1080,
    "vip.refresh_pay": 1080,

    "trial.info": 4020,
    "trial.choose_fighter": 4020,
    "trial.fight": 4020,
    "trial.buy_buff": 4020,
    "trial.open_box": 4020,
    "trial.skip": 4020,
    "trial.award": 4020,

    "group.info": 5105,
    "group.info1": 5105,
    "group.rank": 5105,
    "group.game_info": 5105,
    "group.create": 5000,
    "group.search": 5105,
    "group.quick_search": 5105,
    "group.update": 5105,
    "group.appoint": 5105,
    "group.quit": 5105,
    "group.kick": 5105,
    "group.apply": 5105,
    "group.review": 5105,
    "group.deny_all": 5105,
    "group.donate": 5105,
    "group.game_tiger": 5100,
    "group.game_bird": 5101,
}
# ================ GAME END ====================

# ===============   HERO ATTR  =====================
HERO_ATTR_HP_BASE = 1001            # 基础生命
HERO_ATTR_HP_GROWTH = 1002          # 生命成长
HERO_ATTR_HP_PERCENT = 1003         # 生命百分比加成
HERO_ATTR_ATTACK_BASE = 1004        # 基础攻击
HERO_ATTR_ATTACK_GROWTH = 1005      # 攻击成长
HERO_ATTR_ATTACK_PERCENT = 1006     # 攻击百分比加成
HERO_ATTR_DEFEND_BASE = 1007        # 基础防御
HERO_ATTR_DEFEND_GROWTH = 1008      # 防御成长
HERO_ATTR_DEFEND_PERCENT = 1009     # 防御百分比加成
HERO_ATTR_SKILL_BASE = 1010         # 基础技巧
HERO_ATTR_SKILL_GROWTH = 1011       # 技巧成长
HERO_ATTR_SKILL_PERCENT = 1012      # 技巧百分比加成
HERO_ATTR_HIT_BASE = 1013           # 基础命中
HERO_ATTR_HIT_GROWTH = 1014         # 命中成长
HERO_ATTR_HIT_PERCENT = 1015        # 命中百分比加成
HERO_ATTR_MISS_BASE = 1016          # 基础闪避
HERO_ATTR_MISS_GROWTH = 1017        # 闪避成长
HERO_ATTR_MISS_PERCENT = 1018       # 闪避百分比加成
HERO_ATTR_SPEED_BASE = 1019         # 基础速度
HERO_ATTR_SPEED_GROWTH = 1020       # 速度成长
HERO_ATTR_SPEED_PERCENT = 1021      # 速度百分比加成
HERO_ATTR_HELP_RATE = 1048          # 援助概率
HERO_ATTR_HELP_SELF_HP = 1025       # 援助自身血量系数
HERO_ATTR_HELP_ENEMY_PARAM = 1026   # 援助敌方血量系数
HERO_ATTR_HELP_ROUND = 1027         # 援助回合系数
HERO_ATTR_CRIT_RATE = 1028          # 暴击概率
HERO_ATTR_CRIT_COEFF = 1029         # 暴击系数
HERO_ATTR_DMG_ADD = 1030            # 伤害加成
HERO_ATTR_DMG_REDUCE = 1031         # 伤害减少
HERO_ATTR_DMG_VALVE = 1033          # 伤害阀值
HERO_ATTR_MAGIC_RATE = 1032         # 奥义概率
HERO_ATTR_MAGIC_SELF_HP = 1046      # 奥义自身血量系数
HERO_ATTR_MAGIC_ROUND = 1047        # 奥义回合系数

HERO_ATTR_PT_SKILL_EFFECT = 1034            # 普通技能效果
HERO_ATTR_BS_SKILL_EFFECT = 1035            # 必杀技能效果
HERO_ATTR_YZ_SKILL_EFFECT = 1036            # 援助技能效果
HERO_ATTR_DC_SKILL_EFFECT = 1037            # 登场技能效果

HERO_ATTR_PT_SKILL_DEFEND = 1038            # 承受普通伤害减少
HERO_ATTR_BS_SKILL_DEFEND = 1039            # 承受必杀伤害减少
HERO_ATTR_YZ_SKILL_DEFEND = 1040            # 承受援助伤害减少
HERO_ATTR_DC_SKILL_DEFEND = 1041            # 登场技能伤害减少

HERO_ATTR_PT_SKILL_LEVEL = 1042         # 普通技能等级
HERO_ATTR_BS_SKILL_LEVEL = 1043         # 必杀技能等级
HERO_ATTR_YZ_SKILL_LEVEL = 1044         # 援助技能等级
HERO_ATTR_DC_SKILL_LEVEL = 1045         # 登场技能等级
# ================ HERO END =====================

# ===============   TASK   =====================
# 任务类型
TASK_TYPE_MAIN = 1                    # 主线任务类型
TASK_TYPE_DAILY = 2                   # 日常任务类型

# 任务目标类型
TASK_TARGET_MISSION_PAST = 1       # 通关副本
TASK_TARGET_USER_LEVEL = 2         # 战队等级
TASK_TARGET_HERO_NUMBER = 3        # 机甲数量达到指定数量
TASK_TARGET_HERO_QUALITY = 4       # n个姬甲升到n品级

TASK_TARGET_ARENA_FIGHT = 5            # 挑战n次竞技场
TASK_TARGET_HERO_LEVEL = 6             # 任意姬甲升n级
TASK_TARGET_TRIAL_TIMES = 7            # 完成n次试炼
TASK_TARGET_HERO_UPGRADE_TIMES = 8     # 进行n次姬甲升品
TASK_TARGET_HERO_PICK_TIMES = 9        # 抽卡n次
TASK_TARGET_BUY_GOLD = 10              # 进行n次金币购买
TASK_TARGET_BUY_ENERGY = 11             # 进行n次体力购买
TASK_TARGET_GROUP_DONATE = 12           # 进行n次公会捐献
TASK_TARGET_CONSUME_DIAMOND = 13       # 每日消费n钻石
TASK_TARGET_SKILL_LEVEL = 14            # 技能升级

TASK_TARGET_MISSION_PT_TIMES = 20   # 通关普通副本n次
TASK_TARGET_MISSION_JY_TIMES = 21     # 通关精英副本n次

TASK_TARGET_DAILY_GOLD_TIMES = 30       # 完成n次日常挑战（金币本）
TASK_TARGET_DAILY_EXP_TIMES = 31        # 完成n次日常挑战（经验本）

TASK_TARGET_TIME_TO_AWARD_5 = 40          # 到达指定时间【5点】领取物品
TASK_TARGET_TIME_TO_AWARD_12 = 41         # 到达指定时间【12点】领取物品
TASK_TARGET_TIME_TO_AWARD_15 = 42         # 到达指定时间【15点】领取物品
TASK_TARGET_TIME_TO_AWARD_18 = 43         # 到达指定时间【18点】领取物品
TASK_TARGET_TIME_TO_AWARD_21 = 44         # 到达指定时间【21点】领取物品

# 任务状态
TASK_STATE_DOING = 0              # 正在进行中
TASK_STATE_COMPLETED = 1          # 已经完成
TASK_STATE_SUBMITED = 2           # 已经提交

# 【日常】任务类型
TASK_DAILY_GET_ITEMS_TYPE = [40,41,42,43,44]
TASK_DAILY_VIP_GET_DIAMOND_TYPE = 51

# 特殊任务 》 特殊条件
# 到时间领取物品
TASK_TIME_TO_AWARD_MAP = {
                            40: ((0,0,0),(24,0,0)),
                            41: ((12,0,0),(14,0,0)),
                            42: ((15,0,0),(17,0,0)),
                            43: ((18,0,0),(20,0,0)),
                            44: ((21,0,0),(23,0,0)),
                        }
# ================ TASK END ====================

# ===============   SKILL   =====================
SKILL_TYPE = {
   "attr": 1,           # buff效果类型：属性变化
   "damage": 2,         # buff效果类型：造成伤害
   "cure": 3,           # buff效果类型：治疗效果
   "status": 4          # buff效果类型：状态：晕眩，缴械等
}

SKILL_TARGET = {
    "self": 1,                  # 施法者自己
    "caller": 2,                # 召唤者，适用于触发援助
    "blue_against_line": 3,     # 敌方对线 blue:敌方，red:己方
    "red_same_line": 4,         # 己方同线
    "blue_same_line": 5,        # 敌方同线
    "red_rand_one": 6,          # 随机单个己方
    "bule_rand_one": 7,         # 随机单个敌方
    "red_hp_lowest": 8,         # 己方血量百分比最低者
    "blue_hp_lowest": 9,        # 敌方血量百分比最低者
    "red_all": 10,              # 己方全体
    "blue_all": 11,             # 敌方全体
    "all": 12,                  # 场上全体
}

SKILL_EFFECT = {
    "damage": 1100,
    "last_damage": 1101,
    "cure": 1102,
    "last_cure": 1103,
    "ban_move": 1104,
    "ban_skill": 1105,
    "ban_help": 1106,
}
# ================ SKILL END ====================

# 默认角色阵容数据
DEFAULT_USER_ARRAY =[0,
{"equips": {"1": {"equip_id": 150307,"exp": 0,"level": 1,"quality": 0,"star": 0},
            "2": {"equip_id": 150801,"exp": 0,"level": 1,"quality": 0,"star": 0},
            "3": {"equip_id": 150802,"exp": 0,"level": 1,"quality": 0,"star": 0},
            "4": {"equip_id": 150803,"exp": 0,"level": 1,"quality": 0,"star": 0},
            "5": {"equip_id": 150903,"exp": 0,"level": 1,"quality": 0,"star": 0},
            "6": {"equip_id": 151003,"exp": 0,"level": 1,"quality": 0,"star": 0}},
    "exp": 0,"fates": [],"favor": 0,"fight": 617,"hero_id": 100050,"level": 1,"marry_id": 0,"quality": 0,
    "skills": {"110041": 1,"110042": 1},
    "spirits": {},
    "star": 2},
0,
0,
0,
0]

# ===============   VIP   =====================
VIP_SILVER_CARD_NEED_RMB = 25
VIP_GOLD_CARD_NEED_RMB = 88

VIP_CARD_REMAIN_SECONDS = 30 * 86400
