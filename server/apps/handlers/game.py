#!/usr/bin/env python
# coding=utf-8

import time
import ujson
import copy
import json
import urllib
import logging
import requests

from apps.misc import utils
from apps.misc import auth_utils
from apps.misc.global_info import Server

from apps.models.user import User
from apps.models.account import Account

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.logics.helpers import user_helper
from apps.logics.helpers import act_helper
from apps.logics import vip as vip_logic

from apps.services.mail import MailService
from apps.services.group import GroupService
from apps.services.notice import NoticeService
from apps.services.worldboss import BossService
from apps.services import charge as charge_service

from .base import BaseHandler
from tornado.escape import json_encode
from libs.rklib.web.logic import gateway
from torngas.settings_manager import settings

class Login(BaseHandler):
    def post(self):
        """游戏登录接口
        """
        account_id = self.get_argument("account_id")
        server_id = self.get_argument("server_id")
        platform = self.get_argument("platform")
        session_id = self.get_argument("session_id")

        server = Server.get_server_by_id(server_id)
        if not server:
            self.finish(json_encode({"mc": MsgCode['ServerNotExist']}))
            return

        # 当服务器还未开启或者维护时，内部账户随意进出游戏
        if int(server["state"]) != settings.SERVER_STATE_OPEN and not auth_utils.white_ip_check(self):
           code = MsgCode['ServerNotOpen'] if int(server["state"]) == settings.SERVER_STATE_CLOSE else MsgCode['ServerUpdateing']
           self.finish(json_encode({'mc': code}))
           return

        check_result = auth_utils.login_auth(session_id, account_id, server_id)
        if check_result:
            self.finish(json_encode(check_result))
            return

        complete_account_id = "%s_%s" % (platform, account_id)
        uid = Account.get_user_id(complete_account_id, server_id)
        if not uid:
            self.finish(json_encode({"mc": MsgCode['GameLoginFail']}))
            return

        user_login_data = {"aid": account_id, "uid": uid, "sid": server_id, "pf": platform}
        ki_user = User.install(user_login_data)
        if not isinstance(ki_user, User):
            self.finish(json_encode({"mc": MsgCode['GameLoginFail']}))
            return

        if ki_user.ext_info.ban_account and ki_user.ext_info.ban_account > int(time.time()):
            self.finish(json_encode({"mc": MsgCode["UserFrozen"]}))
            return

        server_time = int(time.time())
        ki_user.update_user_login_info(server_time)
        user_guide_checker(ki_user) # 为前端加引导保护器，防止玩家引导断掉 导致无法进行游戏
        ki_user.vip.update_card_when_request() # 更新玩家vip月卡信息
        ki_user.activity.update_effective_acts(ki_user.sid, ki_user.game_info.role_level) # 更新活动数据
        act_helper.update_after_login(ki_user)
        if charge_service.ismember_of_paid_set(uid):
            vip_logic.charge_refresh(ki_user) # 如果有未发送元宝的订单，立即发送元宝

        _set_secure_cookie(self, account_id, uid, platform, server_time, server_id) # 返回COOKIE

        # boss_hero_rank = BossService.login_notice(ki_user.sid, ki_user.uid)
        # if boss_hero_rank and boss_hero_rank == 1:
        #     NoticeService.broadcast(ki_user.sid, 20, {'uid': ki_user.uid, 'name': ki_user.name}, boss_hero_rank)

        msg = {}
        msg["mc"] = MsgCode['GameLoginSucc']

        msg["data"] = {}
        msg["data"]["user_data"] = fetch_user_data(ki_user)
        msg["data"]["server_time"] = server_time

        self.write(json_encode(msg))

class Api(BaseHandler):
    """游戏业务接口
    """
    def post(self):
        request_context = self.request.request_context
        user = request_context.user
        # ======   核心 * 调用业务代码的接口  ==============
        result = gateway.process(request_context)
        # ============  ============  ===================
        self.write(json_encode(result))
        # ****************** 测试专用查用户数据接口 ************************** #
        # ki_user = request_context.user
        # user_data = fetch_user_data(ki_user)
        # user_data = {}
        # user_data["acts_data"] = ki_user.activity.get_effective_acts(ki_user.sid, ki_user.game_info.role_level)

        # result["user_data"] = user_data

        # data = ujson.dumps(result)
        # data1 = utils.encrypt(ujson.dumps(data))
        # data2 = utils.decrypt(data1)
        # *************************** END ********************************* #

def _set_secure_cookie(self, account_id, uid, platform, server_time, server_id):
    """设置cookie信息
    """
    token = auth_utils.get_rkauth_signature(account_id, uid, platform, server_id, server_time)

    cookie_str = "aid=%s&uid=%s&pf=%s&sid=%s&ts=%s&token=%s" % (account_id,uid,platform,server_id,server_time,token)
    self.set_secure_cookie("user_cookie_chain", cookie_str)

def fetch_user_data(ki_user):
    """
    """
    user_data = {}
    user_data["user"] = ki_user.get_user_game_info()
    user_data["package"] = ki_user.package.items
    user_data["array"] = ki_user.array.mission

    user_data["hero"] = {}
    user_data["hero"]["heros"] = user_helper.build_hero_euqip_skill(ki_user)  # 把技能和装备 装配到机甲上。
    user_data["hero"]["gold_cd"] = ki_user.hero.pick_info["gold_cd"]
    user_data["hero"]["diamond_pick_times"] = ki_user.hero.pick_info["diamond_pick_times"]
    user_data["hero"]["diamond_ten_times"] = ki_user.hero.pick_info["diamond_ten_times"]

    user_data["daily"] = {}
    user_data["daily"]["mission_info"] = ki_user.daily_info.mission_info
    user_data["daily"]["hero_pick_info"] = ki_user.daily_info.hero_pick_info
    user_data["daily"]["buy_energy_times"] = ki_user.daily_info.buy_energy_times
    user_data["daily"]["buy_gold_times"] = ki_user.daily_info.buy_gold_times
    user_data["daily"]["mall_pick_cd"] = ki_user.daily_info.mall_pick_cd
    user_data["daily"]["mall_refresh_times"] = ki_user.daily_info.mall_refresh_times
    user_data["daily"]["world_chat_times"] = ki_user.daily_info.world_chat_times
    user_data["daily"]["resign_tag"] = ki_user.daily_info.resign_tag
    user_data["daily"]["group_donate_times"] = ki_user.daily_info.group_info["donate_times"]
    user_data["daily"]["online_awards"] = ki_user.daily_info.online_awards
    user_data["daily"]["trial_proccess"] = ki_user.trial.daily_current_process  # 冗余数据，临时增加。
    user_data["daily"]["arena_fight_times"] = ki_user.arena.daily_challenge_times  # 冗余数据，临时增加。

    act_mission_times = dict.fromkeys(range(1,6), 0)
    for k,v in ki_user.daily_info.act_missions.items():
        act_mission_times[int(k)] = v["past_times"]
    user_data["daily"]["act_mission_times"] = act_mission_times

    user_data["mission"] = {}
    user_data["mission"]["chapters"] = ki_user.mission.chapters
    user_data["mission"]["missions"] = ki_user.mission.missions

    user_data["group"] = {}
    user_data["group"]["group_id"] = ki_user.group.group_id
    user_data["group"]["group_name"] = GroupService.get_name_by_id(ki_user.sid, ki_user.group.group_id)
    user_data["group"]["cd"] = ki_user.group.cd

    user_data["vip"] = {}
    user_data["vip"]["card_data"] = ki_user.vip.card_data
    user_data["vip"]["bought_gifts"] = ki_user.vip.bought_gifts

    user_data["extra"] = {}
    user_data["extra"]["update_name_times"] = ki_user.update_name_times

    #  ======================== update =======================
    user_data["arena"] = {}
    user_data["arena"]["challenge_times"] = ki_user.arena.daily_challenge_times
    user_data["arena"]["add_times"] = ki_user.arena.daily_add_times
    user_data["arena"]["last_fight"] = ki_user.arena.last_fight
    user_data["arena"]["refresh_times"] = ki_user.arena.daily_refresh_times
    user_data["arena"]["admire_list"] = ki_user.arena.daily_admire_list
    user_data["arena"]["awarded_index"] = ki_user.arena.awarded_index
    user_data["arena"]["daily_awarded_index"] = ki_user.arena.daily_awarded_index
    user_data["arena"]["daily_scores"] = ki_user.arena.daily_scores
    user_data["arena"]["max_rank"] = ki_user.arena.max_rank
    #  ======================== update =======================

    fetch_user_module_data(ki_user, user_data)

    return user_data

def fetch_user_module_data(ki_user, user_data):
    """根据玩家功能是否开启，返回前端数据

    Args:
        func_id 功能ID

    Returns:
        data {}
    """
    level = ki_user.game_info.role_level

    # 天赋数据
    talent_open_level = 1
    if level >= talent_open_level:
        user_data["talent"] = ki_user.talent.talents

    # 战舰数据
    warship_open_level = 1
    if level >= warship_open_level:
        user_data["warship"] = {}
        user_data["warship"]["ships"] = ki_user.warship.ships
        user_data["warship"]["team"] = ki_user.warship.team

    # 主线任务数据
    maintask_open_level = 1
    if level >= maintask_open_level:
        user_data["main_task_doing"] = ki_user.task.main_doing_tasks

    # 每日任务数据, 每次登录必须调用更新每日日常任务数据，要不然新手建号上线日常任务重复领取BUG！！！！
    dailytask_open_level = 1
    daily_tasks = ki_user.task.get_daily_tasks(ki_user.game_info.role_level,
                                    ki_user.game_info.vip_level, ki_user.vip.card_data)
    if level >= dailytask_open_level:
        user_data["daily_tasks"] = daily_tasks

    # 签到数据
    sign_open_level = 1
    if level >= sign_open_level:
        user_data["sign"] = {}
        user_data["sign"]["last_sign"] = ki_user.sign.last_sign
        user_data["sign"]["month_sign_days"] = ki_user.sign.month_sign_days
        user_data["sign"]["last_award_index"] = ki_user.sign.last_award_index
        user_data["sign"]["total_sign_days"] = ki_user.sign.total_sign_days

    # 随机商店数据
    mystery_shop_open_level = 1
    if level >= mystery_shop_open_level:
        show_time = ki_user.mall.mystery.get("last_refresh", 0)
        user_data["mystery_shop"] = {}
        user_data["mystery_shop"]["show"] = 1 if show_time and time.time() - show_time < 3600 else 0
        user_data["mystery_shop"]["time"] = show_time

def user_guide_checker(ki_user):
    """玩家引导保护器
    """
    tmp = 0
    for id, value in game_config.guide_main_cfg.items():
        if ki_user.game_info.role_level >= value["skip_level"] + 1 and id >= tmp:
            tmp = id

    if tmp > ki_user.game_info.last_guide_id:
        ki_user.game_info.last_guide_id = tmp
        ki_user.game_info.put()
