#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-30 17:30:59
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      游戏后台管理的接入点
# @end
# @copyright (C) 2015, kimech

import time
import zlib
import cPickle as pickle

from tornado.escape import json_encode

from .base import BaseHandler
from apps.misc import auth_utils
from apps.misc import platform_auth
from apps.models.account import Account
from apps.misc.global_info import Server
from apps.misc.global_info import Platform
from apps.configs.msg_code import MsgCode
from torngas.settings_manager import settings
from apps.services.notice import NoticeService
from apps.services import rank as rank_service
from apps.services import name as name_service

from apps.logics.helpers import act_helper
from apps.logics.helpers import task_helper
from apps.services import charge as charge_service
from apps.services.group import GroupService

from libs.rklib.core import app
from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

class InternalAdminClass:
    def __init__(self):
        super(InternalAdminClass, self).__init__()

    @classmethod
    def admin_add_notice(cls, params):
        start = params.get("start")
        end = params.get("end")
        interval = params.get("interval", 30)
        notice_type = params.get("notice_type")
        content = params.get("content", "")
        sid = params.get("sid")

        if int(notice_type) == 1:
            NoticeService.admin_notice(int(sid), int(start), int(end), content)  # 登录面板公告
        else:
            NoticeService.admin_broadcast(int(sid), int(start), int(end), int(interval), content)  # 跑马灯公告

        return {"mc": 900002}

    @classmethod
    def admin_delete_notice(cls, params):
        notice_id = params.get("notice_id")
        plat = params.get("plat")
        sid = params.get("sid")

        NoticeService.admin_delete_notice(plat, notice_id)  # 删除登录面板公告

        return {"mc": 900002}

    @classmethod
    def admin_send_mail(cls, params):
        sid = params.get("sid")
        uids = params.get("uids")
        title = params.get("title")
        sender = params.get("sender")
        msg = params.get("msg")
        attachments = params.get("attachments")

        from apps.services.mail import MailService
        if str(uids) == "@all":
            receivers = rank_service.get_all_players(int(sid))
        else:
            receivers = str(uids).split("/")

        MailService.send_system(receivers, title, sender, msg, eval(attachments))

        return {"mc": 900002}

    @classmethod
    def admin_fix_gamer(cls, params):
        sid = params.get("sid")
        uids = params.get("uids")
        items = params.get("items")

        if str(uids) == "@all":
            receivers = rank_service.get_all_players(int(sid))
        else:
            receivers = str(uids).split("/")

        from apps.models.user import User
        from apps.logics import package as pack_logic
        for uid in receivers:
            user = User.get(uid)
            if isinstance(user, User):
                pack_logic.add_items(user, eval(items))
                _handle_daily_task_after_vitual_pay(user)

        return {"mc": 900002}

    @classmethod
    def admin_ban_chat(cls, params):
        """禁言
        """
        uid = params.get("uid")
        times = params.get("times")

        from apps.models.user import User
        user = User.get(uid)
        if isinstance(user, User):
            user.ext_info.ban_chat = int(time.time()) + int(times)
            user.ext_info.put()

            return {"mc": 900002}
        else:
            return {"mc": 900007}

    @classmethod
    def admin_ban_account(cls, params):
        """禁号
        """
        uid = params.get("uid")
        times = params.get("times")

        from apps.models.user import User
        user = User.get(uid)
        if isinstance(user, User):
            user.ext_info.ban_account = int(time.time()) + int(times)
            user.ext_info.put()

            return {"mc": 900002}
        else:
            return {"mc": 900007}

    @classmethod
    def admin_vitual_pay(cls, params):
        """模拟充值
        """
        uid = params.get("uid")
        money = params.get("money")

        from apps.models.user import User
        user = User.get(uid)
        if isinstance(user, User):
            amount = int(money)
            try:
                act_helper.update_after_charge(user, amount * 10, amount)
            except:
                return {"mc": 900009}

            try:
                user.vip.update_card_when_charge(amount)

                user.game_info.diamond += amount * 10
                user.game_info.add_vip_exp(amount * 10, instant_save=True)

                charge_service.add_uid_paid_set(str(uid))

                _handle_daily_task_after_vitual_pay(user)
            except Exception,e:
                raise e
                return {"mc": 900009}

            return {"mc": 900002}
        else:
            return {"mc": 900007}

    @classmethod
    def admin_clean_chat(cls, params):
        """清除聊天
        """
        sid = params.get("sid")
        uid = params.get("uid")

        try:
            tmp_msgs = redis_client.lrange(rediskey_config.CHAT_WORLD_BOX_KEY % sid, 0, 99999)
            for msg in tmp_msgs:
                msg1 = pickle.loads(msg)
                if str(uid) == msg1["sender"]["uid"]:
                    redis_client.lrem(rediskey_config.CHAT_WORLD_BOX_KEY % sid, 1, msg)

            return {"mc": 900002}
        except:
            return {"mc": 900009}

    @classmethod
    def admin_clean_mail(cls, params):
        """清除邮件
        """
        uid = params.get("uid")

        try:
            redis_client.delete(rediskey_config.MAIL_REPERTORY_NEW_PREFIX % uid)
            redis_client.delete(rediskey_config.MAIL_REPERTORY_OLD_PREFIX % uid)
            return {"mc": 900002}
        except:
            return {"mc": 900009}

    @classmethod
    def admin_query_player_info(cls, params):
        sid = params.get("sid")
        uid = params.get("uid", "")
        uname = params.get("uname", "")
        dtype = params.get("type", "user")

        from apps.models.user import User
        # uid为空 则根据uname查询玩家数据
        if uid:
            target_user = User.get(uid)
        elif uname:
            target_uid = name_service.get_uid_by_name(uname)
            target_user = User.get(target_uid)
        else:
            target_user = None

        if not target_user:
            return {"mc": 900007}

        data = {}
        if str(dtype) == "user":
            user_attrs = ["uid","name","update_name_times","avatar",
                           "user_sign","account_id","platform","sid",
                           "state","type","create_time","last_request",
                           "last_sign_time","total_login_days","login_history_dates",
                           "used_cdkey_tags", "game_info", "ext_info"]

        elif str(dtype) == "hero":
            user_attrs = ["hero", "equip", "skill", "spirit"]

        elif str(dtype) == "group":
            attr_obj = eval("target_user.group")
            data["group"] = {}
            for attr1 in attr_obj.all_def_attrs:
                if attr1 not in ["uid"]:
                    data["group"][attr1] = getattr(attr_obj, attr1)

            if not target_user.group.group_id:
                group = {}
            else:
                group = GroupService.find(target_user.sid, target_user.group.group_id)

            data["group_data"] = {}
            data["group_data"]["base"] = group

            data["uid"] = target_user.uid
            data["name"] = target_user.name

            data["mc"] = 900002
            data["info"] = pickle.dumps(data)

            return data

        else:
            user_attrs = [dtype]

        for attr in user_attrs:
            if type(eval("target_user.%s" % attr)) in [unicode, str, int, dict, list, set, tuple]:
                data[attr] = eval("target_user.%s" % attr)
            else:
                attr_obj = eval("target_user.%s" % attr)
                data[attr] = {}
                for attr1 in attr_obj.all_def_attrs:
                    if attr1 not in ["uid"]:
                        data[attr][attr1] = getattr(attr_obj, attr1)

            data["uid"] = target_user.uid
            data["name"] = target_user.name

        data["mc"] = 900002
        data["info"] = pickle.dumps(data)

        return data

class Admin(BaseHandler):
    def post(self):
        if not settings.DEBUG and not _check_admin_ip_in_whitelist(self):
            self.finish(json_encode({"mc": 900001}))
            return

        action = self.get_argument("action", "")
        if not action:
            self.finish(json_encode({"mc": 900005}))
            return

        try:
            ticket = self.get_argument("ticket", "")
            # 根据方法不同进行分发
            func_name = 'admin_%s' % action
            if not hasattr(InternalAdminClass, func_name):
                self.finish(json_encode({"mc": 900004}))
                return

            func = getattr(InternalAdminClass, func_name)
            decode_params = _get_admin_params(self)
            if not decode_params:
                self.finish(json_encode({"mc": 900006}))
                return

            result = func(decode_params)
            self.write(json_encode(result))
        except Exception,e:
            self.write(json_encode({"mc": 900009}))

class Index(BaseHandler):
    def get(self):
        self.write(json_encode({"mc": 200}))


def _handle_daily_task_after_vitual_pay(ki_user):
    """
    """
    new_task_ids = task_helper.prepare_daily_task(ki_user.game_info.role_level, ki_user.game_info.vip_level)
    add_task = [task_id for task_id in new_task_ids if task_id not in ki_user.task.daily_tasks]

    if add_task:
        for daily_task_id in add_task:
            ki_user.task.daily_tasks[daily_task_id] = {"process":0, "state": 0}

        ki_user.task.put()
    else:
        pass

def _check_admin_ip_in_whitelist(handler):
    """验证向游戏服务器发送消息的后台IP是否合法
    """
    remote_ip = handler.request.remote_ip
    if "X-Real-Ip" in handler.request.headers:
        remote_ip = handler.request.headers.get("X-Real-Ip")

    if remote_ip in settings.ADMIN_WHITE_IPS:
        return True
    else:
        return False

def _get_admin_params(handler):
    """读取参数
    """
    arguments = handler.get_argument("arguments", "")
    if not arguments:
        return

    decode_params = {}
    params = arguments.split("&")
    for param in params:
        kvs = param.split("=")
        if param and kvs[1]:
            decode_params[kvs[0]] = kvs[1]

    return decode_params
