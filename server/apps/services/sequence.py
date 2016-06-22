#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-25 13:16:46
# @Author : Jiank (http://jiankg.github.com)
# @doc
#    序列号生成服务
# @end
# @copyright (C) 2015, kimech

from libs.rklib.core import app

from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

class Sequence(object):
    """唯一ID生成序列类
    """
    user_id_prefix = 10000000
    group_id_prefix = 10000
    mail_id_prefix = 1000000000
    chat_private_id_prefix = 1000000000

    def __init__(self):
        super(Sequence, self).__init__()

    @classmethod
    def generate_express_id(cls):
        return redis_client.hincrby(rediskey_config.ACCOUNT_EXPRESS_KEY, "sequence")

    @classmethod
    def generate_user_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "user_id")
        sequence = cls.user_id_prefix + int("%07d" % seq)

        return "%s%s" % (sid, sequence)

    @classmethod
    def generate_group_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "group_id")
        sequence = cls.group_id_prefix + int("%04d" % seq)

        return sequence

    @classmethod
    def generate_mail_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "mail_id")
        sequence = cls.mail_id_prefix + int("%09d" % seq)

        return "%s%s" % (sid, sequence)

    @classmethod
    def generate_chat_private_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "chat_private_id")
        sequence = cls.chat_private_id_prefix + int("%09d" % seq)

        return sequence

    @classmethod
    def generate_notice_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "notice_id")
        sequence = cls.chat_private_id_prefix + int("%09d" % seq)

        return sequence

    @classmethod
    def generate_arena_fight_log_id(cls, sid):
        seq = redis_client.hincrby(rediskey_config.SEQUENCE_KEY % sid, "arena_fight_id")
        sequence = cls.chat_private_id_prefix + int("%09d" % seq)

        return sequence
