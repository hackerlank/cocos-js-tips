#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 10:32:37
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     公告服务器
#       公告规则，为避免大规模的查询带来的服务器响应时间特长，按公告类型优先级取出20条扔给客户端
#       优先级：官方公告>公会战第1>抽到4星卡>抽到3星卡>升到7星>升到6星>升到5星>获得觉醒材料>觉醒星际宝箱获得XX>试炼达到n层>竞技场前10>通关噩梦副本>抽到2星卡
#        1.跑马灯
#        2.登录面板
# @end
# @copyright (C) 2015, kimech

import time
import datetime

import cPickle as pickle

from libs.rklib.core import app
from apps.configs import rediskey_config

from sequence import Sequence

redis_client = app.get_storage_engine('redis').client.current

BROADCAST_MAX_NUM = 20

NOTICE_TYPE_1 = 1 # 登录面板
# {'id': 110000005, "notice_type":2, "start": 1448914158, "end": 1448915158, "content":"test", "id": 110000005}
NOTICE_TYPE_2 = 2 # 跑马灯公告

NOTICE_TYPE_11 = 11 # 1、    玩家在姬库抽到完整姬甲 {'notice_type': 11, 'trigger': {'uid': '110000001', 'name': 'player1'}, 'data': {'hero_id': 100005, 'star': 4, 'quality': 3}}
NOTICE_TYPE_12 = 12 # 2、    姬甲升星到5-7星
NOTICE_TYPE_13 = 13 # 3、    终极试炼系统，玩家通过40层（包括40层）以上每10层触发{'notice_type': 13, 'trigger': {'uid': '110000001', 'name': 'player1'}, 'data': 40}
NOTICE_TYPE_14 = 14 # 4、    商店觉醒星际宝箱中获得紫色品质以上（包括紫色） {'notice_type': 14, 'trigger': {'uid': '110000001', 'name': 'player1'}, 'data': 120001}
NOTICE_TYPE_15 = 15 # 5、    竞技场玩家每次进入前10名时触发 {'notice_type': 15, 'trigger': {'uid': '110000001', 'name': 'player1'}, 'data': 4}
NOTICE_TYPE_16 = 16 # 6、    噩梦副本章节满星时触发 {'notice_type': 16, 'trigger': {'uid': '110000001', 'name': 'player1'}, 'data': 202110}
NOTICE_TYPE_17 = 17 # 7、    公会战获得第一名时触发
NOTICE_TYPE_18 = 18 # 8、    公会战积分第一名玩家
NOTICE_TYPE_19 = 19 # 9、    获得觉醒材料时触发
NOTICE_TYPE_20 = 20 # 10、   世界BOSS英雄舰长登录时全服公告

BROADCAST_PRIORITY = ["20", "17", "11_4", "11_3", "12_7", "12_6", "12_5", "19", "14", "13", "15", "16", "11_2"]

class NoticeService(object):
    """公告服务
    """
    def __init__(self):
        super(NoticeService, self).__init__()

    @classmethod
    def get_login_notices(cls):
        """根据平台ID获取登录公告

        Args:

        """
        now = int(time.time())
        redis_key = rediskey_config.NOTICE_BOX_KEY

        results = []
        _tmp = redis_client.hgetall(redis_key)

        if not _tmp:
            return []

        for notice, content in _tmp.items():
            notice1 = pickle.loads(content)
            if notice1["notice_type"] == NOTICE_TYPE_1 and notice1["start"] <= now < notice1["end"]:
                results.append(notice1["content"])

        return results

    @classmethod
    def get_broadcasts(cls, sid, start=0):
        """根据平台ID获取广播信息

        Args:
            sid :服务器ID
            start :起始位置，用于从哪条开始取跑马灯，前端以及播放过的不再取

        Returns:
            []
        """
        # 系统广播
        now = int(time.time())
        redis_key1 = rediskey_config.NOTICE_BOX_KEY
        _tmp1 = redis_client.hgetall(redis_key1)
        results = []
        if _tmp1:
            for notice, content in _tmp1.items():
                notice1 = pickle.loads(content)
                if notice1["notice_type"] == NOTICE_TYPE_2 and notice1["start"] <= now < notice1["end"]:
                    results.append(notice1)

        broadcasts = []
        index = 0
        while len(broadcasts) < BROADCAST_MAX_NUM and index < len(BROADCAST_PRIORITY):
            left_space = BROADCAST_MAX_NUM - len(broadcasts)
            redis_key = rediskey_config.BROADCAST_BOX_KEY % (sid, BROADCAST_PRIORITY[index])

            _tmp = redis_client.lrange(redis_key, 0, left_space-1)
            for i in _tmp:
                msg = pickle.loads(i)
                if msg["time"] >= start:
                    broadcasts.append(msg)

            index += 1

        return results + broadcasts

    @classmethod
    def broadcast(cls, sid, ntype, trigger, data):
        """炫耀广播

        Args:
            ntype 减宏定义
            trigger: 'player': {'uid': '110000001', 'name': 'player1'} 'group': {'group_id': 10004, 'name': 'group_1'}
            data: 'hero': {'hero_id': 100005, 'star': 4, 'quality': 4} & 物品ID & 挑战层数 & 竞技场名次 & 副本ID

        """
        now = int(time.time())
        notice = {"notice_type": ntype, "trigger": trigger, "data": data, "time": int(time.time())}

        cls.save(sid, 0, ntype, notice)

    @classmethod
    def admin_notice(cls, sid, start, end, content):
        """登录面板公告
        """
        id = Sequence.generate_notice_id(sid)
        notice = {"notice_type": NOTICE_TYPE_1, "start": start, "end": end, "content": content, "id": id}

        cls.save(sid, id, NOTICE_TYPE_1, notice)

    @classmethod
    def admin_broadcast(cls, sid, start, end, interval, msg):
        """系统跑马灯广播
        """
        now = int(time.time())
        id = Sequence.generate_notice_id(sid)
        notice = {"notice_type": NOTICE_TYPE_2, "start": start, "end": end, "interval": interval, "content": msg, "id": id}

        cls.save(sid, id, NOTICE_TYPE_2, notice)

    @classmethod
    def admin_delete_notice(cls, plat, notice_id):
        """
        """
        redis_client.hdel(rediskey_config.NOTICE_BOX_KEY, notice_id)

    @staticmethod
    def save(sid, nid, ntype, notice):
        if ntype in [NOTICE_TYPE_1, NOTICE_TYPE_2]:
            redis_key = rediskey_config.NOTICE_BOX_KEY
            redis_client.hset(redis_key, nid, pickle.dumps(notice))
        else:
            if ntype in [NOTICE_TYPE_11, NOTICE_TYPE_12]:
                redis_key = rediskey_config.BROADCAST_BOX_KEY % (sid, "%s_%s" % (ntype, notice["data"].get("star", 0)))
            else:
                redis_key = rediskey_config.BROADCAST_BOX_KEY % (sid, ntype)

            redis_client.lpush(redis_key, pickle.dumps(notice))
