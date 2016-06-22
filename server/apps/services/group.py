#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-10 11:15:58
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     公会服务
# @end
# @copyright (C) 2015, kimech

import copy
import time
import cPickle as pickle

from apps.misc import utils
from libs.rklib.core import app
from apps.models.user import User
from apps.models.group import Group

from apps.configs import game_config
from apps.configs import rediskey_config

from .mail import MailService
from .sequence import Sequence
from . import name as name_service
from . import rank as rank_service

from apps.logics.helpers import common_helper

redis_client = app.get_storage_engine('redis').client.current

# 每个玩家都有这个公会资讯邮箱  玩家被同意加入公会和被踢出公会消息都放在这个邮箱中，玩家在请求服务器时，自己去操作自己的数据，之后清空邮箱
# list => [{"from_group_id": 10001, "action": 1, "time": 1451475957}] # action 1-同意加入 0-被踢出
# 20151230晚9点 检测玩家是否有工会的时候太tm麻烦了，暂时直接修改玩家公会数据，不要信箱功能
# player_group_box_key = "xtzj.%s.group_info_box.%s"

GROUP_STATE_CLOSED = 0
GROUP_STATE_OPEN = 1

GROUP_JOIN_STATE_BAN = 0
GROUP_JOIN_STATE_FREE = 1
GROUP_JOIN_STATE_REQUEST = 2

GROUP_JOIN_REQUEST_STATE_DOING = 0
GROUP_JOIN_REQUEST_STATE_AGREE = 1
GROUP_JOIN_REQUEST_STATE_DENIED = 2

GROUP_LOG_TYPE_CREATE = 1
GROUP_LOG_TYPE_JOIN = 2
GROUP_LOG_TYPE_LEAVE = 3
GROUP_LOG_TYPE_KICK = 4
GROUP_LOG_TYPE_APPOINT = 5
GROUP_LOG_TYPE_DONATE = 6
GROUP_LOG_TYPE_GAME_TIGER = 7

GROUP_LOG_TYPE_GAME_2 = 8

GROUP_POSITION_MASTER = 1
GROUP_POSITION_MASTER2 = 2
GROUP_POSITION_ELITE = 3
GROUP_POSITION_MEMBER = 4

GROUP_POSITION_MASTER_NUMBER = 1
GROUP_POSITION_MASTER2_NUMBER = 2
GROUP_POSITION_ELITE_NUMBER = 15

class GroupService(object):
    """公会服务
    """
    def __init__(self):
        super(GroupService, self).__init__()

    @classmethod
    def create(cls, sid, name, icon, creater):
        """创建公会，初始化公会基础数据

        state : 1 - 正常，0 - 已解散

        Args:
            sid 服务器ID
            name 公会名称
            icon 公会图标
            creater 创建者信息 {"uid": "110000001", "icon": icon, "name": "test", "fight": 5521, "avatar": 10005, "level": 15, "login": 1451475957}

        Returns:

        """
        creater_uid = creater["uid"]
        group_id = Sequence.generate_group_id(sid)

        group = {}
        group["id"] = group_id
        group["icon"] = icon
        group["name"] = name
        group["exp"] = 0
        group["level"] = 1
        group["creater"] = creater_uid
        group["master"] = creater_uid
        group["member_number"] = 1
        group["join_level_limit"] = 0
        group["join_state"] = GROUP_JOIN_STATE_FREE
        group["notice"] = ""
        group["join_request_sequence"] = 0
        group["daily_update"] = time.strftime('%Y%m%d%H')
        group["daily_exp"] = 0
        group["state"] = GROUP_STATE_OPEN

        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        member_key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)

        try:
            redis_client.hmset(main_key, group)
            redis_client.hset(member_key, creater_uid, {"uid": creater_uid, "position":GROUP_POSITION_MASTER, "donate":0})
        except Exception,e:
            raise e

        name_service.add_created_group_name(name, group_id)
        rank_service.update_rank(sid, rank_service.RANK_GROUP, group_id, 0)
        cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_CREATE, creater_uid, creater["name"], int(time.time()))

        return group_id

    @classmethod
    def get_name_by_id(cls, sid, group_id):
        """
        """
        if not group_id:
            return ''

        group_data = cls.find(sid, group_id)
        return group_data["name"] if group_data else ''

    @classmethod
    def groupcount(cls, sid):
        """公会总数量
        """
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, "group")
        return redis_client.zcard(ranking_name)

    @classmethod
    def rank(cls, sid, start=0, end=0):
        """公会排行数据

        从rank cache中取
        """
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, "group")
        ranking_list = redis_client.zrevrange(ranking_name, start-1, end-1)

        ranks = []
        for i in ranking_list:
            group_data = cls.find(sid, int(i))
            if group_data:
                tmp = {"rank": start, "group_id": group_data["id"]}
                for key,value in group_data.items():
                    if key in ["notice", "icon", "name", "level", "member_number", "join_state", "join_level_limit"]:
                        tmp[key] = value

                ranks.append(tmp)
                start += 1

        return ranks

    @classmethod
    def tiger_rank(cls, sid, group_id, start=0, end=0):
        """老虎机排行榜
        """
        ranking_name = rediskey_config.GROUP_GAME_TIGER_KEY % (sid, group_id)
        ranking_list = redis_client.zrevrange(ranking_name, start-1, end-1, withscores=True)

        ranks = []
        for index,i in enumerate(ranking_list):
            uid, process, rank = i[0], int(i[1]), index+start
            user = User.get(uid)
            tmp = {"rank": rank, "uid": uid, "process": "%s-%s" % (process / 1000, process % 1000), "avatar": user.avatar, "name": user.name}
            ranks.append(tmp)

        return ranks

    @classmethod
    def tiger_rank_single(cls, sid, group_id, uid):
        """老虎机个人最佳查询
        """
        ranking_name = rediskey_config.GROUP_GAME_TIGER_KEY % (sid, group_id)
        result = redis_client.zscore(ranking_name, uid)
        result = result if result else 0

        return "%s-%s" % (result / 1000, result % 1000)

    @classmethod
    def bird_rank(cls, sid, group_id, start=0, end=0):
        """小鸟排行榜
        """
        ranking_name = rediskey_config.GROUP_GAME_BIRD_KEY % (sid, group_id)
        ranking_list = redis_client.zrevrange(ranking_name, start-1, end-1, withscores=True)

        ranks = []
        for index,i in enumerate(ranking_list):
            uid, process, rank = i[0], i[1], index+start
            user = User.get(uid)
            tmp = {"rank": rank, "uid": uid, "process": process, "avatar": user.avatar, "name": user.name}
            ranks.append(tmp)

        return ranks

    @classmethod
    def tiger_rank_single(cls, sid, group_id, uid):
        """小鸟个人最佳查询
        """
        ranking_name = rediskey_config.GROUP_GAME_BIRD_KEY % (sid, group_id)
        result = redis_client.zscore(ranking_name, uid)
        result = result if result else 0

        return result

    @classmethod
    def update_game_tiger_rank(cls, sid, uid, group_id, point):
        """更新老虎机排行榜

        计分方式
            5001 【5 - 点数 1 - 相对次数】
        """
        ranking_name = rediskey_config.GROUP_GAME_TIGER_KEY % (sid, group_id)
        result = redis_client.zscore(ranking_name, uid)
        old = int(result) if result else 0

        if old / 1000 < point:
            score = point * 1000 + 1
            redis_client.zadd(ranking_name, score, uid)
        elif old / 1000 == point:
            score = point * 1000 + (old % 1000 + 1)
            redis_client.zadd(ranking_name, score, uid)
        else:
            pass

    @classmethod
    def update_game_bird_rank(cls, sid, uid, group_id, process):
        """更新小鸟排行榜
        """
        ranking_name = rediskey_config.GROUP_GAME_BIRD_KEY % (sid, group_id)
        redis_client.zadd(ranking_name, process, uid)

    @classmethod
    def update(cls, sid, group_id, values):
        """修改公会信息

        1.图标 2.公告 3.限制加入等级 4.加入状态

        Args:
            type 标记类型 1-公会名称 2-公会ID
            tag 标记 公会名称或者ID

        Returns:
            group_data {}

        """
        rkey = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        redis_client.hmset(rkey, values)

    @classmethod
    def find(cls, sid, tag, type=2):
        """根据名称或者公会ID获得公会数据

        Args:
            type 标记类型 1-公会名称 2-公会ID
            tag 标记 公会名称或者ID

        Returns:
            group_data {}

        """
        if type == 1:
            group_id = name_service.get_group_id_by_name(tag)
        else:
            group_id = tag

        key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        result = redis_client.hgetall(key)
        if result:
            data = cls.build_group_data(result)
            if data["state"] == GROUP_STATE_OPEN:
                return data
            else:
                return {}
        else:
            return {}

    @classmethod
    def quick_search(cls, sid, role_level):
        """
        """
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, "group")
        sorted_group_ids = redis_client.zrange(ranking_name, 0, -1)
        for id in sorted_group_ids:
            group_data = cls.find(sid, id)
            if group_data and group_data["join_state"] == GROUP_JOIN_STATE_FREE and group_data["join_level_limit"] <= role_level:
                cfg = game_config.group_cfg.get(group_data["level"], {})
                max_number = cfg["max_member"] if cfg else 0
                if group_data["member_number"] < max_number:
                    return group_data

        return {}

    @classmethod
    def join_request(cls, sid, group_id, applyer_uid):
        """申请加入公会

        Args:
            applyer_uid 申请者UID

        """
        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        request_key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)

        user = User.get(applyer_uid)
        applyer = user.get_user_group_info()

        seq = redis_client.hincrby(main_key, "join_request_sequence")
        # applyer.update({"request_uid": seq, "state": GROUP_JOIN_REQUEST_STATE_DOING})
        applyer.update({"request_id": seq})
        redis_client.lpush(request_key, applyer)

    @classmethod
    def search_request(cls, sid, group_id, request_id):
        """查找申请单号信息

        Args:
            request_id 申请单号

        """
        request_key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)
        for i in range(redis_client.llen(request_key)):
            result = redis_client.lindex(request_key, i)
            result1 = cls.build_group_member_data(result)
            if result1 and result1["request_id"] == request_id:
                return result1

        return {}

    @classmethod
    def check_in_apply_list(cls, sid, group_id, uid):
        """确认玩家是否已经申请过这个公会

        """
        request_key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)
        for i in range(redis_client.llen(request_key)):
            result = redis_client.lindex(request_key, i)
            result1 = cls.build_group_member_data(result)
            if result1 and result1["uid"] == uid:
                return True

        return False

    @classmethod
    def agree(cls, sid, group_id, joiner_id, atype=1):
        """同意加人申请 & 直接加入

        atype 1-审核批准别人加入 2-直接加入

        # 1、给加入玩家公会资讯信箱投递消息
        2、公会成员列表增加记录
        3、公会成员数量+1
        3、公会日志增加一条记录
        4、公会聊天频道发广播

        Args:
            joiner_id 加入者UID

        """
        # player_group_box = player_group_box_key % (sid, joiner_id)
        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        member_key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)

        # 取加入者数据
        # {"uid": "110000001", "name": "test", "fight": 5521, "avatar": 10005, "level": 15, "login": 1451475957}
        user = User.get(joiner_id)

        try:
            # pipe.lpush(player_group_box, {"from_group_id": group_id, "action": 1, "time": int(time.time()), "time": int(time.time())})
            redis_client.hset(member_key, joiner_id, {"uid": joiner_id, "position":GROUP_POSITION_MEMBER, "donate":0})
            redis_client.hincrby(main_key, "member_number")

            # 被别人审核通过加入才需要执行这步骤
            if atype == 1:
                user.group.join(group_id)

        except Exception,e:
            raise e

        cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_JOIN, joiner_id, user.name, int(time.time()))
        # TODO 公会频道发广播

    @classmethod
    def delete_request(cls, sid, group_id, request_id):
        """处理完后删除申请单信息

        Args:
            request_id 申请单号

        """
        request_key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)
        for i in range(redis_client.llen(request_key)):
            result = redis_client.lindex(request_key, i)
            result1 = cls.build_group_member_data(result)
            if result1 and result1["request_id"] == request_id:
                redis_client.lrem(request_key, 0, result) # 0 - 删除所有值为result的元素

    @classmethod
    def delete_all_request(cls, sid, group_id):
        """一键拒绝即删除所有玩家入会申请

        Args:

        """
        request_key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)
        redis_client.delete(request_key)

    @classmethod
    def get_position_number(cls, sid, group_id, position):
        """检测当前职位人数

        Args:
            position 职位
        """
        members = cls.members(sid, group_id)
        if not members:
            return 0
        else:
            count = len([member for member in members if member["position"] == position])
            return count

    @classmethod
    def appoint(cls, sid, group_id, acter_uid, member_uid, position):
        """任命成员

        Args:
            acter_uid 操作者UID
            member_uid 目标UID
            position 职务

        """
        user = User.get(member_uid)
        if position != GROUP_POSITION_MASTER:
            cls.set_member_info_by_uid(sid, group_id, member_uid, "position", position)
        else:
            cls.set_member_info_by_uid(sid, group_id, acter_uid, "position", GROUP_POSITION_MEMBER)
            cls.set_member_info_by_uid(sid, group_id, member_uid, "position", position)

            # 转让会长
            main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
            redis_client.hset(main_key, "master", user.uid)

        cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_APPOINT, member_uid, user.name, int(time.time()), position)

    @classmethod
    def donate(cls, sid, group_id, donater_id, donater_name, group_exp, tag):
        """公会成员捐献

        1、公会成员列表记录更新
        2、公会经验增长
        3、公会日志增加一条记录
        4、公会聊天频道发广播

        Args:
            donater_id 加入者UID

        """
        # 增加公会经验前，先更新今日经验
        cls.update_daily_exp(sid, group_id)

        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        redis_client.hincrby(main_key, "daily_exp", group_exp)

        # 更新经验和排行榜
        new_exp = redis_client.hincrby(main_key, "exp", group_exp)
        rank_service.update_rank(sid, rank_service.RANK_GROUP, group_id, new_exp)

        # 更新等级
        old_level = int(redis_client.hget(main_key, "level"))
        new_level = common_helper.get_level_by_exp(game_config.group_exp_cfg, new_exp)
        if old_level != new_level:
            redis_client.hset(main_key, "level", new_level)

        cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_DONATE, donater_id, donater_name, int(time.time()), tag)

        # TODO 公会频道发广播

    @classmethod
    def quit(cls, sid, group_id, quiter_id, quiter_name):
        """退出公会

        1、公会成员列表删除该成员记录
        2、公会成员数量-1
        3、公会日志增加一条记录
        4、公会聊天频道发广播

        Args:
            quiter_id 退出者UID

        """
        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        member_key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)

        try:
            redis_client.hdel(member_key, quiter_id)
            redis_client.hincrby(main_key, "member_number", -1)
        except Exception,e:
            raise e

        if int(redis_client.hget(main_key, "member_number")) == 0:
            cls.delete(sid, group_id)
        else:
            cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_LEAVE, quiter_id, quiter_name, int(time.time()))
            # TODO 公会频道发广播

    @classmethod
    def kick(cls, sid, group_id, uid):
        """踢人

        1、给被踢玩家公会资讯信箱投递消息
        2、从公会除名
        3、公会成员数量-1
        3、公会日志增加一条记录
        4、公会聊天频道发广播
        5、给被踢玩家发邮件

        Args:
            uid 被踢出公会者ID

        """
        # player_group_box = player_group_box_key % (sid, uid)
        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        member_key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)

        user = User.get(uid)

        try:
            # redis_client.lpush(player_group_box, {"from_group_id": group_id, "action": 0, "time": int(time.time())})
            redis_client.hdel(member_key, uid)
            redis_client.hincrby(main_key, "member_number", -1)
            user.group.quit()

            # 清楚训练场数据
            redis_client.hdel(rediskey_config.GROUP_TRAIN_KEY % (sid, group_id), uid)
            redis_client.hdel(rediskey_config.GROUP_TRAIN_LOG_KEY % (sid, group_id), uid)
        except Exception,e:
            raise e

        cls.create_group_log(sid, group_id, GROUP_LOG_TYPE_KICK, uid, user.name, int(time.time()))
        # TODO 公会频道发广播

        # 给被踢玩家发邮件
        gname = redis_client.hget(main_key, "name")
        MailService.send_game(uid, 4001, [gname], {})

    @classmethod
    def delete(cls, sid, group_id):
        """解散公会

        Args:
            sid,group_id

        Returns:

        """
        key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        result = redis_client.hset(key, "state", GROUP_STATE_CLOSED)
        # 从排行数据里删除
        ranking_name = rediskey_config.RANK_KEY_PREFIX % (sid, "group")
        redis_client.zrem(ranking_name, group_id)

    @classmethod
    def join_requests(cls, sid, group_id, start, end):
        """获取公会的申请记录
        """
        key = rediskey_config.GROUP_REQUEST_KEY % (sid, group_id)
        result = redis_client.lrange(key, start-1, end-1)

        if not result:
            return []
        else:
            return [cls.build_group_member_data(record) for record in result]

    @classmethod
    def logs(cls, sid, group_id, start, end):
        """获取公会的日志
        """
        key = rediskey_config.GROUP_LOGS_KEY % (sid, group_id)
        result = redis_client.lrange(key, start-1, end-1)
        if not result:
            return []
        else:
            return [cls.build_group_log_data(record) for record in result]

    @classmethod
    def members(cls, sid, group_id, start=1, end=999):
        """获取公会全体成员

        Args:
            sid,group_id

        Returns:

        """
        key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)
        result = redis_client.hgetall(key)
        if not result:
            return []
        else:
            simple_members = [cls.build_group_member_data(member) for member in result.values()]
            simple_members1 = sorted(simple_members, key=lambda x:x["position"])
            targets = []
            for m in simple_members1[start-1:end]:
                user = User.get(m["uid"])
                extra_fields = {
                                "login": user.last_request,
                                "fight": user.game_info.fight,
                                "level": user.game_info.role_level,
                                "name": user.name,
                                "avatar": user.avatar,
                            }
                m.update(extra_fields)
                targets.append(m)

            return targets

    @classmethod
    def get_master_name_by_uid(cls, uid):
        """获取公会会长名称
        """
        user = User.get(uid)
        if isinstance(user, User):
            return user.name
        else:
            return ""

    @classmethod
    def get_member_info_by_uid(cls, sid, group_id, uid):
        """获取公会成员数据
        """
        key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)
        result = redis_client.hget(key, uid)
        if result:
            return cls.build_group_member_data(result)
        else:
            return {}

    @classmethod
    def set_member_info_by_uid(cls, sid, group_id, uid, field, value):
        """更新公会成员数据
        """
        member = cls.get_member_info_by_uid(sid, group_id, uid)
        if not member:
            return
        else:
            if field == "donate":
                member[field] += value
            else:
                member[field] = value

            key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)
            redis_client.hset(key, uid, member)

    @staticmethod
    def create_group_log(sid, group_id, ltype, uid, uname, time, data=0):
        """记录公会日志

        Args:
            ltype 日志类型
            uid 涉及角色ID
            uname 涉及角色名称
            time 发生时间戳
            data 涉及数值

        Returns:

        """
        logs_key = rediskey_config.GROUP_LOGS_KEY % (sid, group_id)
        redis_client.lpush(logs_key, {"uid": uid, "name": uname, "data": data, "action":ltype, "time":time})

    @staticmethod
    def build_group_data(data):
        """构建公会数据

        把从redis取出来的所有数据按格式进行转换

        Args:
            data {"id": "10001", "name": "test", "exp": "110"}

        Returns:
            data {"id": 10001, "name": "test", "exp": 110}
        """
        try:
            if isinstance(data, str):
                data = eval(data)
        except Exception,e:
            data = {}

        realdata = copy.deepcopy(data)
        for key, value in data.items():
            if key not in ["name", "creater", "notice", "master"]:
                realdata[key] = int(value)
            else:
                realdata[key] = value

        return realdata

    @staticmethod
    def build_group_member_data(data):
        """构建公会成员数据

        把从redis取出来的所有数据按格式进行转换

        Args:
            data {"uid": "110000001", "position": "1", "donate": "100"}

        Returns:
            data {"uid": "110000001", "position":1, "donate":100}
            tip: {"login":1451462290,"fight":5540,"level":10,"name":"Ame","avatar":10005}
        """
        try:
            if isinstance(data, str):
                data = eval(data)
        except:
            data = {}

        if not data:
            return {}

        realdata = copy.deepcopy(data)
        for key, value in data.items():
            realdata[key] = value if key in ["uid", "name"] else int(value)

        return realdata

    # @staticmethod
    # def build_group_request_data(data):
    #     """构建公会申请数据

    #     把从redis取出来的所有数据按格式进行转换

    #     Args:
    #         data {"request_id": "1000023", "uid": "110000001", "name": "AME", "avatar": "100005", "level": "10", "fight": "5540", "state": "1"}

    #     Returns:
    #         data {"request_id": 1000023, "uid": "110000001", "name": "AME", "avatar": 100005, "level": 10, "fight": 5540, "state": 1}
    #     """
    #     realdata = copy.deepcopy(data)

    #     for key, value in data.items():
    #         if key not in ["uid", "name"]:
    #             realdata[key] = int(value)
    #         else:
    #             realdata[key] = value

    #     return realdata

    @staticmethod
    def build_group_log_data(data):
        """构建公会日志数据

        把从redis取出来的所有数据按格式进行转换

        Args:
            data {"uid": "110000001", "name": "AME", "data": "120", "action": "1", "time": "1451462290"}

        Returns:
            data {"uid": "110000001", "name": "AME", "data": 120, "action": 1, "time": 1451462290}
        """
        try:
            data = eval(data)
        except:
            data = {}

        if not data:
            return {}

        realdata = copy.deepcopy(data)
        if int(realdata["action"]) == GROUP_LOG_TYPE_DONATE:
            keys = ["uid", "name", "data"]
        else:
            keys = ["uid", "name"]

        for key, value in data.items():
            if key not in keys:
                realdata[key] = int(value)
            else:
                realdata[key] = value

        return realdata

    @classmethod
    def update_daily_exp(cls, sid, group_id):
        """到点刷新每日经验数据
        """
        main_key = rediskey_config.GROUP_MAIN_KEY % (sid, group_id)
        if common_helper.time_to_refresh(int(redis_client.hget(main_key, "daily_update")), 5):
            redis_client.hset(main_key, "daily_update", time.strftime('%Y%m%d%H'))
            redis_client.hset(main_key, "daily_exp", 0)

            redis_client.delete(rediskey_config.GROUP_TRAIN_KEY % (sid, group_id))
            redis_client.delete(rediskey_config.GROUP_TRAIN_LOG_KEY % (sid, group_id))

    @staticmethod
    def check_player_has_group(sid, uid):
        """审核通过时，检查玩家是否有公会

        1.检查玩家当前的group_id
        # 【暂时取缔】 2.检查玩家的邮箱中是否有已经被加入其他公会或者踢出公会的消息

        """
        user = User.get(uid)
        return True if user.group.group_id else False

    @classmethod
    def train_members(cls, sid, group_id, myid, start=1, end=999):
        """获取公会全体成员训练所数据

        Args:
            sid,group_id

        Returns:

        """
        key = rediskey_config.GROUP_MEMBER_KEY % (sid, group_id)
        result = redis_client.hgetall(key)
        if not result:
            return []
        else:
            simple_members = [cls.build_group_member_data(member) for member in result.values()]
            simple_members1 = sorted(simple_members, key=lambda x:x["position"])
            targets = []
            for m in simple_members1[start-1:end]:
                if m["uid"] == myid:
                    continue

                user = User.get(m["uid"])
                train_heros = [i for i in user.group.train_list if i not in [0,-1]]
                helped_times = GroupService.get_train_pos_times(sid, group_id, m["uid"])
                if not train_heros or int(helped_times) >= 6:
                    continue

                user_fields = {
                                "level": user.game_info.role_level,
                                "name": user.name,
                                "avatar": user.avatar,
                                "train_heros": train_heros,
                            }

                m.update(user_fields)
                targets.append(m)

            return targets

    @classmethod
    def get_train_all_add_times(cls, sid, group_id, uid, datas):
        """获取姬甲被公会其它成员加速的次数
        """
        key = rediskey_config.GROUP_TRAIN_HERO_KEY % (sid, group_id)

        tmp = {}
        for i in datas:
            if i not in [0,-1]:
                result = redis_client.hget(key, "%s_%s" % (uid, i))
                tmp[i] = 0 if not result else result

        return tmp

    @classmethod
    def get_train_hero_times(cls, sid, group_id, uid, hero_id):
        """获取姬甲被公会其它成员加速的次数
        """
        key = rediskey_config.GROUP_TRAIN_HERO_KEY % (sid, group_id)
        result = redis_client.hget(key, "%s_%s" % (uid, hero_id))
        redis_client.hset(key, "%s_%s" % (uid, hero_id), 0)

        return 0 if not result else result

    @classmethod
    def get_train_pos_times(cls, sid, group_id, uid):
        """获取成员被加速次数
        """
        key = rediskey_config.GROUP_TRAIN_KEY % (sid, group_id)
        result = redis_client.hget(key, uid)

        return 0 if not result else result

    @classmethod
    def get_train_logs(cls, sid, group_id, uid):
        key = rediskey_config.GROUP_TRAIN_LOG_KEY % (sid, group_id)
        result = redis_client.hget(key, uid)

        return [] if not result else pickle.loads(result)

    @classmethod
    def update_train_express_times(cls, sid, group_id, uid, hero_id, myname):
        """更新训练所姬甲被其它成员加速次数
        """
        cls.update_daily_exp(sid, group_id)
        log_key = rediskey_config.GROUP_TRAIN_LOG_KEY % (sid, group_id)
        logs = redis_client.hget(log_key, uid)
        logs1 = pickle.loads(logs) if logs else []
        logs1.append(myname)

        pipeline = redis_client.pipeline()
        pipeline.multi()
        pipeline.hincrby(rediskey_config.GROUP_TRAIN_HERO_KEY % (sid, group_id), "%s_%s" % (uid, hero_id), 1)
        pipeline.hincrby(rediskey_config.GROUP_TRAIN_KEY % (sid, group_id), uid, 1)
        pipeline.hset(log_key, uid, pickle.dumps(logs1))
        pipeline.execute()
