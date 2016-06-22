#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-30 18:51:53
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     系统业务
# @end
# @copyright (C) 2015, kimech

import time
import httplib

import simplejson as json

from tornado.escape import json_encode
from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.services.mail import MailService
from apps.services.chat import ChatService
from apps.services.notice import NoticeService
from apps.services.arena import ArenaService
from apps.services.group import GroupService
from apps.services import charge as charge_service
from apps.services.statistics import Statictics as stat_service

from .helpers import act_helper
from .helpers import common_helper

from apps.services.chargecallbacks.common import handle_order_data
from apps.services.chargecallbacks.common import charge_error_log

def heartbeat(context):
    """心跳协议，玩家在主场景时，
       每隔几分钟向服务器请求一次，
       检测服务器是否有需要提醒前端的功能

    包括:
        1.新邮件
        2.私聊消息
        3.跑马灯公告
        4.竞技场被击败
    """
    ki_user = context.user

    uid = ki_user.uid
    sid = ki_user.sid
    group_id = ki_user.group.group_id
    plat = ki_user.platform

    data = {}
    data["new_mails"] = len(MailService.query_mails(uid, 0))

    private_msgs = ChatService.get_private_msgs(sid, uid, ki_user.game_info.last_chat_read)
    data["private_msgs"] = 1 if private_msgs else 0

    broadcast_msgs = NoticeService.get_broadcasts(sid, ki_user.game_info.broadcast_id)
    data["broadcast_msgs"] = broadcast_msgs

    ki_user.game_info.refresh_broadcast_stamp()

    # arena_last_sign = ki_user.arena.extra_data.get("heartbeat_last_sign", 0)
    # arena_info = ArenaService.heartbeat_info(plat, sid, uid, arena_last_sign)
    # data["arena_info"] = {"fail_times": 0}

    # 充值付费标记，1 - 有已完成付费的充值订单，0 - 没有已完成充值付费的订单
    data["paid_tag"] = charge_service.ismember_of_paid_set(uid)

    # 通关心跳来检测玩家新活动  从数据库中取活配置
    # activity = {}
    # activity["info"] = act_helper.get_active_act_info(sid, ki_user.game_info.role_level)
    # activity["data"] = ki_user.activity.get_effective_acts(sid, ki_user.game_info.role_level)
    # data["activity"] = activity

    # 公会数据  玩家被审核或者被踢出公会之后  通过心跳通知前端
    data["group"] = {}
    data["group"]["group_id"] = group_id
    data["group"]["cd"] = ki_user.group.cd

    # 处理训练所 姬甲挂机经验
    # train_heros = [i for i in ki_user.group.train_list if i not in [0,-1]]
    # if group_id and train_heros:
    #     group_data = GroupService.find(sid, group_id)
    #     if group_data:
    #         data["group"]["level"] = group_data["level"]
    #         gcfg = game_config.group_cfg.get(group_data["level"], {})
    #         # if gcfg["open_train"]:
    #         data["group"]["train_hero_exps"] = handle_group_train_heros(train_heros, ki_user, gcfg["train_exp"])

    context.result["data"] = data

def handle_group_train_heros(train_heros, user, exp_every_minutes):
    """每个心跳中结算公会训练所的姬甲数据
    """
    now = int(time.time())
    train_hero_exps = {}
    for hero_id in train_heros:
        hero = user.hero.heros[hero_id]
        tmp_exp = hero["exp"]
        max_exp = game_config.hero_level_exp_cfg.get(hero["level"]+1, None)
        if not max_exp:
            continue

        # 经验已经最大，更新时间改为当前
        if hero["level"] >= user.game_info.role_level and tmp_exp >= max_exp:
            user.group.train_dict[hero_id] = now
        else:
            interval_minutes = int(now - user.group.train_dict[hero_id]) / 60
            # 读取别人帮我加速的次数
            express_times = GroupService.get_train_hero_times(user.sid, user.group.group_id, user.uid, hero_id)
            add_exp = (interval_minutes + int(express_times) * 30) * exp_every_minutes
            user.group.train_dict[hero_id] += interval_minutes * 60     # 更新时间

            if tmp_exp + add_exp > max_exp:
                tmp_exp = max_exp
                user.group.train_dict[hero_id] = now
            else:
                tmp_exp += add_exp

            after_level = common_helper.get_level_by_exp(game_config.hero_exp_level_cfg, tmp_exp)
            user.hero.update_exp_level(hero_id, tmp_exp, min(user.game_info.role_level, after_level), False)

        train_hero_exps[hero_id] = add_exp

    user.hero.put()
    user.group.put()

    return train_hero_exps
