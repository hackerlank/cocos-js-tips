#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 10:32:37
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     邮件服务器
# @end
# @copyright (C) 2015, kimech

import time
import copy
import datetime

import cPickle as pickle

from libs.rklib.core import app

from sequence import Sequence
from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

MAIL_TYPE_GAME = 1
MAIL_TYPE_SYSTEM = 2

class MailService(object):
    """邮件服务
    """
    def __init__(self):
        super(MailService, self).__init__()

    @classmethod
    def send_system(cls, ids, title, fromwho, msg, attachments):
        """发送系统运维邮件

        Args:
            ids 接收邮件的玩家uid列表 []
            title 邮件标题  str
            fromwho 发件人 str
            mtype 邮件类型 int
            msg 邮件内容 str
            attachments 附件 {}
        """
        mail = {}

        mail["type"] = MAIL_TYPE_SYSTEM
        mail["title"] = title
        mail["from"] = fromwho
        mail["msg"] = msg
        mail["attachments"] = attachments

        for uid in ids:
            cls.send(uid, mail)

    @classmethod
    def send_game(cls, uid, temp_id, datas, attachments):
        """发送正常游戏功能邮件

        Args:
            uid 接收邮件的玩家uid
            temp_id 邮件模板ID
            datas 关联数据
            attachments 附件 {}
        """
        mail = {}

        mail["type"] = MAIL_TYPE_GAME
        mail["temp_id"] = temp_id
        mail["datas"] = datas
        mail["attachments"] = attachments

        cls.send(uid, mail)

    @classmethod
    def get_user_mails(cls, uid):
        """
        """
        new_mails = cls.query_mails(uid, 0)
        old_mails = cls.query_mails(uid, 1)

        return new_mails, old_mails

    @classmethod
    def query_mails(cls, uid, mtype):
        """读取邮件

            mtype 1-已读邮件 0-新邮件
        """
        if mtype:
            user_mail_box_key = rediskey_config.MAIL_REPERTORY_OLD_PREFIX % uid
        else:
            user_mail_box_key = rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid

        targets = []
        mails = redis_client.hgetall(user_mail_box_key)
        now = datetime.datetime.now()
        for k,v in mails.items():
            dencoded_mail = pickle.loads(v)
            if mtype and (now - datetime.datetime.utcfromtimestamp(dencoded_mail["read"])).days <= 3:
                targets.append(dencoded_mail)
            elif not mtype and (now - datetime.datetime.utcfromtimestamp(dencoded_mail["create"])).days <= 7:
                targets.append(dencoded_mail)
            else:
                redis_client.hdel(user_mail_box_key, k)

        return targets

    @classmethod
    def get_attachments(cls, uid, mail_id):
        """读取邮件内容

        Args:
            mail_id 邮件的唯一ID
        """
        new_mail_box_key = rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid
        mail = redis_client.hget(new_mail_box_key, str(mail_id))
        if mail:
            dencoded_mail = pickle.loads(mail)
            return dencoded_mail["attachments"]
        else:
            return {}

    @classmethod
    def update_mail_state(cls, uid, mail_id, state):
        """读取邮件内容

        新邮件如果有附件未领取  则还是新邮件状态

        Args:
            mail_id 邮件的唯一ID

        Returns:

        """
        new_mail_box_key = rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid
        mail = redis_client.hget(new_mail_box_key, str(mail_id))
        if not mail:
            return

        dencoded_mail = pickle.loads(mail)
        # 如果附件不为空，并且新状态不为已领取的话 邮件还是新邮件
        if dencoded_mail["attachments"] and state != 2:
            return

        try:
            # 从新列表中删除，加入已读列表
            redis_client.hdel(new_mail_box_key, str(mail_id))

            dencoded_mail["read"] = time.time()
            old_mail_box_key = rediskey_config.MAIL_REPERTORY_OLD_PREFIX % uid
            redis_client.hset(old_mail_box_key, mail_id, pickle.dumps(dencoded_mail))
            # 已读列表只保留20封邮件，注意这里有个坑：正确做法应该是按照读取时间排序 取最后读的20个 而不是按照mail_id排序 目前不改了！
            old_mail_ids = redis_client.hkeys(old_mail_box_key)
            old_mail_ids.sort()

            for expired_mail_id in old_mail_ids[:-20]:
                redis_client.hdel(old_mail_box_key, expired_mail_id)

        except Exception,e:
            raise e

    @classmethod
    def check_mail_state(cls, uid, mail_id):
        """检测玩家某邮件状态

        可能邮件不存在

        Args:
            mail_id 邮件的唯一ID

        """
        new_mail_box_key = rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid
        old_mail_box_key = rediskey_config.MAIL_REPERTORY_OLD_PREFIX % uid

        if redis_client.hexists(new_mail_box_key, str(mail_id)):
            return 0
        elif redis_client.hexists(old_mail_box_key, str(mail_id)):
            return 1
        else:
            return None

    @staticmethod
    def send(uid, mail):
        """发送邮件
        """
        # 根据玩家ID特殊服务器标示位确定服务器ID
        new_mail_id = Sequence.generate_mail_id(uid[:-8])
        mail.update({"mail_id": new_mail_id, "create": time.time(), "read": 0})
        new_mail_box_key = rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid

        try:
            redis_client.hset(new_mail_box_key, new_mail_id, pickle.dumps(mail))
            new_mails = redis_client.hkeys(new_mail_box_key)
            # 新邮件保留五十封，过期的自动删除
            new_mails.sort()
            for expired_mail_id in new_mails[:-50]:
                redis_client.hdel(new_mail_box_key, expired_mail_id)
        except Exception,e:
            raise e
