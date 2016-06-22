#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 10:32:37
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     聊天服务器
# @end
# @copyright (C) 2015, kimech

import time
import datetime
import cPickle as pickle

from name import gfw
from group import GroupService
from apps.logics import user as user_logic
from apps.configs import rediskey_config
from sequence import Sequence
from libs.rklib.core import app

CHAT_CHANNEL_WORLD = 1
CHAT_CHANNEL_GROUP = 2
CHAT_CHANNEL_NOTICE = 3
CHAT_CHANNEL_PRIVATE = 4

CHAT_WORLD_MAX_NUM = 100
CHAT_NOTICE_MAX_NUM = 100
CHAT_GROUP_MAX_NUM = 100

redis_client = app.get_storage_engine('redis').client.current

# 私聊过期时间24小时
PRIVATE_CHAT_EXPIRED = 86400

class ChatService(object):
    """聊天服务
    """
    def __init__(self):
        super(ChatService, self).__init__()

    # @classmethod
    # def print_info(cls, group_id, uid):
    #     """
    #     """
    #     tmp_msgs = redis_client.lrange(rediskey_config.CHAT_WORLD_BOX_KEY % sid, 0, CHAT_WORLD_MAX_NUM)
    #     msgs = map(lambda x:pickle.loads(x), tmp_msgs)
    #     print "WORLD:"
    #     print msgs

    #     gtmp_msgs = redis_client.hget(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id)
    #     gmsgs = pickle.loads(gtmp_msgs) if gtmp_msgs else []
    #     print "GROUP:"
    #     print gmsgs

    #     private_msg_id_list = redis_client.hget(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid)
    #     print private_msg_id_list
    #     pmsgs = []
    #     if private_msg_id_list:
    #         private_msg_id_list = pickle.loads(private_msg_id_list)
    #         for msg_id in private_msg_id_list:
    #             msg = redis_client.hget(rediskey_config.CHAT_PRIVATE_POOL_KEY % sid, msg_id)
    #             pmsgs.append(pickle.loads(msg))

    #     print "PRIVATE:"
    #     print pmsgs

    @classmethod
    def get_chat_msgs(cls, sid, ctype, start, end, uid="", group_id=0):
        """获取聊天内容

        Args:
            ctype: 聊天类型
            last_read_time: 上次读取聊天信息的时间戳
            uid: 玩家ID，私聊信息
            group_id: 帮派ID，公会聊天
        """
        msgs = []
        if ctype == CHAT_CHANNEL_WORLD:
            tmp_msgs = redis_client.lrange(rediskey_config.CHAT_WORLD_BOX_KEY % sid, 0, CHAT_WORLD_MAX_NUM)
            msgs = map(lambda x:pickle.loads(x), tmp_msgs)

        elif ctype == CHAT_CHANNEL_GROUP:
            tmp_msgs = redis_client.hget(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id)
            if tmp_msgs:
                msgs = pickle.loads(tmp_msgs)

        elif ctype == CHAT_CHANNEL_NOTICE:
            tmp_msgs = redis_client.lrange(rediskey_config.CHAT_NOTICE_BOX_KEY % sid, 0, CHAT_NOTICE_MAX_NUM)
            msgs = map(lambda x:pickle.loads(x), tmp_msgs)

        elif ctype == CHAT_CHANNEL_PRIVATE:
            private_msg_id_list = redis_client.hget(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid)
            if private_msg_id_list:
                private_msg_id_list = pickle.loads(private_msg_id_list)
                private_msg_id_list.reverse()
                for msg_id in private_msg_id_list[start-1:end]:
                    msg = redis_client.hget(rediskey_config.CHAT_PRIVATE_POOL_KEY % sid, msg_id)
                    msgs.append(pickle.loads(msg))

        else:
            pass

        target_msgs = msgs[start-1:end]
        target_msgs.sort(key=lambda x:x["send_time"], reverse=True)

        return target_msgs

    @classmethod
    def send(cls, sid, ctype, msg, sender, group_id=None, to_who=None):
        """发言
        """
        send_time = int(time.time())

        # 处理敏感字符
        msg = gfw.replace(msg)

        chat_msg = {}
        chat_msg["send_time"] = send_time
        chat_msg["msg"] = msg

        if ctype == CHAT_CHANNEL_NOTICE:
            redis_client.lpush(rediskey_config.CHAT_NOTICE_BOX_KEY % sid, pickle.dumps(chat_msg))
            if redis_client.llen(rediskey_config.CHAT_NOTICE_BOX_KEY % sid) > CHAT_NOTICE_MAX_NUM:
                redis_client.ltrim(rediskey_config.CHAT_NOTICE_BOX_KEY % sid, 0, CHAT_NOTICE_MAX_NUM - 1)
        else:
            group_name = GroupService.get_name_by_id(sid, group_id)
            sender["group_name"] = group_name
            chat_msg["sender"] = sender

            if ctype == CHAT_CHANNEL_WORLD:
                redis_client.lpush(rediskey_config.CHAT_WORLD_BOX_KEY % sid, pickle.dumps(chat_msg))
                if redis_client.llen(rediskey_config.CHAT_WORLD_BOX_KEY % sid) > CHAT_WORLD_MAX_NUM:
                    redis_client.ltrim(rediskey_config.CHAT_WORLD_BOX_KEY % sid, 0, CHAT_WORLD_MAX_NUM - 1)

            elif ctype == CHAT_CHANNEL_GROUP:
                group_chat_box = redis_client.hget(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id)
                if group_chat_box is None:
                    redis_client.hset(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id, pickle.dumps([chat_msg]))
                else:
                    box = pickle.loads(group_chat_box)
                    box.append(chat_msg)
                    if len(box) > CHAT_GROUP_MAX_NUM:
                        final_box = box[-CHAT_GROUP_MAX_NUM:]
                        redis_client.hset(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id, pickle.dumps(final_box))
                    else:
                        redis_client.hset(rediskey_config.CHAT_GROUP_BOX_KEY % sid, group_id, pickle.dumps(box))

            elif ctype == CHAT_CHANNEL_PRIVATE:
                user_info = user_logic.fetch_user_info(to_who)
                chat_msg["receiver"] = user_info["name"] if user_info else ""

                msg_id = Sequence.generate_chat_private_id(sid)
                redis_client.hset(rediskey_config.CHAT_PRIVATE_POOL_KEY % sid, msg_id, pickle.dumps(chat_msg))

                # 把私聊信息扔到一个大池子里，留一个编号让发信息和接受信息的人都记住，凭着号去取聊天信息
                for uid in [sender["uid"], to_who]:
                    private_box = redis_client.hget(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid)
                    if private_box is None:
                        redis_client.hset(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid, pickle.dumps([msg_id]))
                    else:
                        box = pickle.loads(private_box)
                        box.append(msg_id)
                        redis_client.hset(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid, pickle.dumps(box))
            else:
                pass

    @classmethod
    def get_private_msgs(self, sid, uid, start):
        """查询start这个时间戳之后是否有玩家uid的私聊信息
        """
        msgs = []
        private_msg_id_list = redis_client.hget(rediskey_config.CHAT_PRIVATE_BOX_KEY % sid, uid)
        if private_msg_id_list:
            private_msg_id_list = pickle.loads(private_msg_id_list)
            private_msg_id_list.reverse()
            for msg_id in private_msg_id_list:
                msg = redis_client.hget(rediskey_config.CHAT_PRIVATE_POOL_KEY % sid, msg_id)
                real_msg = pickle.loads(msg)
                if real_msg["send_time"] >= start and real_msg["receiver"] == uid:
                    msgs.append(real_msg)

        return msgs
