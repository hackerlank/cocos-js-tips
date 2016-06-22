#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 10:32:37
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     世界boss
# @end
# @copyright (C) 2015, kimech

import time
import copy
import datetime

import cPickle as pickle

from libs.rklib.core import app

from apps.models.user import User
from apps.configs import game_config
from apps.configs import rediskey_config
from apps.services.mail import MailService
from apps.services.group import GroupService

from apps.logics.helpers import common_helper

redis_client = app.get_storage_engine('redis').client.current

WORLD_BOSS_MONSTER_ID = 229100
WORLD_BOSS_MONSTER_HP = 229100 * 10

WORLD_BOSS_TYPE_NPC = 1
WORLD_BOSS_TYPE_PLAYER = 2

WORLD_BOSS_RANK_TODAY = 1
WORLD_BOSS_RANK_TOTAL = 2
WORLD_BOSS_RANK_HEROS = 3
WORLD_BOSS_RANK_YES = 4

WORLD_BOSS_HP_MAX = 1000000000
WORLD_BOSS_HP_MIN = 10000000

WORLD_BOSS_CYCLE = 5
WORLD_BOSS_DEFAULT_LEVEL = 25

WORLD_BOSS_SUPPORT_EXTRA_AWARD = {1: 100000}
class BossService(object):
    """世界boss服务
    """
    def __init__(self):
        super(BossService, self).__init__()

    @classmethod
    def get(cls, sid):
        """获取boss数据
        """
        key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid
        data = redis_client.hgetall(key)

        if not data:
            cls.initial(sid)
            data = redis_client.hgetall(key)
        elif common_helper.time_to_refresh(data["update"], 21):
            cls.update_at_21(sid)
            data = redis_client.hgetall(key)
        else:
            pass

        data["name"] = pickle.loads(data["name"])
        data["left_hp"] = int(data["hp"]) - int(data["lose_hp"])

        # 整型字段
        for key,value in data.items():
            if key not in ["uid","name","update","ender"]:
                data[key] = int(value)

        return data

    @classmethod
    def initial(cls, sid):
        """初始化boss数据
        """
        key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid

        main_data = {
                "id": WORLD_BOSS_MONSTER_ID,
                "type": WORLD_BOSS_TYPE_NPC,
                "hp": WORLD_BOSS_MONSTER_HP,
                "lose_hp": 0,
                "days": 1,
                "update": time.strftime('%Y%m%d%H'),
                "name": pickle.dumps(""),
                "uid": "",
                "version": 1,
                "level": WORLD_BOSS_DEFAULT_LEVEL,
                "ender": "",
            }

        redis_client.hmset(key, main_data)

    @classmethod
    def update_at_21(cls, sid):
        """boss战开始，清除今日榜单，生成旧榜单 供玩家查看支持记录
        """
        redis_client.delete(rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid)
        redis_client.hset(rediskey_config.WORLD_BOSS_MAIN_KEY % sid, "update", time.strftime('%Y%m%d%H'))

    @classmethod
    def settle_after_boss_fight(cls, sid):
        """9:20检查并结算boss数据
        """
        key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid
        if not redis_client.exists(key):
            cls.initial(sid)
        else:
            cls.award_today_rank_players(sid)       # 发今日伤害榜奖励

            old_data = cls.get(sid)
            # 英雄圣殿对应数据更新
            if old_data["uid"]:
                redis_client.zincrby(rediskey_config.WORLD_BOSS_HEROS_KEY % sid, old_data["uid"], 1)

            # boss被打死，版本增加，boss名称改变，清除总榜，今日榜-》昨日榜，boss血量更新
            if old_data["left_hp"] <= 0 or old_data["days"] >= WORLD_BOSS_CYCLE:
                total_rank_key = rediskey_config.WORLD_BOSS_DMG_TOTAL_RANK_KEY % (sid, old_data["version"]) # 获取这个boss总榜的第一名玩家
                uids = redis_client.zrange(total_rank_key,0,1)
                new_boss = {"name": pickle.dumps(""), "uid": "", "level": WORLD_BOSS_DEFAULT_LEVEL}
                if uids:
                    user = User.get(uids[0])
                    if isinstance(user, User):
                        group_name = GroupService.get_name_by_id(user.sid, user.group.group_id)
                        new_boss["name"], new_boss["uid"], new_boss["level"] = pickle.dumps("%s（%s）" % (user.name, group_name)), uids[0], user.game_info.role_level

                boss_new_hp = max(min(old_data["lose_hp"] * 1.15 * (1 + 0.2 * (3 - (old_data["days"] + 1))), WORLD_BOSS_HP_MAX), WORLD_BOSS_HP_MIN)
                main_data = {
                    "id": WORLD_BOSS_MONSTER_ID,
                    "type": WORLD_BOSS_TYPE_NPC if not old_data["version"] else WORLD_BOSS_TYPE_PLAYER,
                    "hp": int(boss_new_hp),
                    "days": 1,
                    "update": time.strftime('%Y%m%d%H'),
                    "version": old_data["version"] + 1,
                    "ender": "",
                    "lose_hp": 0,
                }

                main_data.update(new_boss)
                redis_client.hmset(key, main_data)          # 更新boss数据
                cls.award_total_rank_players(sid, old_data["version"])          # 发总榜奖励
                cls.award_boss_ender(sid, old_data["ender"])        # 发boss终结者
            else:
                redis_client.hincrby(key, "days", 1)

            # 生成旧榜单
            cls.build_yesterday_rank(sid)

            print "BOSS STATUS:"
            print cls.get(sid)

    @staticmethod
    def award_today_rank_players(sid):
        """给今日伤害榜玩家发奖
        """
        key = rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid
        ranking_list = redis_client.zrevrange(key, 0, -1, withscores=True)
        if not ranking_list:
            return

        for index, value in enumerate(ranking_list):
            award_cfg = common_helper.get_award_by_data(game_config.boss_daily_award_cfg, index+1)
            if award_cfg:
                MailService.send_game(value[0], 3009, [index+1], award_cfg["awards"])
                print "[boss] award_today_rank_players: receiver: %s, dmg: %s, awards: %s" % (value[0], index+1, award_cfg["awards"])

        # 支持了今日第一名的玩家额外获得金币
        support_key = rediskey_config.WORLD_BOSS_SUPPORT_KEY % sid
        try:
            number_one = ranking_list[0][0]
        except:
            number_one = None

        if isinstance(number_one, str):
            supports = redis_client.hget(support_key, number_one)
            l = [] if not supports else pickle.loads(supports)
            for uid in l:
                MailService.send_game(uid, 3010, [number_one], WORLD_BOSS_SUPPORT_EXTRA_AWARD)
                print "[boss] award_today_support_awards: receiver: %s, number_one: %s, awards: %s" % (uid, number_one, WORLD_BOSS_SUPPORT_EXTRA_AWARD)

    @staticmethod
    def award_total_rank_players(sid, version):
        """给击杀该版本BOSS伤害总榜玩家发奖
        """
        key = rediskey_config.WORLD_BOSS_DMG_TOTAL_RANK_KEY % (sid,version)
        ranking_list = redis_client.zrevrange(key, 0, -1, withscores=True)
        if not ranking_list:
            return

        for index, value in enumerate(ranking_list):
            award_cfg = common_helper.get_award_by_data(game_config.boss_total_award_cfg, index+1)
            if award_cfg:
                awards = copy.deepcopy(award_cfg["awards"])
                for k,v in awards.items():
                    awards[k] = v * 2

                MailService.send_game(value[0], 3010, [index+1], awards)

                print "[boss] award_total_rank_players: receiver: %s, dmg: %s, awards: %s" % (value[0], index+1, awards)

    @staticmethod
    def award_boss_ender(sid, uid):
        """给该版本BOSS最后一击的玩家发奖
        """
        if not uid:
            return

        award_cfg = common_helper.get_award_by_data(game_config.boss_total_award_cfg, 1)
        MailService.send_game(uid, 3011, [], award_cfg["awards"])
        print "[boss] award_boss_ender: receiver: %s, awards: %s" % (uid, award_cfg["awards"])

    @classmethod
    def myrank(cls, rtype, sid, uid):
        """读取排行榜数据
        """
        if rtype == WORLD_BOSS_RANK_TODAY:
            key = rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid
        else:
            data = cls.get(sid)
            key = rediskey_config.WORLD_BOSS_DMG_TOTAL_RANK_KEY % (sid, data["version"])

        result = redis_client.zrevrank(key, uid)
        if isinstance(result, int):
            return result + 1, int(redis_client.zscore(key, uid))
        else:
            return 0, 0

    @classmethod
    def alive(cls, sid):
        """判断boss是否活着
        """
        key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid
        return int(redis_client.hget(key, "hp")) > int(redis_client.hget(key, "lose_hp"))

    @classmethod
    def rank(cls, rtype, sid, start, end):
        """读取排行榜数据

        rtype:
            1 - 今日排名
            2 - 总排名
            3 - 英雄圣殿
            4 - 昨日榜单
        """
        if rtype == WORLD_BOSS_RANK_YES:
            cache_rank_name = rediskey_config.WORLD_BOSS_DMG_YES_RANK_KEY % sid
            return redis_client.lrange(cache_rank_name, start-1, end-1)

        if rtype == WORLD_BOSS_RANK_TODAY:
            key = rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid
        elif rtype == WORLD_BOSS_RANK_TOTAL:
            key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid
            version = redis_client.hget(key, "version")
            key = rediskey_config.WORLD_BOSS_DMG_TOTAL_RANK_KEY % (sid, version)
        else:
            key = rediskey_config.WORLD_BOSS_HEROS_KEY % sid

        ranking_list = redis_client.zrevrange(key, start-1, end-1, withscores=True)
        ranks = []
        for index,i in enumerate(ranking_list):
            rank_data = {}
            rank_data['rank'] = start + index + 1
            rank_data['data'] = int(i[1])
            user = User.get(i[0])
            if isinstance(user, User):
                rank_data['name'] = user.name
                rank_data['level'] = user.game_info.role_level
                rank_data['group_name'] = GroupService.find(user.sid, user.group.group_id)

            ranks.append(rank_data)

        return ranks

    @classmethod
    def support(cls, sid, uid, myid):
        """支持玩家
        """
        try:
            key = rediskey_config.WORLD_BOSS_SUPPORT_KEY % sid
            l = redis_client.hget(key, uid)
            l1 = pickle.loads(l) if l else []
            l1.append(myid)
            redis_client.hset(key, uid, pickle.dumps(l1))

            return True
        except Exception,e:
            return False

    @classmethod
    def fight(cls, sid, uid, dmg):
        """战斗结算
        """
        key = rediskey_config.WORLD_BOSS_MAIN_KEY % sid
        old_info = cls.get(sid)
        new_lose_hp = int(redis_client.hincrby(key, "lose_hp", dmg))
        if old_info["left_hp"] > 0 and new_lose_hp >= old_info["hp"]:
            redis_client.hset(key, "ender", uid)

        total_rank_key = rediskey_config.WORLD_BOSS_DMG_TOTAL_RANK_KEY % (sid, old_info["version"])
        if old_info["lose_hp"] == 0:
            redis_client.delete(total_rank_key)  # 前一天的boss被击杀，清除总榜

        redis_client.zincrby(total_rank_key, uid, dmg)  # 更新总伤害榜
        today_rank_key = rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid
        redis_client.zincrby(today_rank_key, uid, dmg)  # 更新今日伤害榜

    @classmethod
    def login_notice(cls, sid, uid):
        """在位时间前五英雄舰长每次上线进行全服务器公告
        """
        rank_key = rediskey_config.WORLD_BOSS_HEROS_KEY % sid
        result = redis_client.zrevrank(rank_key, uid)

        if isinstance(result, int):
            return rank + 1
        else:
            return 0

    @staticmethod
    def build_yesterday_rank(sid):
        """
        """
        rank_key = rediskey_config.WORLD_BOSS_DMG_DAILY_RANK_KEY % sid
        ranking_list = redis_client.zrevrange(rank_key, 0, 10, withscores=True)
        if not ranking_list:
            return

        user_ranking = []
        for key, value in enumerate(ranking_list):
            rank_data = {}
            rank_data['uid'] = value[0]
            rank_data['score'] = int(value[1])
            user = User.get(rank_data['uid'])
            if isinstance(user, User):
                rank_data['name'] = user.name
                rank_data['level'] = user.game_info.role_level
                rank_data['avatar'] = user.avatar

            user_ranking.append(rank_data)

        a = 1
        for x in user_ranking:
            x['rank'] = a
            a += 1

        cache_rank_name = rediskey_config.WORLD_BOSS_DMG_YES_RANK_KEY % sid
        while redis_client.llen(cache_rank_name) != 0:
            redis_client.delete(cache_rank_name)
            time.sleep(1)

        for rank in user_ranking:
            redis_client.lpush(cache_rank_name, rank)
