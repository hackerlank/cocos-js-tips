#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 15:14:28
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      背包道具业务逻辑:
#       0.显示
#       1.使用物品
# @end
# @copyright (C) 2015, kimech

import copy
import logging

from apps.configs import game_config
from apps.configs import static_const
from apps.configs.msg_code import MsgCode
from apps.services.notice import NoticeService

from apps.logics.helpers import common_helper

import apps.logics.user as user_logic

PACKAGE_MAX_SLOTS = 999

# ========================= GAME API ==============================
def use(context):
    """玩家使用道具

    玩家使用背包里的道具

    Args:
        context: KiRequestContext类，处理一次请求所需要的数据。
        items  使用道具dict

    Returns:
        MsgCode['PackageItemUseSucc']     使用成功
        MsgCode['PackageItemNotExist']    道具不存在
        MsgCode['PackageItemNotEnough']    数量不足
        MsgCode['PackageItemNotAvailable']  道具不可用

    Raises:

    """
    ki_user = context.user

    items = context.get_parameter("items", "{}")
    try:
        items = eval(items)
        if not isinstance(items, dict):
            raise 1

        for v in items.values():
            if v <= 0:
                raise e
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    for item_id, num in items.items():
        cfg = game_config.item_cfg.get(int(item_id))
        if cfg["type"] not in [6,7]:
            context.result['mc'] = MsgCode['PackageItemNotAvailable']
            return
        else:
            item_num = ki_user.package.get_item_num_by_id(int(item_id))
            if item_num < num:
                context.result['mc'] = MsgCode['PackageItemNotEnough']
                return

    use_items = sum([[item] * num for item,num in items.items()], [])

    goods = []
    level_area = max([i for i in range(0,100,10) if ki_user.game_info.role_level >= i])
    for item in use_items:
        cfg = game_config.item_cfg.get(item)
        ex_cfg = game_config.item_exchange_cfg.get(cfg["items"])
        target = common_helper.weight_random(ex_cfg["lib_%s" % level_area])
        goods.append(copy.deepcopy(game_config.item_pack_cfg.get(target)))

    goods = amend_goods(goods)

    # 扣除物品
    remove_items(ki_user, items)

    # 添加物品
    if goods:
        add_items(ki_user, goods)

    context.result['mc'] = MsgCode['PackageItemUseSucc']
    context.result['data'] = {"goods": goods}

def sale(context):
    """出售道具

    玩家出售背包里的道具

    Args:
        context: KiRequestContext类，处理一次请求所需要的数据。
        items  出售道具dict

    Returns:
        MsgCode['PackageItemUseSucc']     使用成功
        MsgCode['PackageItemNotExist']    道具不存在
        MsgCode['PackageItemNotEnough']    数量不足

    Raises:

    """
    ki_user = context.user

    items = context.get_parameter("items", "{}")
    try:
        items = eval(items)
        if not isinstance(items, dict):
            raise 1

        for v in items.values():
            if v <= 0:
                raise e
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    total_price = 0
    for item_id, num in items.items():
        cfg = game_config.item_cfg.get(int(item_id))
        if not cfg["can_sale"]:
            context.result['mc'] = MsgCode['PackageItemNotSold']
            return
        else:
            item_num = ki_user.package.get_item_num_by_id(int(item_id))
            if item_num < num:
                context.result['mc'] = MsgCode['PackageItemNotEnough']
                return

        total_price += cfg["sale_price"] * num

    # 扣除物品
    remove_items(ki_user, items)
    # 添加物品
    add_items(ki_user, {1: total_price})

    context.result['mc'] = MsgCode['PackageItemSaleSucc']

def express_buy(context):
    """快捷购买通道

    Args:
        item_id
        item_num

    Returns:

    """
    ki_user = context.user

    item_id = context.get_parameter("item_id")
    item_num = context.get_parameter("item_num")

    if item_num < 0 or item_num > 100:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cfg = game_config.item_cfg.get(item_id)
    if ki_user.game_info.role_level < cfg["need_level"]:
        context.result['mc'] = MsgCode['UserLevelTooLow']
        return

    need_diamond = cfg["buy_price"] * item_num
    if not user_logic.check_game_values1(ki_user, diamond=need_diamond):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    user_logic.consume_game_values1(ki_user, diamond=need_diamond)
    add_items(ki_user, {item_id: item_num})

    context.result["mc"] = MsgCode['PackageExpressBuySucc']

# ========================= MODULE API =============================
def add_items(user, items):
    """新增道具

    Args:
        user 用户对象
        items 道具字典, eg: {71001:2, 71003:3}
    """
    # 类似金币，钻石，经验，vip经验，荣誉等特殊道具类型，特殊添加处理
    special_items = {}
    normal_items = {}
    heros = []

    for item_id, num in items.iteritems():
        if item_id in static_const.SPECIAL_ITEMS_LIST:
            special_items[item_id] = num
        elif item_id in game_config.hero_base_cfg:
            heros.append({item_id: num})
        else:
            normal_items[item_id] = num

    if heros:
        import apps.logics.hero as hero_logic
        hero_logic.add_heros(user, heros)

    if special_items:
        user_logic.add_game_values(user, special_items)

    if normal_items:
        broadcast_list = []
        for k,v in normal_items.iteritems():
            if int(k) in game_config.item_cfg:
                user.package.add(k, v)
                if game_config.item_cfg[k]["broadcast"]:
                    broadcast_list.append(k)

        # 炫耀觉醒碎片
        try:
            for item_id in broadcast_list:
                trigger = {'uid': user.uid, 'name': user.name}
                NoticeService.broadcast(user.sid, 19, trigger, item_id)
        except:
            logging.error("【武器觉醒碎片】炫耀广播发生错误。")

        user.package.put()

def remove_items(user, items):
    """移除N个道具

    Args:
        user 用户对象
        items 道具字典, eg: {71001:2, 71003:3}
    """
    # 类似金币，钻石，经验，vip经验，荣誉等特殊道具类型，特殊扣除处理
    special_items = {}
    normal_items = {}

    for item_id, num in items.iteritems():
        if item_id in static_const.SPECIAL_ITEMS_LIST:
            special_items[item_id] = num
        else:
            normal_items[item_id] = num

    if normal_items:
        for k,v in normal_items.iteritems():
            user.package.remove(k, v)

        user.package.put()

    if special_items:
        user_logic.consume_game_values(user, special_items)

def check_items_enough(user, items):
    """检查道具是否足够

    Args:
        user 用户对象
        items 道具字典, eg: {71001:2, 71003:3}
    """
    _result_list = []
    # 类似金币，钻石，经验，vip经验，荣誉等特殊道具类型，特殊检测处理
    special_items = {}

    for item_id, num in items.iteritems():
        if item_id in static_const.SPECIAL_ITEMS_LIST:
            special_items[item_id] = num
        else:
            item_num = user.package.get_item_num_by_id(item_id)
            _result_list.append(item_num >= num)

    if special_items:
        spec_result = user_logic.check_game_values(user, special_items)
        _result_list.append(spec_result)

    return False if False in _result_list else True

def amend_goods(datas):
    """修正数据结构，方便使用

    [{10001:1, 10002:2}, {10002:1, 10003:2}] -> {10001: 1, 10002: 3, 10003: 2}

    """
    if not datas:
        return {}
    else:
        l = []
        for i in datas:
            l += i.items()

        d = {}
        for j in l:
            if j[0] not in d:
                d[j[0]] = j[1]
            else:
                d[j[0]] += j[1]

        return d
