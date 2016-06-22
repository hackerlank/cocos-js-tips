#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-25 13:16:46
# @Author : Jiank (http://jiankg.github.com)
# @doc
#    排行榜服务
# @end
# @copyright (C) 2015, kimech

import time

from libs.rklib.core import app

from apps.configs import game_config
from apps.configs import rediskey_config

from apps.services import act as act_service
from apps.services.mail import MailService

redis_client = app.get_storage_engine('redis').client.current

RANK_FIGHT = 1
RANK_GROUP = 2
RANK_HERO = 3
RANK_ARENA = 4
RANK_PEAK_ARENA = 5
RANK_MISSION_STAR = 6
RANK_TRIAL = 7
RANK_HERO_COUNT = 8
RANK_ARENA_FIGHT = 9

RANK_ACT_GOLD = 101
RANK_ACT_EXP = 102
RANK_ACT_FIRE = 103
RANK_ACT_ICE = 104
RANK_ACT_PHANTOM = 105

RANK_KEY_MAPPING = {1: "fight", 2: "group", 3: "hero", 4: "arena", 5: "peak_arena",
                    6: "mission_star", 7: "trial", 8: "hero_count", 9: "arena_fight",
                    101: "act_gold", 102: "act_exp", 103: "act_fire", 104: "act_ice",
                    105: "act_phantom"}

ACT_RANK_TYPE_MAPPING = {1:"act_gold", 2:"act_exp", 3:"act_fire", 4:"act_ice", 5:"act_phantom"}

# ==================== 主要排行数据【战力，副本星级，机甲，试炼】 ======================
def update_rank(sid, rank_type, id, score):
    """刷新榜单
    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[rank_type])
    redis_client.zadd(ranking_name, score, id)

def update_trial_rank(sid, uid, process):
    """更新试炼排行榜

    Args:
        uid :用户ID
        process :最大进度
    """
    # 取出老数据
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_TRIAL])
    old = redis_client.zscore(ranking_name, uid)
    if old or old < process:
        redis_client.zadd(ranking_name, process, uid)

# ==================== 活动副本排行数据【金币，经验，冰封，烈焰】 ======================
def update_act_mission_rank(sid, rank_type, uid, score):
    """
    更新【金币活动副本】的最新伤害排行数据
    更新【经验活动副本】的最新伤害排行数据
    更新【烈焰活动副本】的最新通关时间
    更新【冰封活动副本】的最新通关时间

    Args:
        uid :玩家UID
        score :玩家伤害值

    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, ACT_RANK_TYPE_MAPPING[rank_type])
    if rank_type in [1, 2]:
        redis_client.zincrby(ranking_name, uid, score)
    else:
        # ============================================
        # 千万要注意参数顺序啊，妈蛋，巨坑啊！！！！！
        redis_client.zadd(ranking_name, score, uid)
        # ============================================

def rank(sid, rank_type, tag):
    """获取用户在战力，获得星星，机甲排行榜中的排名

    Args:
        ranking_name: 排行榜名称
        tag: 查询排行标记

    Returns:
        user_rank: 用户在排行榜中的排名
    """
    if not tag:
        return {}

    # ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[rank_type])

    # if rank_type != RANK_ARENA:
    #     user_rank = redis_client.zrevrank(ranking_name, tag)
    # else:
    #     try:
    #         user_rank = int(redis_client.zscore(ranking_name, tag)) - 1
    #     except:
    #         user_rank = -1

    # # 为了避免自己的排名和下面榜中的差异，50名之内的还是以cache中的榜单排名为准
    # if isinstance(user_rank, int) and 0 <= user_rank < 50:

    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, RANK_KEY_MAPPING[rank_type])
    rank_list = redis_client.lrange(cache_rank_name, 0, -1)
    if rank_type == RANK_GROUP:
        # 帮派
        for rank_member in rank_list:
            rank_member = eval(rank_member)
            if rank_member["group_id"] == tag:
                return rank_member

    elif rank_type == RANK_HERO:
        # 机甲
        for rank_member in rank_list:
            rank_member = eval(rank_member)
            if "%s_%s" % (rank_member["uid"], rank_member["hid"]) == str(tag):
                return rank_member

    else:
        for rank_member in rank_list:
            rank_member = eval(rank_member)
            if rank_member["uid"] == tag:
                return rank_member

    return {}

def trial_rank(sid, uid):
    """获取试炼排名

    Args:

    Returns:

    """
    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, "trial")
    rank_list = redis_client.lrange(cache_rank_name, 0, -1)
    for rank_member in rank_list:
        rank_member = eval(rank_member)
        if rank_member["uid"] == uid:
            return rank_member["rank"]

    try:
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, "trial")
        rank = int(redis_client.zrevrank(ranking_name, uid)) + 1
    except:
        rank = 0

    return rank

def grouprank(sid, group_id):
    """获取公会排名

    Args:

    Returns:

    """
    try:
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_GROUP])
        rank = int(redis_client.zrevrank(ranking_name, group_id)) + 1
    except:
        rank = 0

    return rank

    # cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_GROUP])
    # rank_list = redis_client.lrange(cache_rank_name, 0, -1)

    # for rank_member in rank_list:
    #     rank_member = eval(rank_member)
    #     if int(rank_member["group_id"]) == group_id:
    #         return rank_member["rank"]

    # return 0

def top(sid, rank_type, start=1, stop=50):
    """获取排行榜区间数据(存储在缓存中)

    Args:
        rank_type: 排行榜类型
        start: 从第几名
        stop: 到第几名

    Returns:
        TOP N 排行列表:
            eg: [{'uid': '10001', 'name': 'jack', 'rank': 1, 'score': 11.0},
                 {'uid': '10002', 'name': 'tom', 'rank': 2, 'score': 10.0}]
    """
    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, RANK_KEY_MAPPING[rank_type])
    # 最多只能取前50名
    rank_list = redis_client.lrange(cache_rank_name, start-1, stop-1)

    return [eval(rank) for rank in rank_list]

def get_trial_fighters(sid, min_fight, max_fight):
    """终极试炼挑选对手

    1.根据玩家最强战力匹配战力排行榜中对应的对手
    2.若1条件没有挑选到合适的对手，则取排行榜按规则挑选对手

    Args:
        uid: 玩家自身的UID 要排除
        min_fight: 战力起始位置
        max_fight: 战力结束位置

    Returns:
        ["20000002"]
    """
    rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_ARENA_FIGHT])
    rank_list = redis_client.zrangebyscore(rank_name, min_fight, max_fight)

    return rank_list

def trial_rank_send_mail_awards(sid):
    """每日凌晨五点结算终极试炼排行榜，给玩家发送排行奖励
    """
    all_players = get_all_players(sid)

    rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_TRIAL])
    ranking_list = redis_client.zrevrange(rank_name, 0, -1, withscores=True)

    if not ranking_list:
        return

    user_ranking = []
    from apps.models.user import User
    for key, value in enumerate(ranking_list):
        rank_data = {'uid': value[0], 'score': int(value[1])}
        user = User.get(rank_data['uid'])
        if user:
            rank_data['score1'] = user.trial.daily_scores
        else:
            rank_data['score1'] = 0

        user_ranking.append(rank_data)

    def tsorted(x,y):
        if x["score"] == y["score"]:
           return y["score1"] - x["score1"]
        else:
           return y["score"] - x["score"]

    user_ranking = sorted(user_ranking, cmp=tsorted)

    a = 1
    for x in user_ranking:
        x['rank'] = a
        a += 1

    user_ranking1 = {}
    for i in user_ranking:
        user_ranking1[str(i['uid'])] = i['rank']

    for uid in all_players:
        user = User.get(uid)
        if not user or user.game_info.role_level <= game_config.user_func_cfg.get(4020, 999):
            continue

        player_rank = user_ranking1.get(uid, 0)
        if player_rank < 0:
            continue

        try:
            award_index = min([rank for rank in game_config.trial_mail_award_cfg if rank >= player_rank])
        except:
            award_index = -1

        if award_index < 0:
            continue

        cfg = game_config.trial_mail_award_cfg.get(award_index)
        MailService.send_game(uid, 1003, [player_rank], cfg["awards"])

        print "trial_rank_awards: receiver: %s, rank: %s, awards: %s" % (uid, player_rank, cfg["awards"])

    trial_delete_daily_rank(sid)

def trial_delete_daily_rank(sid):
    """每日五点 等脚本发完排行奖励的时候 清除排行榜数据
    """
    rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_TRIAL])
    redis_client.delete(rank_name)

    print "[Clean Trial Rank Success]: %s " % rank_name

def fight_rank_send_mail_awards(sid, act_id):
    """到活动结束时间点发送排行奖励

    Args:
        sid  服务器ID
        act_id  活动ID
    """
    indexes = game_config.act_sample_detail_cfg.get(act_id, [])
    max_cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, max(indexes)))

    rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_FIGHT])
    top = redis_client.zrevrange(rank_name, 0, max_cfg["cond_a"]-1, withscores=True)

    for index, player in enumerate(top):
        fight_rank = index + 1
        try:
            award_index = min([rank for rank in indexes if rank >= fight_rank])
        except:
            award_index = 0

        if not award_index:
            continue

        cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, award_index))
        # 排名前10 且 战力达到指定值才有奖励
        if player[1] >= cfg["cond_b"]:
            MailService.send_game(player[0], 1001, [fight_rank], cfg["awards"])
            print "[act:%s] fight_rank_send_mail_awards: receiver: %s, rank: %s, fight: %s, awards: %s" % (act_id, player[0], fight_rank, player[1], cfg["awards"])

def fight_send_mail_awards(sid, act_id):
    """到活动结束时间点发送战力达标奖励

    Args:
        sid  服务器ID
        act_id  活动ID
    """
    indexes = game_config.act_sample_detail_cfg.get(act_id, [])
    min_cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, max(indexes)))

    rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[RANK_FIGHT])
    max_score = 9999999
    targets = redis_client.zrangebyscore(rank_name, min_cfg["cond_a"], max_score, withscores=True)

    for index, player in enumerate(targets):
        try:
            def is_reached(level):
                cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, level), {})
                if not cfg:
                    return False
                else:
                    return player[1] >= cfg["cond_a"]

            fight_level = min(filter(is_reached, indexes))
        except:
            fight_level = 0

        if not fight_level:
            continue

        cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, fight_level))
        MailService.send_game(player[0], 1002, [player[1]], cfg["awards"])
        print "[act:%s] fight_send_mail_awards: receiver: %s, fight_level: %s, fight: %s, awards: %s" % (act_id, player[0], fight_level, player[1], cfg["awards"])

def get_all_players(sid):
    """获取全服所有玩家的UID
    """
    return redis_client.zrange(rediskey_config.RANK_KEY_PREFIX % (sid, RANK_KEY_MAPPING[1]), 0, -1)
