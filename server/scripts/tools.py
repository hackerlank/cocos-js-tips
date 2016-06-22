#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-12-09 20:47:03
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   游戏维护工具
#       1.排行榜前10玩家丰厚回报（第7日21:30按照最高战力发放）
#       2.达到指定战力就有额外好礼（第7日21:30按照最高战力发放）
#       2.全民目标奖励邮件发放奖励（第7日21:30按照最高战力发放）
#       3.竞技场导入机器人
#       4.凌晨5点试炼排行榜结算
#       5.晚上21点竞技场结算
#       6.查询玩家信息
#
# ex: python scripts/tools.py --env=prod --plat=ios --command=search_player_data --sid=1 --args=1,uid
#
# @end
# @copyright (C) 2015, kimech

import os
import sys
import time
import json
import cPickle as pickle
import datetime

env_list = ["local","dev","prod"]
plat_list = ["local","dev","ios","android","apple"]
cmd_list = ["act_fight_rank","act_fight_target","arena_import_robots",
            "count_trial_rank","count_arena_rank","search_player_data",
            "delete_chat_msg","act_add_award","settle_world_boss"]

def parse_arg(input_arg, spliter, choices):
    """
    """
    tmp = input_arg.split(spliter)
    if tmp[1] not in choices:
        raise

    return tmp[1]

try:
    ENV = parse_arg(sys.argv[1], "--env=", env_list)
    PLAT = parse_arg(sys.argv[2], "--plat=", plat_list)
    COMMAND = parse_arg(sys.argv[3], "--command=", cmd_list)
except Exception,e:
    print """
useage: python tools.py
            --env=%s
            --plat=%s
            --command=%s
""" % (env_list, plat_list, cmd_list)
    sys.exit()

# ==========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BASE_DIR + '/apps')

import settings
os.environ.setdefault('KIMECH_APP_SETTINGS', 'settings.%s' % ENV)

from libs.rklib.core import app
app.init(plat = PLAT,
         storage_cfg_file = BASE_DIR + "/apps/configs/app_config/storage.conf",
         logic_cfg_file = BASE_DIR + "/apps/configs/app_config/logic.conf",
         model_cfg_file = BASE_DIR + "/apps/configs/app_config/model.conf")
# ==========================================================================

from apps.services import rank as rank_service
from apps.services import act as act_service
from apps.services.arena import ArenaService
from apps.services.worldboss import BossService

from apps.logics.helpers import act_helper

from apps.misc import utils
from apps.configs import game_config
from apps.configs import rediskey_config
from apps.services.mail import MailService

from apps.models.user import User

redis_client = app.get_storage_engine('redis').client.current

# ============================= Internal Functions =========================
def _act_fight_send_awards(sid, act_id):
    if game_config.activity_cfg[act_id]["type"] == 200:
        try:
            print "*" * 80
            print "Time: %s, [SERVER_ID: %s ACT_ID: %s] fight rank awards mail service start." % (datetime.datetime.now(), sid, act_id)

            def fight_rank_send_mail_awards(sid, act_id):
                """到活动结束时间点发送排行奖励

                Args:
                    sid  服务器ID
                    act_id  活动ID
                """
                indexes = game_config.act_sample_detail_cfg.get(act_id, [])
                max_cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, max(indexes)))

                rank_name = rediskey_config.RANK_KEY_PREFIX % (sid, "fight")
                top = redis_client.zrevrange(rank_name, 0, max_cfg["cond_a"]-1, withscores=True)

                for index, player in enumerate(top):
                    fight_rank = index + 1
                    try:
                        award_index = min([rank for rank in indexes if rank >= fight_rank])
                    except:
                        award_index = 0

                    if not award_index:
                        continue

                    cfg = game_config.act_detail_cfg.get("%s-%s" % (act_id, award_index))
                    # 排名前10 且 战力达到指定值才有奖励
                    if player[1] >= cfg["cond_b"]:
                        MailService.send_game(player[0], 1001, [fight_rank], cfg["awards"])
                        print "[act:%s] fight_rank_send_mail_awards: receiver: %s, rank: %s, fight: %s, awards: %s" % (act_id, player[0], fight_rank, player[1], cfg["awards"])

            fight_rank_send_mail_awards(sid, act_id)

            print "[ACT] fight rank awards mail service done."
            print "*" * 80
        except Exception,e:
            print e

    elif game_config.activity_cfg[act_id]["type"] == 300:
        try:
            print "*" * 80
            print "Time: %s, [SERVER_ID: %s ACT_ID: %s] fight awards mail service start." % (datetime.datetime.now(), sid, act_id)
            rank_service.fight_send_mail_awards(sid, act_id)
            print "[ACT] fight awards mail service done."
            print "*" * 80
        except Exception,e:
            print e

def _arena_rank_awards_mail(sid):
    try:
        print "*" * 80
        print "[SERVER: %s] Time: %s, arena rank awards mail service start." % (sid, datetime.datetime.now())
        ArenaService.crontab_send_award_mail(sid)
        print "arena rank awards mail service done."
        print "*" * 80
    except Exception,e:
        print e

def _act_add_awards_mail(sid, actid):
    """
    """
    receivers = rank_service.get_all_players(sid)
    for uid in receivers:
        user = User.get(uid)
        if not isinstance(user, User):
            print "uid: [ %s ] not exist." % uid
        else:
            if actid not in user.activity.acts:
                continue

            act_data = user.activity.acts[actid]
            index_list = game_config.act_sample_detail_cfg.get(actid)
            awards_indexes = [index for index in index_list if utils.bit_test(act_data["canget"], index)]
            if not awards_indexes:
                print "[act:%s] act add mail awards: receiver: %s, count: %s, award_level: 0, awards: {}" % (actid, uid, act_data["data"])
                continue

            award_index = max(awards_indexes)
            award_cfg = game_config.act_detail_cfg.get("%s-%s" % (actid, award_index))
            MailService.send_game(uid, 3008, [act_data["data"]], award_cfg["awards"])

            print "[act:%s] act add mail awards: receiver: %s, count: %s, award_level: %s, awards: %s" % (actid, uid, act_data["data"], award_index, award_cfg["awards"])

def _arena_import_robots(sid):
    ArenaService.import_robots(sid)

def _worldboss_settle_result(sid):
    try:
        print "*" * 80
        print "[SERVER: %s] Time: %s, world boss settle the results start." % (sid, datetime.datetime.now())
        BossService.settle_after_boss_fight(sid)
        print "world boss settle the results done."
        print "*" * 80
    except Exception,e:
        print e

# =========================== Main ============================================
if __name__ == '__main__':
    """
    """
    try:
        if COMMAND in ["act_fight_rank", "act_fight_target", "act_add_award"]:
            server_choices, act_choices = [],[]

            servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
            server_choices = servers.keys()
            helpstr1 = "--sid=%s    # server id\n" % server_choices
            SID = parse_arg(sys.argv[4], "--sid=", server_choices)

            acts = act_service.all(SID)
            act_choices = [str(i) for i in acts.keys() if game_config.activity_cfg[int(i)]["type"] in (200,300,328)]
            helpstr1 += """            --actid=%s    # act id""" % act_choices
            ACT_ID = parse_arg(sys.argv[5], "--actid=", act_choices)

            # ================= core ====================
            if COMMAND in ["act_fight_rank", "act_fight_target"]:
                _act_fight_send_awards(int(SID), int(ACT_ID))
            elif COMMAND in ["act_add_award"]:
                _act_add_awards_mail(int(SID), int(ACT_ID))
            else:
                pass
            # ================= ---- ====================

        elif COMMAND in ["arena_import_robots"]:
            server_choices, act_choices = [],[]

            servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
            server_choices = servers.keys()
            helpstr1 = "--sid=%s    # server id" % server_choices
            SID = parse_arg(sys.argv[4], "--sid=", server_choices)

            # ================= core ====================
            _arena_import_robots(SID)
            # ================= ---- ====================

        elif COMMAND in ["count_trial_rank", "count_arena_rank", "settle_world_boss"]:
            helpstr1 = ""
            servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
            for sid in servers:
                if COMMAND == "count_trial_rank":
                    rank_service.trial_rank_send_mail_awards(sid)
                elif COMMAND == "count_arena_rank":
                    _arena_rank_awards_mail(sid)
                elif COMMAND == "settle_world_boss":
                    _worldboss_settle_result(sid)
                else:
                    pass

        elif COMMAND in ["delete_chat_msg"]:
            server_choices = []

            servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
            server_choices = servers.keys()
            helpstr1 = "--sid=%s    # server id\n" % server_choices
            SID = parse_arg(sys.argv[4], "--sid=", server_choices)

            keywords = sys.argv[5].split("--keywords=")[1]
            tmp_msgs = redis_client.lrange(rediskey_config.CHAT_WORLD_BOX_KEY % SID, 0, 9999)
            for msg in tmp_msgs:
                msg1 = pickle.loads(msg)
                if keywords in msg1["msg"]:
                    redis_client.lrem(rediskey_config.CHAT_WORLD_BOX_KEY % SID, 1, msg)

        elif COMMAND in ["search_player_data"]:
            server_choices = []

            servers = redis_client.hgetall(rediskey_config.PLATFORM_SERVER_KEY)
            server_choices = servers.keys()
            helpstr1 = "--sid=%s    # server id\n" % server_choices
            SID = parse_arg(sys.argv[4], "--sid=", server_choices)

            user_attrs = ["uid","name","update_name_times","avatar",
                          "user_sign","account_id","platform","sid",
                          "state","type","create_time","last_request",
                          "last_sign_time","total_login_days","login_history_dates",
                          "used_cdkey_tags","game_info","vip","daily_info",
                          "task","package","hero","equip","skill","spirit",
                          "array","mission","talent","warship","mall","group",
                          "arena","trial","sign","activity"]

            helpstr1 += """            --args=%s,%s""" % ("1", user_attrs)
            tmp = sys.argv[5].split("--args=")
            args = tmp[1].split(",")
            if args[1] not in user_attrs:
                raise

            UID = "%s%s" % (SID, 10000000 + int("%07d" % int(args[0])))
            user = User.get(UID)
            if not isinstance(user, User):
                print "uid: [ %s ] not exist." % UID
            else:
                if type(eval("user.%s" % args[1])) in [unicode, str, int, dict, list, set, tuple]:
                    data = eval("user.%s" % args[1])
                    # 时间格式 特殊处理下 方便查看
                    if args[1] in ["create_time","last_request","last_sign_time"]:
                        dtime = time.localtime(int(data))
                        data = time.strftime("%F %H:%M:%S", dtime)

                    print "[ %s ]: %s" % (args[1], data)
                else:
                    attr_obj = eval("user.%s" % args[1])
                    for attr in attr_obj.all_def_attrs:
                        data = getattr(attr_obj, attr)
                        if isinstance(data, dict):
                            data = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

                        print "[ %s ]: %s" % (attr, data)

    except Exception, e:
        # raise e
        print """
useage: python tools.py
            --env=%s
            --plat=%s
            --command=%s
            %s
""" % (ENV, PLAT, COMMAND, helpstr1)

        sys.exit()
