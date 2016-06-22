#!/usr/bin/env python
# encoding: utf-8

import time
import logging
import hashlib

from .common import handle_order_data
from .common import charge_error_log

from apps.services import charge as charge_service
from torngas.settings_manager import settings

# =========== 签名方法 ===========================
def _gen_safe_sign(params, pay_key):
    if len(params) == 0:
        return ''

    keys = params.keys()
    keys.sort()

    query_arr = []
    for k in keys:
        if k == 'sign' or k == 'sig':
            continue
        else:
            query_arr.append(k + '=' + params[k])

    query_str = '&'.join(query_arr)

    return hashlib.md5(query_str + pay_key).hexdigest()

# =========== 签名方法 END ========================
def pay_callback(handler):
    """
        /notification/EZ?app=1234567890ABCDEF&cbi=CBI123456&ct=1376578903&fee=100&pt=1376577801&ssid=123456&st=1&tcd=137657AVDEDFS&uid=1234&ver=1&sign=xxxxxxxxxxx
        app String 1234567890ABCDEF 十六进制字符串形式的应用ID
        cbi String CIB123456 在客户端由CP应用指定的额外参数，比如可以传游戏中的道具ID、游戏中的用户ID等
        ct long 1376578903 支付完成时间
        fee int 100 金额（分）
        pt long 1376577801 付费时间，订单创建服务器UTC时间戳（毫秒）
        sdk String 09CE2B99C22E6D06 渠道在易接服务器的ID
        ssid String 123456 订单在渠道平台上的流水号
        st int 1 是否成功标志，1标示成功，其余都表示失败
        tcd String 137657AVDEDFS 订单在易接服务器上的订单号
        uid String 1234 付费用户在渠道平台上的唯一标记
        ver String 1 协议版本号，目前为“1”
        sign String f67893489267ea3 上述内容的数字签名，方法在下文会说明
    """
    params = dict.fromkeys([
        "app",
        "cbi",
        "sdk",
        "ct",
        "fee",
        "pt",
        "ssid",
        "st",
        "tcd",
        "uid",
        "ver",
        "sign",
        ], '')

    for i in params:
        params[i] = handler.get_argument(i, "")

    app_cfg = settings.PLATFORM_APP_ID_MAPPING.get("EZ", {})
    if not app_cfg:
        charge_error_log("EZ_%s" % params["sdk"], params["cbi"], "app_cfg is null")
        return "FAIL"

    try:
        # 兄弟啊，这不是我们的充值订单，不要拿我作宝搞啊。
        if params["app"].upper() != app_cfg["AppId"]:
            return "SUCCESS"

        # 充值未成功，不予处理
        if int(params["st"]) != 1:
            return "SUCCESS"

        safe_sign = _gen_safe_sign(params, app_cfg["PayKey"])
        if safe_sign != params['sign']:
            charge_error_log("EZ_%s" % params["sdk"], params["cbi"], "safe_sign != params['sign']")
            return "FAIL"

        dealed_data = charge_service.get_by_extra_data(params["tcd"])
        if dealed_data:
            return "SUCCESS"  # 已经处理过的订单，除重

        order = {"plat": "EZ", "account": params["uid"], "uid": "", "orderid": params["cbi"], "amount": int(params["fee"]) / 100, "extra": params["tcd"]}
        result = handle_order_data(order)
        if result:
            return "SUCCESS"
        else:
            charge_error_log("EZ_%s" % params["sdk"], params["cbi"], "handle_order_data(order) Error")
            return "FAIL"

    except Exception,e:
        charge_error_log("EZ_%s" % params["sdk"], params["cbi"], "%s" % e)
        return "FAIL"
