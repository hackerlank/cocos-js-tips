#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     验证工具文件
# @end
# @copyright (C) 2015, kimech

import re
import time
import hashlib

from torngas import settings

from apps.configs.msg_code import MsgCode
from apps.configs import rediskey_config

from libs.rklib.core import app
redis_client = app.get_storage_engine('redis').client.current

def white_ip_check(handler):
    """服务器异常状态时，检查白名单，白名单玩家可以进入游戏
    """
    remote_ip = handler.request.remote_ip
    if "X-Real-Ip" in handler.request.headers:
        remote_ip = handler.request.headers.get("X-Real-Ip")

    if redis_client.sismember(rediskey_config.PLATFORM_WHITE_SET_KEY, remote_ip):
        return True
    else:
        return False

def check_param_legal(*args, **kwargs):
    """
    检测参数非空
    检测参数不含特殊字符，防注入式攻击
    """
    illegals = [None, '']
    _tmp = set(illegals).intersection(set(args))

    if _tmp:
        return False

    # 检测特殊字符
    for arg in args:
        _result = re.findall("[^a-zA-Z0-9_]", arg)
        if _result:
            return False

    return True

def login_auth(session_id, account_id, server_id):
    """选服之后登陆验证
    """
    try:
        if len(session_id) != 42:
            return {"mc": MsgCode['ServerAuthParamError']}

        timestamp = int(session_id[-10:])
        now_time = int(time.time())

        # 选服的session存活时间1分钟，超过一分钟强制重新请求选服
        # if now_time - 60 > timestamp or now_time + 60 < timestamp:
        #     return {"mc": MsgCode['ServerSessionExpired']}

        if session_id[10:].upper() != build_session_id(account_id, timestamp)[10:].upper():
            return {"mc": MsgCode['ServerAuthParamError']}

        return {}
    except Exception, e:
        return {"mc": MsgCode['ServerAuthParamError']}

def auth_cookie(cookie_data):
    """验证签名，并且返回验证后的用户ID
    """
    kiauth_signature = cookie_data.get('token', '')

    aid = cookie_data.get('aid', '')
    uid = cookie_data.get('uid', '')
    pf = cookie_data.get('pf', '')
    sid = cookie_data.get('sid', 0)
    ts = cookie_data.get('ts', 0)

    built_signature = get_rkauth_signature(aid, uid, pf, int(sid), int(ts))

    if kiauth_signature == built_signature:
        return {'aid': aid, 'uid': uid, 'pf': pf, 'sid': int(sid), 'ts': int(ts)}
    else:
        return None

def get_rkauth_signature(aid, uid, pf, sid, ts):
    """
    生成rkauth签名
    """
    kiauth_fields = {}
    kiauth_fields['uid'] = uid
    kiauth_fields['aid'] = aid
    kiauth_fields['pf'] = pf
    kiauth_fields['sid'] = sid
    kiauth_fields['ts'] = ts
    kiauth_fields['WEB_KEY'] = settings.WEB_KEY
    kiauth_fields['GAME_KEY'] = settings.GAME_KEY

    return build_auth_signature(kiauth_fields)

def build_auth_signature(kiauth_fields):
    """生成kiauth签名"""
    payload = "&".join(k + "=" + str(kiauth_fields[k]) for k in sorted(kiauth_fields.keys()))

    return hashlib.md5(payload).hexdigest()

def build_session_id(account_id, now_time):
    now_time = str(now_time)

    hash_str = "%s%s%s" % (settings.WEB_KEY, account_id, now_time)
    hash_code = hashlib.md5(hash_str).hexdigest()
    ticket = '%s%s' % (hash_code, now_time)

    return ticket
