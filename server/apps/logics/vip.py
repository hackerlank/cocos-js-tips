#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-29 19:46:56
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     vip业务接口
# @end
# @copyright (C) 2015, kimech

import time
import logging
from apps.misc import utils

from apps.configs import game_config
from apps.configs.msg_code import MsgCode
from apps.logics import package as pack_logic
from apps.logics import user as user_logic

from .helpers import act_helper
from .helpers import common_helper

from apps.models.account import Account

from apps.services import charge as charge_service
from apps.services.statistics import Statictics as stat_service

# 订单状态 0-未生效 1-未使用 2-已使用
ORDER_PREPARE = 0
ORDER_AVAILABLE = 1
ORDER_USED = 2

# ========================= GAME API ==============================
def info(context):
    """vip界面数据
    """
    ki_user = context.user

    context.result["data"] = {}
    context.result["data"]["bought_gifts"] = ki_user.vip.bought_gifts
    context.result["data"]["charged_index"] = ki_user.vip.charged_index

def charge(context):
    """充值接口

    Args:
        index 充值券编号

    Returns:

    """
    ki_user = context.user

    complete_account_id = "%s_%s" % (ki_user.platform, ki_user.account_id)
    account = Account.get_account(complete_account_id)
    if account.type == 2:
        context.result['mc'] = MsgCode['VipChargeTmpAccountCantCharge']
        return

    index = context.get_parameter("index")
    cfg = game_config.charge_cfg.get(index, {})
    if not cfg:
        context.result['mc'] = MsgCode['VipChargeIndexNotExist']
        return

    order = generate_charge_order(index, cfg["rmb"], ki_user)
    result = charge_service.insert_order(order)
    if not result:
        context.result['mc'] = MsgCode['VipChargeFailed']
        return

    try:
        stat_service.charge(ki_user.platform, ki_user.account_id, ki_user.uid, order["orderid"], order["price"], ORDER_PREPARE)
    except:
        logging.error("ERROR:【order status: 0 record charge log failed. 】")

    context.result["data"] = {}
    context.result["data"]["orderid"] = order["orderid"]
    context.result["data"]["money"] = cfg["rmb"]

def buy(context):
    """购买特权礼包

    Args:
        index 与vip相对应

    Returns:
        mc
    """
    ki_user = context.user

    index = context.get_parameter("index")
    if index > ki_user.game_info.vip_level:
        context.result['mc'] = MsgCode['UserVipTooLow']
        return

    # 只能买一次
    if utils.bit_test(ki_user.vip.bought_gifts, index):
        context.result['mc'] = MsgCode['VipGiftAlreadyBought']
        return

    cfg = game_config.vip_priv_cfg.get(index, {})
    if not cfg:
        context.result['mc'] = MsgCode['VipGiftNotExist']
        return

    if not user_logic.check_game_values1(ki_user, diamond=cfg["priv_gift_price"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    ki_user.vip.buy(index)
    pack_logic.add_items(ki_user, cfg["priv_gift"])
    user_logic.consume_game_values1(ki_user, diamond=cfg["priv_gift_price"])

    context.result['mc'] = MsgCode['VipGiftBuySuccess']

def refresh_pay(context):
    """充值成功后发送协议刷新元宝数据

    Args:

    Returns:

    """
    ki_user = context.user

    charge_money = charge_refresh(ki_user)

    # 返回前端最新的钻石信息，vip经验信息
    diamond = ki_user.game_info.diamond
    vip_exp = ki_user.game_info.vip_exp

    datas = {}
    datas["diamond"] = diamond
    datas["vip_exp"] = vip_exp
    datas["charge_money"] = charge_money

    context.result["data"] = datas

# ================================================================
def charge_refresh(player):
    """
    1.玩家每次登录时检测是否有已充值付款的订单，如果充值已完成 则加上响应元宝数
    2.玩家每次充值完收到支付成功时检测是否有已充值付款的订单，如果充值已完成 则加上响应元宝数
    """
    avalible_orders = charge_service.get_by_uid(player.uid, ORDER_AVAILABLE)

    if not avalible_orders:
        return

    total, rmb = 0, 0
    for order in avalible_orders:
        diamond, money = do_charge(order, player)
        total += diamond
        rmb += money

    try:
        act_helper.update_after_charge(player, int(total),  int(rmb))
    except:
        pass

    try:
        player.vip.update_card_when_charge(int(rmb))
    except:
        pass

    return rmb

def do_charge(order, player):
    # 判断额外赠送钻石
    index = order["charge_id"]
    cfg = game_config.charge_cfg.get(index)

    if int(order["charged_amount"]) != int(order["price"]):
        amount = int(order["charged_amount"])
        add_diamond = amount * 10
    else:
        amount = order["price"]
        extra = 0 if utils.bit_test(player.vip.charged_index, index) else cfg["first_extra"]
        add_diamond = amount * 10 + extra

    # 更新数据库里状态， 为防止出错玩家刷单  先更新 然后加元宝
    charge_service.update_order_comleted(order["orderid"])

    # 加元宝,加vip经验
    player.game_info.diamond += add_diamond
    player.game_info.add_vip_exp(amount * 10, instant_save=True)

    # 充值和应该充值符合时候才额外赠送
    if int(order["charged_amount"]) == int(order["price"]):
        player.vip.charge(index)

    player.game_info.put()
    charge_service.rem_uid_paid_set(player.uid) # 从已完成付费的集合中删除已经刷新钻石的玩家ID

    try:
        stat_service.charge(player.platform, player.account_id, player.uid, order["orderid"], amount, ORDER_USED)
    except:
        logging.error("ERROR:【order status: 2 record charge log failed. 】")

    return add_diamond, amount

def generate_charge_order(index, money, player):
    """生成充值订单
    """
    orderid = "%s_%s_%s_%s" % (player.sid, player.uid, money, int(time.time()*1000))

    order = {}
    order["orderid"] = orderid
    order["account_id"] = player.account_id
    order["uid"] = player.uid
    order["plat"] = player.platform
    order["sid"] = player.sid
    order["charge_id"] = index
    order["price"] = money
    order["status"] = ORDER_PREPARE
    # order["status"] = ORDER_AVAILABLE
    order["created_at"] = int(time.time())
    order["completed_at"] = 0

    return order
