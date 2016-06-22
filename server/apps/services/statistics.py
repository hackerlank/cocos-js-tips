#!/usr/bin/env python
# encoding: utf-8

# @Date : 2015-07-18 11:10:29
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      登录dau统计，每日每个角色只记录一次
#                   平台/服务器/账户/角色ID/注册时间/最近登录时间/留存天数
#           format: DEV_account1/110000001/1448519912/1448519910/1
# @end
# @copyright (C) 2015, kimech

import time
import logging
import datetime

from torngas.settings_manager import settings

DAU_FORMATTER = ['account_id','uid','create_time','login_time','stay']
CHARGE_FORMATTER = ['account', 'plat', 'uid', 'orderid', 'money', 'status', 'time']

from libs.rklib.core import app
from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

class Statictics(object):
    """
    """
    DAU_LOG = logging.getLogger('statictics.dau')
    CHARGE_LOG = logging.getLogger('statictics.charge')

    def __init__(self):
        super(Statictics, self).__init__()

    @classmethod
    def dau(self, user):
        """日用户活跃，每个用户每日只记录一次
        """
        if settings.DEBUG:
            return

        try:
            try:
                # 留存天数
                stay = (datetime.date.today() - datetime.date.fromtimestamp(user.create_time)).days + 1
            except Exception:
                stay = 0

            data = {
                    'account_id':user.platform + "_" + user.account_id,
                    'uid':user.uid,
                    'create_time':user.create_time,
                    'login_time':int(time.time()),
                    'stay':stay
                }


            log = self.build_log_data(data, DAU_FORMATTER)
            self.DAU_LOG.info(log)

            self.active(user.sid, user.uid)

        except Exception, e:
            logging.error(e)

    @classmethod
    def charge(self, plat, account, uid, orderid, money, status):
        """用户充值日志

        1.生成订单日志
        2.付款结束，平台回调操作订单日志
        3.玩家刷新钻石，充值生效日志

        """
        if settings.DEBUG:
            return

        try:
            data = {
                    'account': account,
                    'plat': plat,
                    'uid': uid,
                    'orderid': orderid,
                    'money': money,
                    'status': status,
                    'time': time.strftime("%Y%m%d%H%M%S")
                }

            log = self.build_log_data(data, CHARGE_FORMATTER)
            self.CHARGE_LOG.info(log)
        except Exception, e:
            logging.error(e)

    @classmethod
    def level(self, user):
        """玩家的等级情况
        """
        try:
            redis_client.hset(rediskey_config.STAT_LEVEL_REDIS_KEY % user.sid, user.uid, user.game_info.role_level)
        except Exception, e:
            logging.error(e)

    @classmethod
    def guide(self, user):
        """玩家的引导进度情况
        """
        try:
            redis_client.hset(rediskey_config.STAT_GUIDE_REDIS_KEY % user.sid, user.uid, user.game_info.last_guide_id)
        except Exception, e:
            logging.error(e)

    @classmethod
    def mission(self, user, mission_id, mtype):
        """玩家的副本通关进度情况
        """
        try:
            redis_client.hset(rediskey_config.STAT_MISSION_REDIS_KEY % user.sid, user.uid, user.mission.missions.keys())
        except Exception, e:
            logging.error(e)

    @classmethod
    def regist(self, sid, uid):
        """ 【统计今日注册】
        """
        try:
            date = time.strftime("%Y%m%d")
            redis_client.sadd(rediskey_config.STAT_TODAY_REGIST_REDIS_KEY % (sid, date), uid)
        except Exception, e:
            logging.error(e)

    @classmethod
    def active(self, sid, uid):
        """ 【统计今日活跃】
        """
        try:
            date = time.strftime("%Y%m%d")
            redis_client.sadd(rediskey_config.STAT_TODAY_ACTIVE_REDIS_KEY % (sid, date), uid)
        except Exception, e:
            logging.error(e)

    @classmethod
    def online(self, sid, uid):
        """ 【统计当前在线】
            玩家在线签到。
            每个协议一次。
        """
        try:
            redis_client.zadd(rediskey_config.STAT_ONLINE_REDIS_KEY % sid, int(time.time()), uid)
        except Exception, e:
            logging.error(e)

    @staticmethod
    def build_log_data(data, formatter):
        """构造日志内容
        """
        delimiter = '/'
        record = []
        for item in formatter:
            record.append(data.get(item, ''))

        log = delimiter.join(map(str, record))

        return log
