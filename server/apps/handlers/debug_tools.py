#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-08-26 15:12:48
# @Author : Jiank (http://jiankg.github.com)
# @doc
#
# @end
# @copyright (C) 2015, kimech

import time

from .base import BaseHandler
from tornado.escape import json_encode
from apps.logics import user as user_logic
from apps.logics import package as package_logic

from apps.logics import mail

# ==========
import datetime
import logging

from apps.models.account import Account

from apps.services.sequence import Sequence

import random
from apps.services import rank as rank_service
from apps.models.user import User

from apps.logics import arena
from apps.logics import activity
from apps.logics import system

from libs.rklib.web.logic import KiRequestContext

from libs.rklib.core import app
redis_client = app.get_storage_engine('redis').client.current
# ==========

class Debug(BaseHandler):
    """游戏调试接口
    """
    def get(self):

        context = KiRequestContext(self)

        players = ['110000001', '110000001', '110000001']

        ki_user = None
        loop = 0
        while not isinstance(ki_user, User) or loop <= 3:
            player = random.choice(players)

            ki_user = User.debug_install(player)
            loop += 1

        context.user = ki_user
        action_list = ["arena.info(context)", "mail.info(context)", "system.heartbeat(context)"]
        action = random.choice(action_list)

        exec(action)

        self.write("%s" % redis_client.incr("pressure_count", 1))

    def post(self):
        request_context = self.request.request_context
        method = request_context.get_parameter("method", "")

        result = {"mc": 100}
        if method == "add_game_value":
            items = request_context.get_parameter("items").strip()
            user_logic.add_game_values(request_context.user, eval(items))

        elif method == "reset_user_data":
            module = request_context.get_parameter("module").strip()

            debug_handle_reset_user_data(request_context.user, module)

        elif method == "add_items":
            items = request_context.get_parameter("items").strip()

            debug_handle_add_items(request_context.user, items)

        elif method == "send_mails":
            receiver = request_context.get_parameter("receiver").strip()
            title = request_context.get_parameter("title").strip()
            sender = request_context.get_parameter("sender").strip()
            msg = request_context.get_parameter("msg").strip()
            attachments = request_context.get_parameter("attachments").strip()
            attachments = eval(attachments)
            if not isinstance(attachments, dict):
                raise 1

            from apps.services.mail import MailService
            MailService.send_system([receiver], title, sender, msg, attachments)
        else:
            result = {"mc": 404}

        self.write(json_encode(result))

def debug_handle_add_items(user, items):
    """
    """
    items = eval(items.replace(' ', ''))
    package_logic.add_items(user, items)

def debug_handle_reset_user_data(user, module):
    """
    """
    exec("user.%s._reset()" % module)
    print "reset %s module done." % module
