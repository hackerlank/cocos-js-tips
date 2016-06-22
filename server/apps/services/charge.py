#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-10 11:15:58
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     物品兑换码服务
# @end
# @copyright (C) 2015, kimech

import copy
import time
import logging
import datetime

from libs.rklib.core import app
from torngas.settings_manager import settings

from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current
mysql_engine = app.get_storage_engine("mysql")

def add_uid_paid_set(uid):
    """把充值已付费的玩家uid放入集合 等待通知ta
    """
    redis_client.sadd(rediskey_config.CHARGE_PAID_SET_KEY, str(uid))

def ismember_of_paid_set(uid):
    """检查玩家是否在充值已付费名单中
    """
    result = redis_client.sismember(rediskey_config.CHARGE_PAID_SET_KEY, str(uid))

    return 1 if result else 0

def rem_uid_paid_set(uid):
    """玩家已经刷新了元宝，从集合中把uid删除掉
    """
    redis_client.srem(rediskey_config.CHARGE_PAID_SET_KEY, str(uid))

def insert_order(order):
    """插入新的充值订单

    Args:
        order 充值订单信息
    """
    try:
        params = copy.copy(order)
        # 为了方便查询  暂时不做分表
        # params["table_name"] = settings.CHARGE_ORDER_TABLE_NAME + datetime.date.today().strftime('%Y_%m')
        params["table_name"] = settings.CHARGE_ORDER_TABLE_NAME

        sql = "INSERT INTO  %(table_name)s (orderid, account_id, uid, plat, \
               sid, charge_id, price, status, created_at, completed_at) VALUES \
               ('%(orderid)s', '%(account_id)s', '%(uid)s', '%(plat)s', %(sid)s, \
               %(charge_id)s, %(price)s, %(status)s, %(created_at)s, %(completed_at)s)" % params

        mysql_engine.master_execute(sql)

        return True
    except Exception,e:
        logging.error(e)
        return False

def get_by_uid(uid, status):
    """根据玩家UID和订单状态获取订单

    """
    try:
        sql = "SELECT * FROM %s WHERE uid = '%s' AND status = %s;" % (settings.CHARGE_ORDER_TABLE_NAME, uid, status)
        results = mysql_engine.master_query(sql)

        return results
    except Exception,e:
        logging.error(e)

def get_by_orderid(orderid):
    """根据订单号获取订单
    """
    try:
        sql = "SELECT * FROM %s WHERE orderid = '%s';" % (settings.CHARGE_ORDER_TABLE_NAME, orderid)
        result = mysql_engine.master_get(sql)
        return result
    except Exception,e:
        logging.error(e)

def get_by_extra_data(ticket_id):
    """
        根据“订单在易接服务器上的订单号”取订单信息
        服务器根据tcd字段做排重处理,防止多次发放道具.如果重复的订单,返回SUCCESS。
    """
    try:
        sql = "SELECT * FROM %s WHERE extra = '%s';" % (settings.CHARGE_ORDER_TABLE_NAME, ticket_id)
        result = mysql_engine.master_get(sql)
        return result
    except Exception,e:
        logging.error(e)

def update_order_charged_amount(orderid, amount):
    """根据订单号修改订单实际充值金额，当实充金额大于订单金额时调用
    """
    try:
        sql = "UPDATE %s SET charged_amount = %s WHERE orderid = '%s'" % (settings.CHARGE_ORDER_TABLE_NAME, amount, orderid)
        mysql_engine.master_execute(sql)
        return True
    except Exception,e:
        logging.error(e)
        return False

def update_order_avalible(orderid, amount, extra=""):
    """根据订单号修改订单为【已成功付款】状态
    """
    try:
        if not extra:
            sql = "UPDATE %s SET status = 1, charged_amount = %s WHERE orderid = '%s'" % (settings.CHARGE_ORDER_TABLE_NAME, amount, orderid)
        else:
            sql = "UPDATE %s SET status = 1, charged_amount = %s, extra = '%s' WHERE orderid = '%s'" % (settings.CHARGE_ORDER_TABLE_NAME, amount, extra, orderid)

        mysql_engine.master_execute(sql)
        return True
    except Exception,e:
        logging.error(e)
        return False

def update_order_comleted(orderid):
    """根据订单号修改订单为【已交付货物】状态
    """
    try:
        sql = "UPDATE %s SET status = 2, completed_at = %s WHERE orderid = '%s'" % (settings.CHARGE_ORDER_TABLE_NAME, int(time.time()), orderid)
        mysql_engine.master_execute(sql)
        return True
    except Exception,e:
        logging.error(e)
        return False
