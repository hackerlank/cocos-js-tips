#!/usr/bin/env python
# encoding: utf-8

import json
import hmac
import time
import logging
import hashlib
import requests

from apps.misc import utils
from apps.misc import auth_utils

from apps.models.account import Account
from apps.configs.msg_code import MsgCode
from torngas.settings_manager import settings

def fetch_plat_openid(params):
    """
    """
    params_list = params.split("|")

    userid = params_list[0].split("_")[1]
    ticket = params_list[1].split("_")[1]
    seqnum = params_list[2].split("_")[1]
    prtchid = params_list[3].split("_")[1]

    app_cfg = settings.PLATFORM_APP_ID_MAPPING.get("WHWJ", {})
    sign_str = "cpid=%s&prtchid=%s&seqnum=%s&ticket=%s&userId=%s" % (app_cfg["AppId"], prtchid, seqnum, ticket, userid)
    signature = utils.md5(sign_str+app_cfg["AppKey"])

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "http://service.wangamedia.com/sdkcore/user/channel/openid.html"
    param = {
        "cpid": app_cfg["AppId"],
        "userId": userid,
        "ticket": ticket,
        "seqnum": seqnum,
        "prtchid": prtchid,
        "sign": signature,
    }

    try:
        data = requests.post(url, data=param, headers=headers, timeout=5).json()
    except requests.exceptions.Timeout:
        logging.error("【 PLATFORM FETCH OPENID FAIL 】reason: request time out.")
        return False

    if data["success"]:
        # 检查openid是否在预约队列里
        return data["businessResult"]
    else:
        reason = data.get("errorCode", "no error msg.")
        logging.error("【 PLATFORM FETCH OPENID FAIL 】reason: %s" % reason)
        return False

def auth_WHWJ(platform, params):
    """
        万好万家
    """
    try:
        params_list = params.split("|")

        userid = params_list[0].split("_")[1]
        ticket = params_list[1].split("_")[1]
        seqnum = params_list[2].split("_")[1]
        prtchid = params_list[3].split("_")[1]

        if not auth_utils.check_param_legal(platform):
            raise
    except:
        return False, MsgCode['AccountAuthParamError'], None

    app_cfg = settings.PLATFORM_APP_ID_MAPPING.get("WHWJ", {})
    if not app_cfg:
        return False, MsgCode['PlatformNotExist'], None, sid

    sign_str = "cpid=%s&prtchid=%s&seqnum=%s&ticket=%s&userid=%s" % (app_cfg["AppId"], prtchid, seqnum, ticket, userid)
    signature = utils.md5(sign_str+app_cfg["AppKey"])

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "http://service.wangamedia.com/sdkcore/user/service/checkonlineuser.html"
    param = {
        "cpid": app_cfg["AppId"],
        "userid": userid,
        "ticket": ticket,
        "seqnum": seqnum,
        "prtchid": prtchid,
        "sign": signature,
    }

    try:
        data = requests.post(url, data=param, headers=headers, timeout=5).json()
    except requests.exceptions.Timeout:
        return False, MsgCode['AccountAuthFail'], None

    if data["success"]:
        return True, None, "%s_%s" % (platform, userid)
    else:
        reason = data.get("errorCode", "no error msg.")
        logging.error("【 PLATFORM AUTH 】auth %s failed, reason: %s" % (platform, reason))
        return False, MsgCode['AccountAuthFail'], None

def auth_EZ(platform, params):
    """
        易接
    """
    try:
        params_list = params.split("|")

        sdk = params_list[0].split("_")[1]
        app = params_list[1].split("_")[1]
        uin = params_list[2].split("_")[1]
        sess = params_list[3].split("_",1)[1]

        if not auth_utils.check_param_legal(platform):
            raise
    except:
        return False, MsgCode['AccountAuthParamError'], None

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "http://sync.1sdk.cn/login/check.html"
    params = "?sdk=%s&app=%s&uin=%s&sess=%s" % (sdk, app, uin, sess)

    try:
        data = requests.get(url + params, timeout=5).json()
    except requests.exceptions.Timeout:
        return False, MsgCode['AccountAuthFail'], None

    account_id = uin if uin else sess
    if data == 0:
        return True, None, "%s_%s" % (platform, account_id)
    else:
        logging.error("【 PLATFORM AUTH 】auth %s failed, reason: code [%s], 返回0表示用户已登录，其他表示未登陆" % (platform, data))
        return False, MsgCode['AccountAuthFail'], None

def auth_XTZJ(platform, params):
    """
    uid_100010|session_28BzIMEXzVUMqBac
    """
    try:
        params_list = params.split("|")

        uid = params_list[0].split("_")[1]
        session = params_list[1].split("_")[1]  # 开发阶段，自己的账号系统 session即password
    except:
        return False, MsgCode['AccountAuthParamError'], None

    if not auth_utils.check_param_legal(platform, uid, session):
        return False, MsgCode['AccountAuthParamError'], None

    # 检查玩家账号是否存在，不存在则注册，若存在则验证密码通过
    complete_account_id = "%s_%s" % (platform, uid)
    if not Account.check_account_exist(complete_account_id):
        return False, MsgCode['AccountAuthFail'], None
        # Account.register(complete_account_id, session, 1)

    if not Account.check_user_password(complete_account_id, session):
        return False, MsgCode['AccountPasswordError'], None

    return True, None, complete_account_id
