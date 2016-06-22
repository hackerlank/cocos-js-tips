#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 10:32:37
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     聊天
# @end
# @copyright (C) 2015, kimech

import time

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.services.chat import ChatService
from apps.logics import user as user_logic
from apps.logics import package as pack_logic
from apps.configs import static_const
from apps.services.name import gfw

CHAT_CHANNEL_WORLD = 1
CHAT_CHANNEL_GROUP = 2
CHAT_CHANNEL_NOTICE = 3
CHAT_CHANNEL_PRIVATE = 4

WORLD_CHAT_EXTRA_DIAMOND = 5

# ========================= GAME API ==============================
def info(context):
    """读取聊天内容

    Args:

    """
    ki_user = context.user

    ctype = context.get_parameter("ctype")
    start = context.get_parameter("start")
    end = context.get_parameter("end")

    if ctype not in [CHAT_CHANNEL_WORLD,CHAT_CHANNEL_GROUP,CHAT_CHANNEL_NOTICE,CHAT_CHANNEL_PRIVATE]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if start <= 0:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    msgs = []
    if ctype == CHAT_CHANNEL_WORLD or ctype == CHAT_CHANNEL_NOTICE:
        msgs = ChatService.get_chat_msgs(ki_user.sid, ctype, start, end)
    elif ctype == CHAT_CHANNEL_GROUP:
        msgs = ChatService.get_chat_msgs(ki_user.sid, ctype, start, end, group_id=ki_user.group.group_id)
    else:
        msgs = ChatService.get_chat_msgs(ki_user.sid, ctype, start, end, uid=ki_user.uid)

    ki_user.game_info.last_chat_read = int(time.time())
    ki_user.game_info.put()

    data = {}
    data["msgs"] = msgs
    context.result["data"] = data

def send(context):
    """发送聊天

    Args:
        ctype: 聊天类型 1 - 世界 2 - 公会 3 - 公告 4 - 私聊 (公告不能发)
        msg: 聊天内容
        receiver: 私聊时，传接收消息的玩家uid

    Returns:
        mc

    """
    ki_user = context.user

    ctype = context.get_parameter("ctype")
    msg = context.get_parameter("msg")
    receiver = context.get_parameter("receiver")

    if ctype not in [CHAT_CHANNEL_WORLD, CHAT_CHANNEL_GROUP, CHAT_CHANNEL_PRIVATE]:
        context.result["mc"] = MsgCode["ParamIllegal"]
        return

    if ctype == CHAT_CHANNEL_WORLD:
        if ki_user.ext_info.ban_chat and ki_user.ext_info.ban_chat > int(time.time()):
            context.result["mc"] = MsgCode["InvalidOperation"]
            return

        used_times = ki_user.daily_info.world_chat_times
        vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level, {})
        if used_times >= vip_cfg["daily_world_chat_times"] and not user_logic.check_game_values1(ki_user, diamond=WORLD_CHAT_EXTRA_DIAMOND):
            context.result["mc"] = MsgCode["DiamondNotEnough"]
            return

    elif ctype == CHAT_CHANNEL_GROUP and ki_user.group.group_id == 0:
        context.result["mc"] = MsgCode["UserHasNoGroup"]
        return

    elif ctype == CHAT_CHANNEL_PRIVATE and int(receiver) == 0:
        context.result["mc"] = MsgCode["ChatPrivateTargetEmpty"]
        return

    elif ctype == CHAT_CHANNEL_PRIVATE and str(receiver) == ki_user.uid:
        context.result["mc"] = MsgCode["ChatCantToSelf"]
        return

    else:
        pass

    sender = {}
    sender["uid"] = ki_user.uid
    sender["avatar"] = ki_user.avatar
    sender["name"] = ki_user.name
    sender["level"] = ki_user.game_info.role_level

    msg = gfw.replace(msg)

    if ctype != CHAT_CHANNEL_PRIVATE:
        ChatService.send(ki_user.sid, ctype, msg, sender, ki_user.group.group_id)
    else:
        ChatService.send(ki_user.sid, ctype, msg, sender, ki_user.group.group_id, receiver)

    if ctype == CHAT_CHANNEL_WORLD:
        ki_user.daily_info.world_chat_times += 1
        ki_user.daily_info.put()

        if ki_user.daily_info.world_chat_times > vip_cfg["daily_world_chat_times"]:
            user_logic.consume_game_values1(ki_user, diamond=WORLD_CHAT_EXTRA_DIAMOND)

    context.result["mc"] = MsgCode["ChatSendMsgSucc"]
