#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-30 17:30:59
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      游戏平台接口
# @end
# @copyright (C) 2015, kimech

import time
import string
import random
import datetime
from random import choice

from tornado.escape import json_encode
from torngas.settings_manager import settings

from .base import BaseHandler
from apps.misc import auth_utils
from apps.misc import platform_auth

from apps.models.account import Account
from apps.misc.global_info import Server
from apps.misc.global_info import Platform
from apps.configs.msg_code import MsgCode

from apps.services.sequence import Sequence
from apps.services.notice import NoticeService

NEED_OPEN_ID_PLATS = ["YSDK", "UC", "QIHOO"]

class Version(BaseHandler):
    def post(self):
        try:
            plat_sign = self.get_argument("platform", "")

            if not auth_utils.check_param_legal(plat_sign):
                self.finish(json_encode({"mc": MsgCode['ParamError']}))
                return

            platform = Platform.get_platform_info()
            platform_data = {}
            if not platform:
                self.write(json_encode({"mc": MsgCode['PlatformNotExist']}))
            else:
                platform_data["cdn_url"] = platform["cdn_url"]
                platform_data["remote_manifest_url"] = platform["remote_manifest_url"]

                if auth_utils.white_ip_check(self):
                    platform_data["resource_version"] = platform["test_resource_version"]
                else:
                    platform_data["resource_version"] = platform["prod_resource_version"]

                msg = {}
                msg["mc"] = 100
                msg["data"] = {}
                msg["data"]["platform"] = platform_data

                self.write(json_encode(msg))
        except Exception,e:
            self.interal_error_handle(e)

class Regist(BaseHandler):
    """注册账户
    """
    def post(self):
        try:
            platform = self.get_argument("platform", "")
            auth_params = self.get_argument("auth_params", "")

            if not auth_utils.check_param_legal(platform):
                self.finish(json_encode({"mc": MsgCode['ParamError']}))
                return

            try:
                params_list = auth_params.split("|")

                account_id = params_list[0].split("_")[1]
                password = params_list[1].split("_")[1] # 自己的账号系统

                if not auth_utils.check_param_legal(account_id, password):
                    raise

                if len(account_id) < 6 or len(account_id) > 18 or len(password) < 6 or len(password) > 18:
                    raise
            except:
                self.finish(json_encode({"mc": MsgCode['AccountRegistParamsError']}))
                return

            complete_account_id = "%s_%s" % (platform, account_id)

            if Account.check_account_exist(complete_account_id):
                self.finish(json_encode({"mc": MsgCode['AccountAlreadyExist']}))
                return

            Account.register(complete_account_id, password)

            msg = build_login_game_data(platform, account_id, auth_utils.white_ip_check(self))
            self.write(json_encode(msg))
        except Exception,e:
            self.interal_error_handle(e)

class Express(BaseHandler):
    """快速试玩
    """
    def post(self):
        try:
            platform = self.get_argument("platform", "")

            if not auth_utils.check_param_legal(platform):
                self.finish(json_encode({"mc": MsgCode['ParamError']}))
                return

            tmp_account_id = None
            while not tmp_account_id:
                tmp_account_id = gen_account_id()
                account = Account.get_account("%s_%s" % (platform, tmp_account_id))
                if not isinstance(account, Account):
                    tmp_account_id = None

            tmp_password = gen_password()

            complete_account_id = "%s_%s" % (platform, tmp_account_id)
            Account.register(complete_account_id, tmp_password, 0)

            msg = build_login_game_data(platform, tmp_account_id, auth_utils.white_ip_check(self))
            msg["data"]["password"] = tmp_password

            self.write(json_encode(msg))
        except Exception,e:
            self.interal_error_handle(e)

class Bind(BaseHandler):
    """绑定游客账号
    """
    def post(self):
        try:
            platform = self.get_argument("platform", "")
            tmp_auth_params = self.get_argument("tmp_auth_params", "")
            auth_params = self.get_argument("auth_params", "")

            if not auth_utils.check_param_legal(platform):
                self.finish(json_encode({"mc": MsgCode['ParamError']}))
                return

            try:
                params_list = auth_params.split("|")
                account_id = params_list[0].split("_")[1]
                password = params_list[1].split("_")[1] # 自己的账号系统

                params_list1 = tmp_auth_params.split("|")
                tmp_account_id = params_list1[0].split("_")[1]
                tmp_password = params_list1[1].split("_")[1] # 自己的账号系统

                if not auth_utils.check_param_legal(account_id, password, tmp_account_id, tmp_password):
                    raise

                if len(account_id) < 6 or len(account_id) > 18 or len(password) < 6 or len(password) > 18:
                    raise
            except Exception,e:
                self.finish(json_encode({"mc": MsgCode['AccountRegistParamsError']}))
                return

            complete_account_id = "%s_%s" % (platform, tmp_account_id)
            complete_account_id1 = "%s_%s" % (platform, account_id)
            if not Account.check_user_password(complete_account_id, tmp_password):
                self.finish(json_encode({"mc": MsgCode['AccountAuthFail']}))
                return

            # 只有临时账户可以绑定账号
            if Account.account_type(complete_account_id) != 0:
                self.finish(json_encode({"mc": MsgCode['AccountBindRepeat']}))
                return

            if Account.check_account_exist(complete_account_id1):
                self.finish(json_encode({"mc": MsgCode['AccountAlreadyExist']}))
                return

            result = Account.bind_account_auth_data(complete_account_id, complete_account_id1, password)
            if result:
                self.write(json_encode({"mc": MsgCode['AccountBindSucc']}))
            else:
                self.write(json_encode({"mc": MsgCode['AccountBindFail']}))
        except Exception,e:
            self.interal_error_handle(e)

class Auth(BaseHandler):
    """账号验证
    """
    def post(self):
        platform = self.get_argument("platform", "")
        auth_params = self.get_argument("auth_params", "")

        if not auth_utils.check_param_legal(platform):
            self.finish(json_encode({"mc": MsgCode['ParamError']}))
            return

        # 根据平台不同进行分发
        platform_config = Platform.get_plat_config(platform)
        if not platform_config:
            self.finish(json_encode({"mc": MsgCode['PlatformNotExist']}))
            return

        if not hasattr(platform_auth, platform_config["checker"]):
            self.finish(json_encode({"mc": MsgCode['AccountAuthParamError']}))
            return

        func = getattr(platform_auth, platform_config["checker"])
        success, code, complete_account_id = func(platform, auth_params)

        if not success:
            self.finish(json_encode({"mc": code}))
            return

        if platform_config["sign"] in NEED_OPEN_ID_PLATS:
            account = Account.get_account(complete_account_id)
            if not account.open_id: # 0 - 未检测 1 - 已预约 2 - 没预约 3 - 已兑奖
                open_id = platform_auth.fetch_plat_openid(auth_params)
                account.update_open_id(open_id)

        account_id = complete_account_id.split("_")[1]
        msg = build_login_game_data(platform, account_id, auth_utils.white_ip_check(self))
        self.write(json_encode(msg))

def gen_account_id():
    now_time = datetime.datetime.now().strftime("%m%d%H%M%S");
    random_num = random.randint(100,999);

    return str(now_time) + str(random_num)

def gen_password(length=8, chars=string.ascii_letters+string.letters):
    return ''.join([choice(chars) for i in range(length)])

def build_login_game_data(platform, account_id, white_ip):
    """
    """
    now_time = int(time.time())

    session_id = auth_utils.build_session_id(account_id, now_time)
    account = Account.get_account("%s_%s" % (platform, account_id))
    servers = Server.get_all_servers()
    login_history = Account.get_login_history("%s_%s" % (platform, account_id))

    msg = {}
    msg["mc"] = 100

    msg["data"] = {}
    msg["data"]["session_id"] = session_id
    msg["data"]["account_id"] = account_id
    msg["data"]["account_type"] = account.type
    msg["data"]["servers_info"] = fectch_server_info(servers, white_ip)
    msg["data"]["login_history"] = login_history
    notice = NoticeService.get_login_notices()
    msg["data"]["notices"] = notice

    return msg

def fectch_server_info(servers, white_ip):
    """整理服务器关键信息传给前端
    """
    final_list = []
    for s,sinfo in servers.items():
        new = {}
        new["server_id"] = sinfo["server_id"]
        new["server_name"] = sinfo["server_name"]
        new["domain"] = sinfo["domain"]
        if sinfo["state"] != settings.SERVER_STATE_OPEN and white_ip:
            new["state"] = settings.SERVER_STATE_OPEN
        else:
            new["state"] = sinfo["state"]

        new["tag"] = sinfo["tags"]
        new["opentime"] = sinfo["open_time"]

        final_list.append(new)

    return final_list
