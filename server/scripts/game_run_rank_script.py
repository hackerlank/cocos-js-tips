#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-09 20:47:03
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   定时排行脚本
# @end
# @copyright (C) 2015, kimech

import os
import sys
import time
import datetime
import traceback
import cPickle as pickle

if len(sys.argv) == 3:
    ENV = sys.argv[1]
    PLAT = sys.argv[2]
    ENV = ENV.upper()
else:
    print "useage: python game_run_rank_script.py [local|dev|prod] [ios|android|apple]\n"
    sys.exit()

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BASE_DIR + '/apps')

import settings
os.environ.setdefault('KIMECH_APP_SETTINGS', 'settings.%s' % ENV.lower())

from libs.rklib.core import app
app.init(plat = PLAT.lower(),
         storage_cfg_file = BASE_DIR + "/apps/configs/app_config/storage.conf",
         logic_cfg_file = BASE_DIR + "/apps/configs/app_config/logic.conf",
         model_cfg_file = BASE_DIR + "/apps/configs/app_config/model.conf")

from apps.models.user import User
from apps.services.group import GroupService
from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

# rank_cache_update_info = "xtzj.caches.S%s.rank.info"  # 排行榜更新数据,记录排行榜上次更新时间戳等等.{}
RANK_UPDATE_INTERVIAL = {"fight": 1, "hero": 1, "mission_star": 1, "arena": 1, "hero_count": 1, "trial": 1, "group": 1,
                         "act_gold": 1, "act_exp": 1, "act_fire": 1, "act_ice": 1, "act_phantom": 1}

def _fetch_group_name_by_id(sid, group_id):
    """
    """
    group_data = GroupService.find(sid, group_id)

    return group_data["name"] if group_data else ''

def _run_update_cached_rank(sid, tag):
    """更新缓存里的战力排行榜
    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, tag)
    ranking_list = redis_client.zrevrange(ranking_name, 0, 50, withscores=True)

    user_ranking = []

    if ranking_list:
        for key, value in enumerate(ranking_list):
            rank_data = {}
            rank_data['rank'] = 0
            # 机甲排行榜需要“机甲ID”这个特殊处理下
            if tag == "hero":
                info = value[0].split("_")
                rank_data['score'] = value[1]
                rank_data['uid'] = info[0]
                rank_data['hid'] = int(info[1])
                user = User.get(rank_data['uid'])
                if isinstance(user, User):
                    rank_data['name'] = user.name
                    rank_data['group_name'] = _fetch_group_name_by_id(user.sid, user.group.group_id)
                    rank_data['level'] = user.hero.heros.get(int(info[1]))["level"]
                    rank_data['quality'] = user.hero.heros.get(int(info[1]))["quality"]
                    rank_data['star'] = user.hero.heros.get(int(info[1]))["star"]

            else:
                rank_data['uid'] = value[0]
                rank_data['score'] = int(value[1])
                user = User.get(rank_data['uid'])
                if isinstance(user, User):
                    rank_data['name'] = user.name
                    rank_data['level'] = user.game_info.role_level
                    rank_data['avatar'] = user.avatar
                    if tag == "trial":
                        rank_data['score1'] = user.trial.daily_scores
                    else:
                        rank_data['group_name'] = _fetch_group_name_by_id(user.sid, user.group.group_id)

            user_ranking.append(rank_data)

    # 终极试炼排序潜规则：若层数相同 则按积分排序
    if tag == "trial":
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

    # 放入排行缓存列表中
    user_ranking.reverse()

    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, tag)
    while redis_client.llen(cache_rank_name) != 0:
        redis_client.delete(cache_rank_name)
        time.sleep(1)

    for rank in user_ranking:
        redis_client.lpush(cache_rank_name, rank)

    print 'total number: ', redis_client.llen(cache_rank_name)
    print 'ranking_name:', ranking_name
    print 'ranking_list:', ranking_list

    if tag == "hero":
        print 'user_ranking:', [(r["uid"], r["hid"], r["rank"], r["score"])for r in user_ranking[::-1]]
    else:
        print 'user_ranking:', [(r["uid"], r["rank"], r["score"])for r in user_ranking[::-1]]

    print '=' * 60

def _run_update_cached_arena_rank(sid, tag):
    """更新竞技场排行榜
    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, tag)
    ranking_list = redis_client.zrangebyscore(ranking_name, 0, 50, withscores=True, score_cast_func=int)

    user_ranking = []

    if ranking_list:
        for key, value in enumerate(ranking_list):
            rank_data = {}
            rank_data['rank'] = 0
            rank_data['uid'] = value[0]
            if rank_data['uid'].startswith("robot_"):
                robot_data = redis_client.hget(rediskey_config.ARENA_ROBOTS_KEY % sid, rank_data['uid'])
                robot_data = eval(robot_data)
                rank_data["name"] = robot_data["name"]
            else:
                rank_data['score'] = value[1]
                user = User.get(rank_data['uid'])
                if isinstance(user, User):
                    rank_data['name'] = user.name
                    rank_data['level'] = user.game_info.role_level
                    rank_data['avatar'] = user.avatar
                    rank_data['group_name'] = _fetch_group_name_by_id(user.sid, user.group.group_id)
                    rank_data['fight'] = sum([user.hero.get_by_hero_id(hero_id)["fight"] for hero_id in user.array.arena if hero_id])

            user_ranking.append(rank_data)

        a = 1
        for x in user_ranking:
            x['rank'] = a
            a += 1

    # 放入排行缓存列表中
    user_ranking.reverse()

    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, tag)
    while redis_client.llen(cache_rank_name) != 0:
        redis_client.delete(cache_rank_name)
        time.sleep(1)

    for rank in user_ranking:
        redis_client.lpush(cache_rank_name, rank)

    print 'ranking_name:', ranking_name
    print 'ranking_list:', ranking_list
    print 'user_ranking:', [(r["uid"], r["rank"])for r in user_ranking[::-1]]
    print '=' * 60

def _run_update_cached_group_rank(sid, tag):
    """更新公会排行榜

    抓取所有公会数据 - 按等级排 - 按总战力排 - 存放进cache里

    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, tag)
    ranking_list = redis_client.zrevrange(ranking_name, 0, -1, withscores=True)

    group_rank = []

    if ranking_list:
        for key, value in enumerate(ranking_list):
            rank_data = {}
            rank_data['rank'] = 0
            rank_data['group_id'] = int(value[0])
            rank_data['exp'] = int(value[1])

            group_data = GroupService.find(sid, value[0])
            if group_data:
                rank_data['name'] = group_data["name"]
                rank_data['icon'] = group_data["icon"]
                rank_data['level'] = group_data["level"]
                master = User.get(group_data["master"])
                rank_data['master'] = master.name if isinstance(master, User) else "会长"
                rank_data['member_number'] = group_data["member_number"]
                rank_data['join_level_limit'] = group_data["join_level_limit"]
                rank_data['join_state'] = group_data["join_state"]
                rank_data['notice'] = group_data["notice"]

                fight = 0
                for uid in [member["uid"] for member in GroupService.members(sid, int(value[0])) if isinstance(member, dict)]:
                    try:
                        user = User.get(uid)
                        fight += user.game_info.fight
                    except:
                        fight += 0

                rank_data['fight'] = fight

            group_rank.append(rank_data)

    def gsorted(x,y):
        if x["level"] == y["level"]:
           return y["fight"] - x["fight"]
        else:
           return y["level"] - x["level"]

    group_rank = sorted(group_rank, cmp=gsorted)

    a = 1
    for x in group_rank:
        x['rank'] = a
        a += 1
    # 放入排行缓存列表中
    group_rank.reverse()

    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, tag)
    while redis_client.llen(cache_rank_name) != 0:
        redis_client.delete(cache_rank_name)
        time.sleep(1)

    # 放入排行缓存列表中
    for rank in group_rank:
        redis_client.lpush(cache_rank_name, rank)

    print 'ranking_name:', cache_rank_name
    print 'ranking_list:', group_rank
    print '=' * 60

def _run_update_cached_act_mission_rank(sid, tag):
    """更新缓存里的活动【冰封，烈焰，幻想】排行榜数据

    按照参加的时间先后
    """
    ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, tag)
    ranking_list = redis_client.zrevrange(ranking_name, -50, -1, withscores=True)

    user_ranking = []

    if ranking_list:
        for key, value in enumerate(ranking_list):
            rank_data = {}
            rank_data['rank'] = 0
            rank_data['uid'] = value[0]
            rank_data['score'] = int(value[1])
            user = User.get(rank_data['uid'])
            if isinstance(user, User):
                rank_data['name'] = user.name
                rank_data['level'] = user.game_info.role_level
                rank_data['avatar'] = user.avatar
                rank_data['group_name'] = _fetch_group_name_by_id(user.sid, user.group.group_id)

            user_ranking.append(rank_data)

    a = 50
    for x in user_ranking:
        x['rank'] = a
        a -= 1

    cache_rank_name = rediskey_config.RANK_CACHE_KEY_PREFIX % (sid, tag)
    while redis_client.llen(cache_rank_name) != 0:
        redis_client.delete(cache_rank_name)
        time.sleep(1)

    for rank in user_ranking:
        redis_client.lpush(cache_rank_name, rank)

    print 'total number: ', redis_client.llen(cache_rank_name)
    print 'ranking_name:', ranking_name
    print 'ranking_list:', ranking_list

    print 'user_ranking:', [(r["uid"], r["rank"], r["score"])for r in user_ranking[::-1]]
    print '=' * 60

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def main():
    now = int(time.time())
    print '*' * 70
    print 'updated_at:', str(datetime.datetime.fromtimestamp(now))
    print '*' * 70

    servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
    for sid in servers:
        for rank in RANK_UPDATE_INTERVIAL.keys():
            # 取每个榜单上次更新时间, 根据每个时间间隔有差异的更新每个榜单。
            # 有的榜单一天刷新一次，有的榜单1小时会刷新一次。
            # rank_info = redis_client.hget(rank_cache_update_info % sid, rank)
            # rank_info = eval(rank_info) if rank_info else {"last_update_timestamp": 0}

            # if now - rank_info["last_update_timestamp"] >= RANK_UPDATE_INTERVIAL[rank] * 3600:
            if rank == "group":
                _run_update_cached_group_rank(sid, rank)
            elif rank == "arena":
                _run_update_cached_arena_rank(sid, rank)
            elif rank in ["act_fire", "act_ice", "act_phantom"]:
                _run_update_cached_act_mission_rank(sid, rank)
            else:
                _run_update_cached_rank(sid, rank)

            # rank_info["last_update_timestamp"] = now
            # rank_info = redis_client.hset(rank_cache_update_info % sid, rank, rank_info)

            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except:
        print 'error_at:', str(datetime.datetime.now())
        traceback.print_exc(file=sys.stdout)
        print '#' * 80
