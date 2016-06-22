#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-09-25 16:47:25
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   商店业务逻辑接口
#       1. 抽奖
#       2. 查看商店物品
#       3. 刷新商店物品
#       4. 购买商店物品
# @end
# @copyright (C) 2015, kimech

import copy
import time
import random
import logging
import datetime

from apps.misc import utils
from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from .helpers import act_helper
from .helpers import hero_helper
from .helpers import common_helper

from apps.logics import user as user_logic
from apps.logics import package as pack_logic

from apps.services.notice import NoticeService

# 商店ID映射表
MALL_MISC = 1
MALL_HONOR = 2
MALL_TRIAL = 3
MALL_GROUP = 4
MALL_MYSTERY = 5

# 觉醒碎片兑换
MALL_CHIP = 100

# 抽奖类型
PICK_TYPE_1 = 1    # 钻石单次
PICK_TYPE_2 = 2    # 钻石连抽
PICK_TYPE_3 = 3    # 钥匙单次
PICK_TYPE_4 = 4    # 钥匙连抽
PICK_TYPE_5 = 5    # 免费

# 随机类型
MALL_RAND_TYPE_1 = 1 # 免费
MALL_RAND_TYPE_2 = 2 # 钥匙单次抽取

############################################
MALL_RAND_TYPE_3 = 3 # 钥匙连抽普通
MALL_RAND_TYPE_4 = 4 # 钥匙连抽必得
############################################

MALL_RAND_TYPE_5 = 5 # 钻石单次抽取

############################################
MALL_RAND_TYPE_6 = 6 # 钻石连抽普通
MALL_RAND_TYPE_7 = 7 # 钻石连抽必得
############################################

REFRESH_CONSUME_DIAMOND = 20
REFRESH_CONSUME_DIAMOND_STEP = 10

# ========================= GAME API ==============================
def pick(context):
    """商店抽奖 - 装备觉醒石头

    Args:
        ptype 抽奖类型  1-单次 2-十连抽

    Returns:

    Raises:

    """
    ki_user = context.user

    ptype = context.get_parameter("ptype")

    if ptype not in [PICK_TYPE_1, PICK_TYPE_2]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    cur_package_len = len(ki_user.package.items)
    if cur_package_len >= pack_logic.PACKAGE_MAX_SLOTS:
        context.result['mc'] = MsgCode['PackageIsFull']
        return

    free = _is_pick_free(ki_user.daily_info.mall_pick_cd, ptype)

    final_type = _fix_pick_type(free, ptype, ki_user.game_info.box_key)

    if not final_type:
        context.result['mc'] = MsgCode['ServerInternalError']
        return

    cfg = game_config.mall_pick_cfg[final_type]
    if not pack_logic.check_items_enough(ki_user, cfg["consume"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 十连抽 or 单次
    loop_index = 0 if ptype == 1 else 9
    picked_items = []
    broadcast_list = []

    while loop_index >= 0:
        broadcast, lib = _get_pick_rand_lib(_pick_lib_type(final_type, loop_index))
        target = random.choice(lib)
        picked_items.append(target)
        if broadcast:
            broadcast_list += target.keys()

        loop_index -= 1

    picked_items_c2s = copy.copy(picked_items)
    picked_items.append(cfg["items"])
    final_items = common_helper.handle_pack_items(picked_items)

    # 加物品&扣除消耗品
    if not free:
        pack_logic.remove_items(ki_user, cfg["consume"])

    pack_logic.add_items(ki_user, final_items)   # 加抽到的物品

    # 更新数据
    if final_type == 5:
        ki_user.daily_info.mall_pick_cd = 1
        ki_user.daily_info.put()

    act_helper.update_after_mall_pick(ki_user, 1 if ptype == 1 else 10)

    # 炫耀
    try:
        for item_id in broadcast_list:
            trigger = {'uid': ki_user.uid, 'name': ki_user.name}
            NoticeService.broadcast(ki_user.sid, 14, trigger, item_id)
    except:
        logging.error("【商店获得物品】炫耀广播发生错误。")

    context.result["data"] = {}
    context.result["data"]["picked_items"] = picked_items_c2s

def info(context):
    """查询商店随机刷新的物品

    Args:
        mtype 商品类别  1-杂货 2-荣誉 3-试炼 4-社团

    Returns:

    Raises:

    """
    ki_user = context.user

    mtype = context.get_parameter("mtype")

    if mtype not in range(1,6):
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    info = None
    now = int(time.time())
    if mtype == MALL_MISC:
        info = ki_user.mall.misc
    elif mtype == MALL_HONOR:
        info = ki_user.mall.honor
    elif mtype == MALL_TRIAL:
        info = ki_user.mall.trial
    elif mtype == MALL_GROUP:
        info = ki_user.mall.group
    else:
        info = ki_user.mall.mystery
        # 神秘商店只能存在一个小时
        if now - info["last_refresh"] >= 3600:
            context.result['mc'] = MsgCode['MallMysteryExpired']
            return

    if mtype != MALL_MYSTERY:
        refresh_cfg = game_config.mall_refresh_cfg[mtype]
        refresh = _need_refresh(refresh_cfg["refreshes"], info["last_refresh"], now)
        if refresh:
            cfg = game_config.mall_cfg[mtype]
            new_random_list = _handle_refresh_action(cfg, ki_user.game_info.role_level)

            info["items"] = new_random_list
            info["last_refresh"] = now
            info["bought"] = []

            ki_user.mall.put()

    context.result["data"] = {}
    context.result["data"]["items"] = info["items"]
    context.result["data"]["bought"] = info["bought"]
    context.result["data"]["last_refresh"] = info["last_refresh"]

def refresh(context):
    """刷新某个商店的物品

    Args:
        mtype 商品类别  1-杂货 2-荣誉 3-试炼 4-社团

    Returns:

    Raises:

    """
    ki_user = context.user

    mtype = context.get_parameter("mtype")

    if mtype not in range(1,5):
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    refresh_times = ki_user.daily_info.mall_refresh_times.get(mtype, 0)
    consume = refresh_times * REFRESH_CONSUME_DIAMOND_STEP + REFRESH_CONSUME_DIAMOND

    if not user_logic.check_game_values1(ki_user, diamond=consume):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    info = None
    if mtype == MALL_MISC:
        info = ki_user.mall.misc
    elif mtype == MALL_HONOR:
        info = ki_user.mall.honor
    elif mtype == MALL_TRIAL:
        info = ki_user.mall.trial
    else:
        info = ki_user.mall.group

    cfg = game_config.mall_cfg[mtype]
    new_random_list = _handle_refresh_action(cfg, ki_user.game_info.role_level)

    user_logic.consume_game_values1(ki_user, diamond=consume)

    info["items"] = new_random_list
    info["bought"] = []
    ki_user.mall.put()

    ki_user.daily_info.update_mall_refresh_times(mtype)

    context.result["data"] = {}
    context.result["data"]["items"] = new_random_list

def buy(context):
    """购买某个商店的某个物品

    Args:
        mtype 商品类别  1-杂货 2-荣誉 3-试炼 4-社团 5-碎片兑换

    Returns:

    Raises:

    """
    ki_user = context.user

    mtype = context.get_parameter("mtype")
    item_tag = context.get_parameter("item_tag")

    if mtype not in [MALL_MISC, MALL_HONOR, MALL_TRIAL, MALL_GROUP, MALL_CHIP, MALL_MYSTERY]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    info = None
    if mtype == MALL_MISC:
        info = ki_user.mall.misc
    elif mtype == MALL_HONOR:
        info = ki_user.mall.honor
    elif mtype == MALL_TRIAL:
        info = ki_user.mall.trial
    elif mtype == MALL_GROUP:
        info = ki_user.mall.group
    elif mtype == MALL_MYSTERY:
        info = ki_user.mall.mystery
        # 神秘商店只能存在一个小时
        if int(time.time()) - info["last_refresh"] >= 3600:
            context.result['mc'] = MsgCode['MallMysteryExpired']
            return
    else:
        pass

    cfg = None
    if mtype in range(1,6):
        if item_tag not in info["items"]:
            context.result['mc'] = MsgCode['ParamIllegal']
            return

        if item_tag in info["bought"]:
            context.result['mc'] = MsgCode['MallItemSaleOut']
            return

        cfg = game_config.mall_tmp_cfg.get(item_tag, {})
    else:
        cfg = game_config.mall_shop_cfg.get(item_tag, {})

    if not cfg:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    if not pack_logic.check_items_enough(ki_user, cfg["consume"]):
        consume_type = cfg["consume"].keys()[0]
        if consume_type == 2:
            context.result['mc'] = MsgCode['DiamondNotEnough']
        else:
            context.result['mc'] = MsgCode['GoldNotEnough']

        return

    pack_logic.remove_items(ki_user, cfg["consume"])
    pack_logic.add_items(ki_user, cfg["item"])   # 加抽到的物品

    if mtype in range(1,6):
        info["bought"].append(item_tag)
        ki_user.mall.put()

    context.result["mc"] = MsgCode["MallBuySucc"]

# ====================================================================
def refresh_mission_mystery_shop(user):
    """刷新副本随机商店物品列表

    Args:
        user 角色数据

    """
    cfg = game_config.mall_cfg[5]
    item_list = _handle_refresh_action(cfg, user.game_info.role_level)

    now = int(time.time())
    info = {}
    info["items"] = item_list
    info["last_refresh"] = now
    info["bought"] = []

    user.mall.mystery = info
    user.mall.put()

    return now

def _is_pick_free(cd, ptype):
    """判断此次抽取是否免费

    连抽没有免费

    """
    if ptype == 2:
        return False
    else:
        if not cd:
            return True
        else:
            return False

def _fix_pick_type(free, ptype, box_key):
    """纠正抽卡类型

    本身只有单次和批量两种类型，但使用钥匙衍生出两种，再加第五种免费

    1 - 钻石单次
    2 - 钻石批量
    3 - 钥匙单次
    4 - 钥匙批量
    5 - 免费

    """
    final_type = 0
    if ptype == PICK_TYPE_1 and free:
        final_type = PICK_TYPE_5
    elif ptype == PICK_TYPE_1 and box_key >= 1:
        final_type = PICK_TYPE_3
    elif ptype == PICK_TYPE_1 and box_key == 0:
        final_type = PICK_TYPE_1
    elif ptype == PICK_TYPE_2 and box_key >= 10:
        final_type = PICK_TYPE_4
    elif ptype == PICK_TYPE_2 and box_key < 10:
        final_type = PICK_TYPE_2
    else:
        pass

    return final_type

def _pick_lib_type(final_type, loop_index):
    """

    # 随机类型
    MALL_RAND_TYPE_1 = 1 # 免费
    MALL_RAND_TYPE_2 = 2 # 钥匙单次抽取
    MALL_RAND_TYPE_3 = 3 # 钥匙连抽普通
    MALL_RAND_TYPE_4 = 4 # 钥匙连抽必得
    MALL_RAND_TYPE_5 = 5 # 钻石单次抽取
    MALL_RAND_TYPE_6 = 6 # 钻石连抽普通
    MALL_RAND_TYPE_7 = 7 # 钻石连抽必得

    """
    if final_type == PICK_TYPE_1:
        return MALL_RAND_TYPE_5
    elif final_type == PICK_TYPE_2:
        return 109 - loop_index
    elif final_type == PICK_TYPE_3:
        return MALL_RAND_TYPE_2
    elif final_type == PICK_TYPE_4:
        return 209 - loop_index
    else:
        return MALL_RAND_TYPE_1

def _get_pick_rand_lib(rand_type):
    """获得随机类型对应的随机库

    Args:
        rand_type 随机类型 12种

    Return:
        {120000: 12}

    """
    cfgs = game_config.mall_pick_rand_cfg
    rand_list = filter(lambda x: x["type"] == rand_type, cfgs.itervalues())

    rand_list = sorted(rand_list, key=lambda x:x["weight"], reverse = True)
    rand_sum = sum([item["weight"] for item in rand_list])

    rand = random.randint(0, rand_sum)

    for item in rand_list:
        rand -= item["weight"]
        if rand <= 0:
            return item["broadcast"], item["libs"]

def _handle_refresh_action(cfg, role_level):
    """刷新操作

    """
    new_random_list = []
    for i in range(1, len(cfg)+1):
        slot_cfg = cfg[i]
        libs = [{item["id"]: item["weight"]} for item in slot_cfg if item["level_limit"]["min"] <= role_level <= item["level_limit"]["max"]]
        rand_libs = []
        for a in libs:
            rand_libs.append(a)

        target = common_helper.weight_random(pack_logic.amend_goods(rand_libs))
        new_random_list.append(target)

    return new_random_list

def _need_refresh(refresh_points, last_refresh, now):
    """
    """
    cur_hour = datetime.datetime.fromtimestamp(now).hour
    last_should_refresh = max([i for i in refresh_points if i[0] <= cur_hour])
    last_should_refresh_hour = last_should_refresh[0]
    last_refresh_hour = datetime.datetime.fromtimestamp(last_refresh).hour

    last_should_refresh_ts = utils.datestamp(utils.timestamp2string(now)) + last_should_refresh_hour * 3600
    if last_refresh_hour < last_should_refresh_hour:
        return True
    else:
        return True if last_refresh < last_should_refresh_ts else False
