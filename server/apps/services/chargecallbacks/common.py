#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2016-01-15 13:30:59
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      游戏充值回调接口
# @end
# @copyright (C) 2015, kimech

import time
import logging

from apps.services import charge as charge_service
from apps.services.statistics import Statictics as stat_service

cErrorLog = logging.getLogger('statictics.charge_error')

def handle_order_data(plat_order):
    """平台验证完毕，游戏服务器内部处理订单状态数据
    """
    orderid = plat_order["orderid"]

    order = charge_service.get_by_orderid(orderid)
    if not order:
        charge_error_log(plat_order["plat"], orderid, "cant be found in the mysql database")
        return False

    if order["status"] != 0:
        return True

    # 实际充值金额不等于生成订单时的金额
    # if plat_order["amount"] != order["price"]:
    #     result = charge_service.update_order_charged_amount(orderid, plat_order["amount"])
    #     if not result:
    #         charge_error_log(plat_order["plat"], orderid, "update charged amount failed when real amount [%s] != original amount" % plat_order["amount"])
    #         return False

    result = charge_service.update_order_avalible(orderid, plat_order["amount"], plat_order.get("extra", ""))
    if not result:
        charge_error_log(plat_order["plat"], orderid, "update order status to avalible failed")
        return False
    else:
        try:
            # 更新数据库订单状态成功，把玩家uid放入一个心跳会检测是否有充值信息的队列，提醒玩家刷新元宝
            charge_service.add_uid_paid_set(order["uid"])
            stat_service.charge(plat_order["plat"], plat_order["account"], plat_order["uid"], orderid, plat_order["amount"], 1)
        except Exception,e:
            logging.error("ERROR:【order status: 1 record charge log failed. 】REASON: %s" % e)

    return True

def charge_error_log(plat, orderid, msg):
    """充值回调失败日志输出

    Args:
        plat 来自平台
        msg 失败原因
        orderid 服务器存储的订单ID
    """
    error_time = time.strftime("%Y-%m-%d %H:%M:%S")
    cErrorLog.error("Time: [ %s ] Platfrom: [ %s ] OrderId: [ %s ] Msg: %s." % (error_time, plat, orderid, msg))
