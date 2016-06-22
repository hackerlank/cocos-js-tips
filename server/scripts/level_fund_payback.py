#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-09 20:47:03
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   定时排行脚本
# @end
# @copyright (C) 2015, kimech

import os
import sys
import time
import datetime
import traceback
import cPickle as pickle

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BASE_DIR + '/apps')

import settings
os.environ.setdefault('KIMECH_APP_SETTINGS', 'settings.prod')

from libs.rklib.core import app
app.init(plat = "ios",
         storage_cfg_file = BASE_DIR + "/apps/configs/app_config/storage.conf",
         logic_cfg_file = BASE_DIR + "/apps/configs/app_config/logic.conf",
         model_cfg_file = BASE_DIR + "/apps/configs/app_config/model.conf")

from apps.models.user import User
from apps.services import rank as rank_service

receivers = rank_service.get_all_players(sid)
for i in receivers:
    user = User.get(i)
    if isinstance(user, User):
        print "%s not exist." % i
        continue

    actid = 3003
    if actid not in user.activity.acts:
        continue

    act_data = user.activity.acts[actid]
