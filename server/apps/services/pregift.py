#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-25 13:16:46
# @Author : Jiank (http://jiankg.github.com)
# @doc
#    测试阶段达标奖励发送
#       1. 4.13 ios越狱删档测试 充值返现[下次测试开服前7日返还上次测试中的150%,剩余350%的钻石在剩下的53天分次返还。]
# @end
# @copyright (C) 2015, kimech

import math
from libs.rklib.core import app

from apps.configs import static_const
from apps.configs import rediskey_config
from apps.configs import game_config
from apps.services.mail import MailService
from torngas.settings_manager import settings

redis_client = app.get_storage_engine('redis').client.current

def payback_diamonds(sid, plat, account_id, uid, login_days):
    """4.13 ios越狱删档测试 充值返现

        走邮件形式发送
    """
    if int(sid) not in (1,2) or login_days > 60:
        return

    payback_amount = redis_client.hget(rediskey_config.ACT_PAYBACK_KEY % sid, "%s_%s" % (plat, account_id))
    if not payback_amount:
        return
    else:
        payback_amount = int(payback_amount)
        if 0 < login_days <= 7:
            get = int(math.ceil(payback_amount * 15.0 / 7))
            left = payback_amount * 50 - get * login_days
        else:
            get = int(math.ceil(payback_amount * 35.0 / 53))
            left = payback_amount * 35 - get * (login_days - 7)

        left = left if left >= 0 else 0

        # 第一次返还的时候 所有的vip经验都返还
        awards = {static_const.DIAMOND: get}
        if login_days == 1:
            awards = {static_const.DIAMOND: get, static_const.VIP_EXP: payback_amount * 10}

        MailService.send_game(uid, 3006, [get, left, 60 - login_days], awards)

def uc_qihoo_test_award_4003(sid, plat, account_id):
    """测试期间，最终等级达到X级
    """
    act_id = 4003
    level = redis_client.hget(rediskey_config.UC_QIHOO_TEST_AWARD_4003_KEY % sid, "%s_%s" % (plat, account_id))
    if not level:
        return {}, 0
    else:
        tmp,tmp1 = {},0
        for i in game_config.act_sample_detail_cfg[act_id]:
            cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, i))
            if i > tmp1 and int(level) >= cfg["cond_a"]:
                tmp,tmp1 = cfg["awards"],i

        return tmp, int(level)

def uc_qihoo_test_award_4004(sid, plat, account_id):
    """测试期间，累计登录X天，送奖励
    """
    act_id = 4004
    login_days = redis_client.hget(rediskey_config.UC_QIHOO_TEST_AWARD_4004_KEY % sid, "%s_%s" % (plat, account_id))
    if not login_days:
        return {},0
    else:
        tmp,tmp1 = {},0
        for i in game_config.act_sample_detail_cfg[act_id]:
            cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, i))
            if i > tmp1 and int(login_days) >= cfg["cond_a"]:
                tmp,tmp1 = cfg["awards"],i

        return tmp, int(login_days)

def uc_qihoo_test_award_4005(sid, plat, account_id):
    """测试期间，竞技场最终排名奖励
    """
    act_id = 4005
    rank = redis_client.hget(rediskey_config.UC_QIHOO_TEST_AWARD_4005_KEY % sid, "%s_%s" % (plat, account_id))
    if not rank:
        return {},0
    else:
        tmp,tmp1 = {},max(game_config.act_sample_detail_cfg[act_id])+1
        for i in game_config.act_sample_detail_cfg[act_id]:
            cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, i))
            if tmp1 > i and int(rank) <= cfg["cond_a"]:
                tmp,tmp1 = cfg["awards"],i

        return tmp,int(rank)
