#!/usr/bin/env python
# -*- coding: utf-8  -*-

import time
import ujson

from apps.misc import auth_utils

from apps.misc.global_info import Server
from torngas.settings_manager import settings
from apps.configs.msg_code import MsgCode

from apps.models.user import User

class KiAuthMiddleware(object):
    def process_request(self, handler, clear):
        """
        匹配路由后，执行处理handler时调用,**支持异步**
        :param handler: handler对象

        """
        request_path = handler.request.uri

        if request_path.startswith("/A6ksi"):
            return

        if request_path.startswith("/notification/"):
            return

        if request_path.startswith("/platform/version"):
            return

        if request_path.startswith("/platform/regist"):
            return

        if request_path.startswith("/platform/express"):
            return

        if request_path.startswith("/platform/bind"):
            return

        if request_path.startswith("/platform/auth"):
            return

        if request_path.startswith("/game/login"):
            return

        if request_path.startswith("/debug"):
            return

        # game api需要检验服务器状态
        cookie = handler.get_secure_cookie("user_cookie_chain")
        if not cookie:
            handler.finish(ujson.dumps({"mc": MsgCode["CookieAuthFailed"]}))
            return 1

        cookie_data = _handle_secure_cookie(cookie)
        server_state = Server.get_server_state_by_id(int(cookie_data["sid"]))
        # 当服务器还未开启或者维护时，内部账户随意进出游戏
        if int(server_state) != settings.SERVER_STATE_OPEN and not auth_utils.white_ip_check(handler):
           code = MsgCode['ServerNotOpen'] if int(server_state) == settings.SERVER_STATE_CLOSE else MsgCode['ServerUpdateing']
           handler.finish(ujson.dumps({"mc": code}))
           return 1

        authed_cookie_data = auth_utils.auth_cookie(cookie_data)
        if not authed_cookie_data:
            handler.finish(ujson.dumps({"mc": MsgCode["CookieAuthFailed"]}))
            return 1

        ki_user = User.install(authed_cookie_data)
        if not isinstance(ki_user, User):
            handler.finish(ujson.dumps({"mc": MsgCode["UserGetDataFailed"]}))
            return 1

        # 双开检测，防止玩家多端登录
        if ki_user.last_sign_time != int(cookie_data["ts"]):
            handler.finish(ujson.dumps({"mc": MsgCode["GameLoginByOthers"]}))
            return 1

        # TODO 用户状态监测
        if ki_user.ext_info.ban_account and ki_user.ext_info.ban_account > int(time.time()):
            handler.finish(ujson.dumps({"mc": MsgCode["UserFrozen"]}))
            return 1

        handler.request.request_context.user = ki_user

        if request_path.startswith("/debug"):
            return 1

def _handle_secure_cookie(cookie_str):
    """
    """
    cookie = {}
    cookie_items = cookie_str.split("&")
    for item in cookie_items:
        valus = item.split("=")
        cookie[valus[0]] = valus[1]

    return cookie
