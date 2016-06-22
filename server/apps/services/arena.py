#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-15 11:25:34
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     竞技场服务
# @end
# @copyright (C) 2015, kimech

import math
import time
import random
import logging

import cPickle as pickle
from libs.rklib.core import app

from apps.configs import game_config
from apps.configs import static_const
from apps.configs import rediskey_config

from apps.logics.helpers import user_helper
from apps.services.group import GroupService
from apps.services.mail import MailService
from apps.services.sequence import Sequence
from apps.services import name as name_service

redis_client = app.get_storage_engine('redis').client.current

ARENA_ROBOTS_NUM = 20000
MATCH_RULES = [0.6, 0.8, 1, 1.125, 0.95]

class ArenaService(object):
    """竞技场服务
    """
    def __init__(self):
        super(ArenaService, self).__init__()

    @staticmethod
    def crontab_send_award_mail(sid):
        """每日晚九点，结算竞技场排行榜，发奖励
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        top = redis_client.zrangebyscore(key, 0, ARENA_ROBOTS_NUM)

        for index, fighter in enumerate(top):
            # 机器人不发奖励
            if fighter.startswith("robot_"):
                continue

            fighter_rank = index + 1
            try:
                award_index = min([rank for rank in game_config.arena_mail_award_cfg if rank >= fighter_rank])
            except:
                award_index = 0

            if not award_index:
                continue

            cfg = game_config.arena_mail_award_cfg.get(award_index)
            MailService.send_game(fighter, 1000, [fighter_rank], cfg["awards"])

            print "crontab_send_award_mail: receiver: %s, rank: %s, awards: %s" % (fighter, fighter_rank, cfg["awards"])

    @staticmethod
    def crontab_act_send_award_mail(sid, act_id):
        """每日晚上九点，运维活动中有给玩家发送奖励的活动
        """
        # 检查活动是否还在有效时间内
        from apps.services import act as act_service
        act_info = act_service.get_act_info(sid, act_id)

        now = int(time.time())

        if not act_info:
            return

        # 计算是否在有效范围内
        if now >= act_info["end"] or now < act_info["start"]:
            return

        indexes = game_config.act_sample_detail_cfg.get(act_id, [])
        max_cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, max(indexes)))

        # 最低名次，即取N多名竞技场玩家
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        top = redis_client.zrangebyscore(key, 0, max_cfg["cond_a"])

        for index, fighter in enumerate(top):
            # 机器人不发奖励
            if fighter.startswith("robot_"):
                continue

            fighter_rank = index + 1
            try:
                award_index = min([rank for rank in indexes if game_config.act_detail_cfg.get("%s-%s" % (act_id, rank))["cond_a"] >= fighter_rank])
            except:
                award_index = 0

            if not award_index:
                continue

            cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, award_index))
            MailService.send_game(fighter, 3000, [fighter_rank], cfg["awards"])

            print "[act:%s] crontab_send_award_mail: receiver: %s, rank: %s, awards: %s" % (act_id, fighter, fighter_rank, cfg["awards"])

    @staticmethod
    def import_robots(sid):
        """导入竞技场机器人

        ***********************************
        *  此功能慎用，会覆盖竞技场的所有数据  *
        ***********************************

        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        member_num = redis_client.zcard(key)
        if member_num != 0:
            print "*" * 80
            print "*       The arena rank is not empty, please handle this by server admin.       *"
            print "*" * 80
        else:
            try:
                robot_id_prfix = "robot_"
                for index in xrange(1, ARENA_ROBOTS_NUM+1):
                    ArenaService.import_robots1(sid, index)

                # 加上一个最特殊的竞技场机器人 让大家平稳度过竞技场引导
                special_index = 99999
                ArenaService.import_robots1(sid, special_index)

                print "*" * 80
                print "Arena import robots successful."
                print "*" * 80
            except Exception, e:
                print "*" * 80
                print "Arena import robots failed."
                print "*" * 80

    @staticmethod
    def import_robots1(sid, index):
        """导入单个竞技场机器人
        """
        robot_id_prfix = "robot_"
        robot_id = robot_id_prfix + str(index)
        robot_data = {"uid": robot_id, "name": game_config.robot_name_cfg.get(index)}
        redis_client.hset(rediskey_config.ARENA_ROBOTS_KEY % sid, robot_id, robot_data)
        redis_client.zadd(rediskey_config.RANK_KEY_PREFIX % (sid, "arena"), index, robot_id)

    @staticmethod
    def enter(sid, uid):
        """真实玩家开放竞技场功能，进入竞技场排名

        Args:
            uid 玩家ID

        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        if not redis_client.zscore(key, uid):
            rank = ARENA_ROBOTS_NUM + redis_client.incr(rediskey_config.ARENA_RANK_SEQUENCE_KEY % sid)
            redis_client.zadd(key, rank, uid)

    @staticmethod
    def admire(sid, fighter_id):
        """膜拜前10玩家

        Args:
            fighter_id 膜拜对象的UID

        """
        redis_client.hincrby(rediskey_config.ARENA_ADMIRE_KEY % sid, fighter_id, 1)

    @staticmethod
    def get_fighter_admired(sid, fighter_id):
        """膜拜前10玩家

        Args:
            fighter_id 膜拜对象的UID

        """
        times = redis_client.hget(rediskey_config.ARENA_ADMIRE_KEY % sid, fighter_id)
        if not times:
            times = 0

        return int(times)

    @staticmethod
    def get_user_rank(sid, uid):
        """查询玩家竞技场排名

        排名等于索引+1

        Args:
            uid 玩家ID
        Returns:
            rank 名次 int
        """
        rank = redis_client.zscore(rediskey_config.RANK_KEY_PREFIX % (sid, "arena"), uid)
        return int(rank) if rank else 0

    @classmethod
    def get_fighter_by_rank(cls, sid, rank):
        """根据竞技场对应排名的玩家数据

        主要适用于 挑战的时候对手的名次更变，需要把该名次最新的玩家找出来

        Args:
            rank 名次
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        data = redis_client.zrangebyscore(key, rank, rank, withscores=True)
        fighters = cls.build_fighter_data(sid, data)

        return fighters[0] if fighters else {}

    @classmethod
    def build_fighter_data(cls, sid, fighter_ranks):
        """组装竞技场玩家或者机器人数据

        Args:
            fighter_ranks = [('110000020', 260), ('110000017', 255)]
        """
        final_fighters = []
        for rank_data in fighter_ranks:
            fighter = {}
            fighter["uid"] = rank_data[0]
            fighter["rank"] = int(rank_data[1])
            # 判断是否是机器人
            if fighter["uid"].startswith("robot_"):
                key = rediskey_config.ARENA_ROBOTS_KEY % sid
                robot_data = redis_client.hget(key, rank_data[0])
                if robot_data:
                    robot_data = eval(robot_data)
                    fighter["name"] = robot_data["name"]
                else:
                    fighter["name"] = "Robot."
            else:
                from apps.models.user import User
                user = User.get(fighter['uid'])
                if isinstance(user, User):
                    fighter['name'] = user.name
                    fighter['avatar'] = user.avatar
                    fighter['fight'] = user.arena.fight

                    # fighter['level'] = user.game_info.role_level
                    # fighter['vip'] = user.game_info.vip_level
                    # try:
                    #     fighter['array'] = user_helper.build_arena_hero_euqip_skill(user)
                    # except:
                    #     fighter['array'] = static_const.DEFAULT_USER_ARRAY

                    # fighter['talents'] = user.talent.talents
                    # fighter['warship'] = user_helper.build_warship_data(user.warship.ships, user.warship.team)
                    # fighter['group_name'] = GroupService.get_name_by_id(user.sid, user.group.group_id)

            # 查找被膜拜的数量
            fighter["admired"] = cls.get_fighter_admired(sid, fighter["uid"]) or 0
            final_fighters.append(fighter)

        return final_fighters

    @classmethod
    def match_fighters(cls, sid, uid, rank, win_times):
        """根据匹配规则生成对手数据

        第一个对手匹配公式：玩家名次*0.35~玩家名次*0.5；
        第二个对手匹配公式：玩家名次*0.51~玩家名次*0.8；
        第三个对手匹配公式：玩家名次*0.81~玩家名次*1.2；
        第四个对手匹配公式：玩家名次*1.10~玩家名次*1.15；
        若是玩家名次为1~10 间，将会从11-20间随机匹配4个玩家，不在匹配公式内

        Args:
            rank 玩家的当前排名
            win_times 玩家胜场次数，为了保证玩家竞技场引导时必过，第一次匹配到的最后一个对手必须是渣渣

        Returns:
            fighters = []  4 名对手的数据
        """
        targets = []
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        if rank > 10:
            for i in xrange(4):
                if win_times == 0 and i == 3:
                    # 玩家第一次竞技场战斗，为了顺利通过引导，最后一个位置必须给他匹配一个渣渣机器人
                    special_robot = ('robot_99999', 99999)
                    targets.append(special_robot)
                else:
                    diff = math.sqrt(rank * MATCH_RULES[i]) / 3 + 5
                    # fighters = [('110000020', 260), ('110000017', 255)]
                    start, stop = rank * MATCH_RULES[i] - diff, rank * MATCH_RULES[i] + diff
                    fighters = redis_client.zrangebyscore(key, start, stop, withscores=True, score_cast_func=int)
                    # 此特殊情况是我身后没有玩家了，只能再从0.91 * rank ~ 1 * rank之间随一个不重复的
                    if not fighters:
                        _start, _stop = rank * MATCH_RULES[4] - diff, rank * MATCH_RULES[4] + diff
                        fighters = redis_client.zrangebyscore(key, _start, _stop, withscores=True, score_cast_func=int)

                    fighters = [i for i in fighters if str(i[0]) != str(uid)]   # 把自己给除开
                    fighters = list(set(fighters).difference(set(targets))) # 求差集，已经加入对手的就不要再加了
                    targets.append(random.choice(fighters))
        else:
            fighters = redis_client.zrangebyscore(key, 1, 20, withscores=True, score_cast_func=int)
            fighters = [i for i in fighters if str(i[0]) != str(uid)]  # 把自己给除开

            while len(targets) < 4:
                aim = random.choice(fighters)
                if aim not in targets:
                    targets.append(aim)

        final_fighters = cls.build_fighter_data(sid, targets)
        final_fighters = sorted(final_fighters, key=lambda x:x["rank"])

        return final_fighters

    @classmethod
    def top_ten(cls, sid):
        """当前竞技场前10数据

        Args:

        Returns:
            top_fighters = []  前10名数据
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        tops = redis_client.zrangebyscore(key, 1, 10, withscores=True, score_cast_func=int)
        top_fighters = cls.build_fighter_data(sid, tops)

        return top_fighters

    @classmethod
    def check_fighter_rank_matched(cls, sid, uid, rank):
        """检查当前uid对应的排名是否和发起挑战时的排名相同

        Args:
            uid 被挑战者的uid
            rank 被挑战者被挑战时的排名

        Returns:
            True or False
        """
        current_rank = cls.get_user_rank(sid, uid)

        return current_rank == rank

    @classmethod
    def fight(cls, sid, attack, defend, result):
        """处理挑战结果

        击败真实玩家 名次互换
        击败机器人 机器人的名次被盖住，待玩家离开这个名次之后再出现在这个名次上

        Args:
            attack 发起挑战者的UID
            defend 被挑战者的UID
            result 0 - 失败 1 - 胜利
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        try:
            attack_rank = int(redis_client.zscore(key, attack))
            defend_rank = int(redis_client.zscore(key, defend))
        except:
            logging.info("file: [arena service] method: [fight] failed. reason: defend_uid: %s attack_uid: %s attack_rank: %s" % (defend, attack, attack_rank))

        # 击败了比自己排名低的对手，不做操作
        if attack_rank <= defend_rank:
            return attack_rank

        diff_rank = attack_rank - defend_rank
        if defend.startswith("robot_"):
            redis_client.zrem(key, defend)  # 删除被击败的
            # ============================================
            # 千万要注意参数顺序啊，妈蛋，巨坑啊！！！！！
            redis_client.zincrby(key, attack, - diff_rank)  # 移动胜利方排名
            # ============================================
            # 如果挑战方名次在20000之内，这个位置的机器人再次出现
            if attack_rank < ARENA_ROBOTS_NUM:
                redis_client.zadd(key, attack_rank, "robot_" + str(attack_rank))
        else:
            # 真实玩家，替换名次
            try:
                redis_client.zincrby(key, defend, diff_rank)
                redis_client.zincrby(key, attack, - diff_rank)
            except Exception,e:
                raise e

        return defend_rank

    @classmethod
    def save_replay(cls, sid, attack_uid, attack_name, attack_avatar, defend, result, logs):
        """保存竞技场挑战日志

        Args:
            attack_uid 发起挑战者的UID
            attack_name 发起挑战者的角色名
            defend 被挑战者的UID
            result 0 - 失败 1 - 胜利
            logs 战斗日志

        Returns:

        """
        now = int(time.time())
        fight_id = Sequence.generate_arena_fight_log_id(sid)

        fight_log = {}
        fight_log["id"] = fight_id
        fight_log["time"] = now
        fight_log["attack_id"] = attack_uid
        fight_log["attack_name"] = attack_name
        fight_log["attack_avatar"] = attack_avatar
        fight_log["defend_id"] = defend

        defend_name, defend_avatar = cls.get_fighter_name_avatar_by_uid(sid, defend)
        fight_log["defend_name"] = defend_name
        fight_log["defend_avatar"] = defend_avatar

        fight_log["result"] = result
        fight_log["snapshot"] = {
            "attacker": {
                            "uid": attack_uid,
                            "name": attack_name,
                            "array": user_helper.build_arena_hero_snapshot(attack_uid),
                            "rank": cls.get_user_rank(sid, attack_uid)
                        },
            "defender": {
                            "uid": defend,
                            "name": defend_name,
                            "array": user_helper.build_arena_hero_snapshot(defend),
                            "rank": cls.get_user_rank(sid, defend)
                        },
        }
        fight_log["logs"] = logs

        pool_key = rediskey_config.ARENA_FIGHTLOG_POOL_KEY % sid
        redis_client.hset(pool_key, fight_id, pickle.dumps(fight_log))

        # 把战斗日志信息扔到一个大池子里，留一个编号让挑战者和被挑战者的人都记住，凭着号去取战斗历史记录
        # 机器人不用存战报
        fighters = [attack_uid,]
        if not defend.startswith("robot_"):
            fighters.append(defend)

        fighter_box_key = rediskey_config.ARENA_FIGHTLOG_BOX_KEY % sid
        for uid in fighters:
            fightlog_id_box = redis_client.hget(fighter_box_key, uid)
            if fightlog_id_box is None:
                redis_client.hset(fighter_box_key, uid, pickle.dumps([fight_id]))
            else:
                box = pickle.loads(fightlog_id_box)
                box.append(fight_id)
                redis_client.hset(fighter_box_key, uid, pickle.dumps(box[-20:]))

    @classmethod
    def get_replay(cls, sid, uid):
        """
        """
        logs = []
        fighter_box_key = rediskey_config.ARENA_FIGHTLOG_BOX_KEY % sid
        fightlog_id_box = redis_client.hget(fighter_box_key, uid)

        if not fightlog_id_box:
            return []

        fightlog_id_list = pickle.loads(fightlog_id_box)
        fightlog_id_list.reverse()
        pool_key = rediskey_config.ARENA_FIGHTLOG_POOL_KEY % sid
        for log_id in fightlog_id_list:
            log = redis_client.hget(pool_key, log_id)
            log_content = pickle.loads(log) if log else {}

            if log_content:
                del log_content["logs"]
                del log_content["snapshot"]

                logs.append(log_content)

        return logs

    @classmethod
    def get_single_replay(cls, sid, uid, log_id):
        """获取单个录像数据
        """
        pool_key = rediskey_config.ARENA_FIGHTLOG_POOL_KEY % sid

        log = redis_client.hget(pool_key, log_id)
        content = pickle.loads(log) if log else {}

        return content

    @classmethod
    def get_trial_fighters(cls, sid, start, end):
        """从排行榜中读取试炼对手数据

        Args:
            start 上线
            end 下线

        Returns:
            "110000001"
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        fighters = redis_client.zrangebyscore(key, start, end)

        return fighters

    @classmethod
    def get_trial_fighters2(cls, sid):
        """从竞技排行榜读取试炼对手数据

        取竞技场倒数500名内选取

        Args:

        Returns:
            "110000001"
        """
        key = rediskey_config.RANK_KEY_PREFIX % (sid, "arena")
        fighters = redis_client.zrange(key, -500, -1)

        return fighters

    @classmethod
    def get_robot_data(cls, sid, uid):
        """从机器人库里取出数据

        """
        robot_data = redis_client.hget(rediskey_config.ARENA_ROBOTS_KEY % sid, uid)
        robot_data = eval(robot_data)

        return robot_data

    @staticmethod
    def get_fighter_name_avatar_by_uid(sid, uid):
        """根据uid获取竞技场对手的名字

        Args:
            uid
        """
        fighter_name = ""
        fighter_avatar = 0
        # 判断是否是机器人
        if uid.startswith("robot_"):
            robot_data = redis_client.hget(rediskey_config.ARENA_ROBOTS_KEY % sid, uid)
            robot_data = eval(robot_data)
            fighter_name = robot_data["name"]
            fighter_avatar = 0
        else:
            from apps.models.user import User
            user = User.get(uid)
            if isinstance(user, User):
                fighter_name = user.name
                fighter_avatar = user.avatar

        return fighter_name, fighter_avatar

    @classmethod
    def heartbeat_info(cls, plat, sid, uid, last_sign):
        """心跳协议传送提示信息

        1. 竞技场被击败提示

        """
        info = {"fail_times": 0}

        fightlog_id_box = redis_client.hget(rediskey_config.ARENA_FIGHTLOG_BOX_KEY % sid, uid)
        if not fightlog_id_box:
            return info

        fightlog_id_list = pickle.loads(fightlog_id_box)
        for log_id in fightlog_id_list:
            log = redis_client.hget(rediskey_config.ARENA_FIGHTLOG_POOL_KEY % sid, log_id)
            if not log:
                continue
            else:
                log = pickle.loads(log)
                if log["time"] > last_sign and str(log["defend_id"]) == str(uid) and log["result"] == 1:
                    info["fail_times"] += 1

        return info
