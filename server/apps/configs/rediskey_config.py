#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2016-03-04 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       REDIS KEY 配置文件
# @end
# @copyright (C) 2015, kimech

# PLATFORM = "AA"   # [APPLE | ALLIANCE | ...]
# ==================================================================================
from torngas.settings_manager import settings

PLATFORM_CONFIG_KEY = "xtzj." + settings.CHANNEL + ".config"
PLATFORM_SERVER_KEY = "xtzj." + settings.CHANNEL + ".servers"
PLATFORM_PLATS_KEY = "xtzj." + settings.CHANNEL + ".plats"
PLATFORM_WHITE_SET_KEY = "xtzj." + settings.CHANNEL + ".whitelist"
YYB_ORDERED_SET = "xtzj." + settings.CHANNEL + ".S%s.yyb_ordered_set"

# 统计时使用的数据
STAT_LEVEL_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.level"
STAT_GUIDE_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.guide"
STAT_MISSION_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.mission"
STAT_ONLINE_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.online"   # sorted_list
STAT_TODAY_ACTIVE_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.active.%s"  # set
STAT_TODAY_REGIST_REDIS_KEY = "xtzj." + settings.CHANNEL + ".statictics.S%s.regist.%s"  # set

#
SEQUENCE_KEY = "xtzj." + settings.CHANNEL + ".sequence.S%s.repo"
ACCOUNT_EXPRESS_KEY = "xtzj." + settings.CHANNEL + ".account_express.sequence"

USER_REGISTERED_NAME = "xtzj." + settings.CHANNEL + ".user.registered_name"

NOTICE_BOX_KEY = "xtzj." + settings.CHANNEL + ".notices"
CHARGE_PAID_SET_KEY = "xtzj." + settings.CHANNEL + ".paid_uids"

BROADCAST_BOX_KEY = "xtzj." + settings.CHANNEL + ".broadcasts.S%s.class_%s"

ACT_KEY_PREFIX = "xtzj." + settings.CHANNEL + ".activity.S%s"                                     # 【活动】
ACT_PRIVATE_SALE_PREFIX = "xtzj." + settings.CHANNEL + ".activity.S%s.private_sale.%s"        # 【活动特卖会】全服限购购买记录 {1:0,2:0}
ACT_DIAMOND_GAMBLE_KEY = "xtzj." + settings.CHANNEL + ".activity.S%s.diamond_gamble.%s"       # 【钻石赌博】记录
ACT_PAYBACK_KEY = "xtzj." + settings.CHANNEL + ".activity.S%s.ios_payback"                # 4.13 sid=1 ios越狱测试充值返还元宝 && 511 sid=2 安卓封测充值测试返还元宝
# 测试活动奖励
UC_QIHOO_TEST_AWARD_4003_KEY = "xtzj." + settings.CHANNEL + ".activity.S%s.uc_qihoo_test_award_4003"
UC_QIHOO_TEST_AWARD_4004_KEY = "xtzj." + settings.CHANNEL + ".activity.S%s.uc_qihoo_test_award_4004"
UC_QIHOO_TEST_AWARD_4005_KEY = "xtzj." + settings.CHANNEL + ".activity.S%s.uc_qihoo_test_award_4005"

ARENA_ROBOTS_KEY = "xtzj." + settings.CHANNEL + ".arena.S%s.robots_lib"
ARENA_ADMIRE_KEY = "xtzj." + settings.CHANNEL + ".arena.S%s.admire_logs"
ARENA_RANK_SEQUENCE_KEY = "xtzj." + settings.CHANNEL + ".arena.S%s.rank_sequence"
ARENA_FIGHTLOG_BOX_KEY = "xtzj." + settings.CHANNEL + ".arena.S%s.fightlog"
ARENA_FIGHTLOG_POOL_KEY = "xtzj." + settings.CHANNEL + ".arena.S%s.fightlog.pool"

RANK_KEY_PREFIX = "xtzj." + settings.CHANNEL + ".rank.S%s.%s"
RANK_CACHE_KEY_PREFIX = "xtzj." + settings.CHANNEL + ".rank_cache.S%s.%s"

MAIL_REPERTORY_NEW_PREFIX = "xtzj." + settings.CHANNEL + ".mail.%s.new"
MAIL_REPERTORY_OLD_PREFIX = "xtzj." + settings.CHANNEL + ".mail.%s.old"

GROUP_CREATED_NAME = "xtzj." + settings.CHANNEL + ".group.created_name"
# hash => key: group_id values: {"id":1001, "name":"test", "exp":110, "level":3, "creater":"110000001", "master":"110000001", "join_request_sequence": 0,
#                                "member_number":1, "join_level_limit": 20, "join_state": 1, "notice": "come on.", "state": 1}
GROUP_MAIN_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.main.%s"
# hash => key: uid values: {"position": 1, "donate":100, "login": 1451462290, "uid": 110000001, "fight": 5540, "level": 10, "name": "Ame", "avatar": 10005}
GROUP_MEMBER_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.member.%s"
# list => [{"request_id": 1000023, "uid": "110000001", "name": "AME", "avatar": 100005, "level": 10, "fight": 5540, "state": 1}, ]
GROUP_REQUEST_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.request.%s"
# list => [{"uid": "110000001", "name": "AME", "data": 120, "action": 1, "time": 1451462290},]
GROUP_LOGS_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.log.%s"
GROUP_GAME_TIGER_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.game_tiger.%s"
GROUP_GAME_BIRD_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.game_bird.%s"

GROUP_TRAIN_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.train_times.%s"  # hash 公会训练所被动加速数
GROUP_TRAIN_HERO_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.train_hero_times.%s"  # hash 公会训练所被动加速数
GROUP_TRAIN_LOG_KEY = "xtzj." + settings.CHANNEL + ".group.S%s.train_log.%s"    # hash  公会训练所被加速日志

# redis存储数据结构: list
CHAT_WORLD_BOX_KEY = "xtzj." + settings.CHANNEL + ".chat.S%s.world"
# redis存储数据结构: hash set
CHAT_GROUP_BOX_KEY = "xtzj." + settings.CHANNEL + ".chat.S%s.group"
# redis存储数据结构: list
CHAT_NOTICE_BOX_KEY = "xtzj." + settings.CHANNEL + ".chat.S%s.notice"
# redis存储数据结构: hash set
CHAT_PRIVATE_BOX_KEY = "xtzj." + settings.CHANNEL + ".chat.S%s.private"
CHAT_PRIVATE_POOL_KEY = "xtzj." + settings.CHANNEL + ".chat.S%s.private.pool"
# 每个玩家都有这个公会资讯邮箱  玩家被同意加入公会和被踢出公会消息都放在这个邮箱中，玩家在请求服务器时，自己去操作自己的数据，之后清空邮箱
# list => [{"from_group_id": 10001, "action": 1, "time": 1451475957}] # action 1-同意加入 0-被踢出
# 20151230晚9点 检测玩家是否有工会的时候太tm麻烦了，暂时直接修改玩家公会数据，不要信箱功能
# player_group_box_key = "xtzj.%s.group_info_box.%s"

# {"id": 10001, "type": 1, "hp": 10000131, "days": 1, "update": "20160505"}
WORLD_BOSS_MAIN_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.main"                                # 世界boss主KEY hash
WORLD_BOSS_DMG_TOTAL_RANK_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.total_rank.v%s"            # 世界boss总伤害榜 sorted_set
WORLD_BOSS_DMG_DAILY_RANK_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.today_rank"                # 世界boss分期伤害榜 sorted_set
WORLD_BOSS_DMG_YES_RANK_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.yes_rank"                    # 世界boss分期昨日伤害榜 list
WORLD_BOSS_SUPPORT_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.support"                          # 世界boss支持队列hash
WORLD_BOSS_HEROS_KEY = "xtzj." + settings.CHANNEL + ".worldboss.S%s.heros"                              # 世界boss英雄圣殿 sorted_set
