#!/usr/bin/env python
# encoding: utf-8

import time
import logging
import hashlib

from urllib import unquote

from .common import handle_order_data
from .common import charge_error_log

from apps.services import charge as charge_service
from torngas.settings_manager import settings

# =========== 签名方法 END ========================
def pay_callback(handler):
    """
        trade_no=100200001021515540800fGRiknoq1h4 //订单号
        cpid=201 // cpid
        game_seq_num=1//游戏序列号
        server_seq_num=1//服务器序列号
        amount=0.01//充值金额，单位元
        user_id=1 //充值用户
        role_id=13234//角色id
        timestamp=20160222173243//当前请求的时间
        verstring=81577b7da20cd69bff67585b946170ef
    """
    params = dict.fromkeys([
        "trade_no",
        "cpid",
        "game_seq_num",
        "server_seq_num",
        "amount",
        "user_id",
        "role_id",
        "timestamp",
        "verstring",
        "ext_info",
        "remark",
        ], '')

    logging.info("params:%s" % handler.request.arguments)

    for i in params:
        params[i] = handler.get_argument(i, "")

    decoded_info = unquote(params["ext_info"])
    decoded_info1 = decoded_info.split("&")
    decoded_info2 = {}

    for i in decoded_info1:
        i1 = i.split("=")
        if len(i1) == 2:
            decoded_info2[i1[0]] = i1[1]

    if not decoded_info2:
        charge_error_log("WHWJ", decoded_info2.get("order_id", ""), "mine order is not exist")
        return "FAIL"

    app_cfg = settings.PLATFORM_APP_ID_MAPPING.get("WHWJ", {})
    if not app_cfg:
        charge_error_log("WHWJ", decoded_info2.get("order_id", ""), "app_cfg is null")
        return "FAIL"

    try:
        # 兄弟啊，这不是我们的充值订单，不要拿我作宝搞啊。
        if int(params["cpid"]) != app_cfg["AppId"]:
            return "SUCCESS"

        query_str = "trade_no=%(trade_no)s&cpid=%(cpid)s&game_seq_num=%(game_seq_num)s&server_seq_num=%(server_seq_num)s&amount=%(amount)s&user_id=%(user_id)s&role_id=%(role_id)s&timestamp=%(timestamp)s" % params
        safe_sign = hashlib.md5(query_str+"&SecretKey=%s" % app_cfg["PayKey"]).hexdigest()

        if safe_sign != params['verstring']:
            charge_error_log("WHWJ", decoded_info2.get("order_id", ""), "safe_sign != params['sign']")
            return "FAIL"

        dealed_data = charge_service.get_by_extra_data(params["trade_no"])
        if dealed_data:
            return "SUCCESS"  # 已经处理过的订单，除重

        order = {"plat": "WHWJ", "account": params["user_id"], "uid": params["role_id"], "orderid": decoded_info2.get("order_id", ""), "amount": float(params["amount"]), "extra": params["trade_no"]}
        result = handle_order_data(order)
        if result:
            return "SUCCESS"
        else:
            charge_error_log("WHWJ", decoded_info2.get("order_id", ""), "handle_order_data(order) Error")
            return "FAIL"

    except Exception,e:
        charge_error_log("WHWJ", decoded_info2.get("order_id", ""), "%s" % e)
        return "FAIL"
