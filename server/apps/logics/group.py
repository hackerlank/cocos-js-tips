#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-12-30 21:11:30
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   公会业务接口:
#       1.创建公会
#       2.查找公会（类型 1-按条件查找 2-快速查找）
#       3.（申请）加入公会
#       4.退出（解散）公会
#     成员:
#       5.请求公会各类数据
#       6.捐献
#     官员：
#       7.变更职务
#       8.踢人
#       9.更新公会信息
#       10.审核申请
# @end
# @copyright (C) 2015, kimech

import time
import copy

from apps.configs import game_config
from apps.configs.msg_code import MsgCode

from apps.services import rank as rank_service
from apps.services import name as name_service
from apps.services.mail import MailService
from apps.services.group import *

from apps.logics import user as user_logic
from apps.logics import package as pack_logic
from apps.logics.helpers import common_helper

GROUP_CREATE_FUNC_ID = 5000
GROUP_CREATE_DIAMOND = 300

JOIN_CD = 6 * 3600
DAILY_DONATE_TIMES = 5
DAILY_MAX_GROUP_EXP = 10000

GAME_BIRD_DIAMOND_LIMIT = 50
GAME_BIRD_CHIP_LIMIT = 2
GAME_BIRD_CHIP_ID = 120113
# ========================= GAME API ==============================
def info(context):
    """获取公会基础数据

    主界面:
    1.公告 2.等级

    大厅:
    1.图标 2.id 3.名称 4.会长 5.人数 6.等级 7.排名 8.成员列表

    审核:
    1.申请条件 2.限制加入状态 3.申请信息

    日志:
    1.日志

    研究院:
    1.等级 2.经验 3.今日公会经验 4.今日捐献次数

    Args:

    Returns:

    """
    ki_user = context.user

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    game_data = copy.deepcopy(group_data)

    group_data_s2c = build_group_info_s2c(ki_user.sid, game_data)
    member_info = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    group_data_s2c["my_position"] = member_info["position"] if member_info else 0

    context.result["data"] = {}
    context.result["data"]["group_data"] = group_data_s2c

def info1(context):
    """获取列表类数据

    Args:
        itype 数据类型 1-成员列表 2-申请列表 3-日志列表
        start 起始位置
        end 结束位置

    Returns:

    """
    ki_user = context.user

    itype = context.get_parameter("itype")
    start = context.get_parameter("start")
    end = context.get_parameter("end")

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    data = {}
    if itype == 1:
        data["list"] = GroupService.members(ki_user.sid, group_id, start, end)

    elif itype == 2:
        mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
        if not mydata or (mydata["position"] not in [GROUP_POSITION_MASTER, GROUP_POSITION_MASTER2]):
            context.result['mc'] = MsgCode['GroupHaveNoAuth']
            return

        requests = GroupService.join_requests(ki_user.sid, group_id, start, end)
        data["list"] = requests

    elif itype == 3:
        logs = GroupService.logs(ki_user.sid, group_id, start, end)
        data["list"] = logs

    else:
        data["list"] = []

    context.result["data"] = data

def rank(context):
    """获取公会排行榜数据

    Args:
        type 1-公会排行 2-小鸟成绩排行 3-老虎机排行榜
        start 排行榜起始位置
        end 排行榜结束位置

    Returns:
        rank_datas 对应条件的排行榜数据
    """
    ki_user = context.user

    rtype = context.get_parameter("type")
    start = context.get_parameter("start")
    end = context.get_parameter("end")

    data = {}
    if rtype == 1:
        rank_datas = GroupService.rank(ki_user.sid, start, end)
        count = GroupService.groupcount(ki_user.sid)

        data["count"] = count
        data["rank_datas"] = rank_datas

    elif rtype == 2:
        rank_datas = GroupService.bird_rank(ki_user.sid, ki_user.group.group_id, start, end)
        data["rank_datas"] = rank_datas

    elif rtype == 3:
        rank_datas = GroupService.tiger_rank(ki_user.sid, ki_user.group.group_id, start, end)
        data["rank_datas"] = rank_datas

    else:
        pass

    context.result["data"] = data

def game_info(context):
    """获取公会游戏&活动数据

    Args:
        game_type 1-老虎机

    Returns:

    """
    ki_user = context.user

    game_type = context.get_parameter("game_type")

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    info = {}
    if game_type == 1:
        times1, times2 = ki_user.daily_info.group_info["tiger_time1"], ki_user.daily_info.group_info["tiger_time2"]
        info["daily_info"] = {"tiger_time1": times1, "tiger_time2": times2}
        points, times = ki_user.group.game_data["tiger_points"], ki_user.group.game_data["tiger_change_times"]
        exp1, exp2 = ki_user.group.donate["tiger_exp1"], ki_user.group.donate["tiger_exp2"]
        info["game_data"] = {"points": points, "xtimes": times, "exp1": exp1, "exp2": exp2}
    elif game_type == 2:
        info["daily_info"] = {
                                "bird_time": ki_user.daily_info.group_info["bird_times"],
                                "got_awards": ki_user.daily_info.group_info["bird_awards"],
                                "daily_best": ki_user.daily_info.group_info["bird_daily_best"]
                            }
        info["game_data"] = {
                                "exp1": ki_user.group.donate["bird_exp1"],
                                "exp2": ki_user.group.donate["bird_exp2"],
                                "history_best": ki_user.group.game_data["bird_best_score"],
                            }
    else:
        info["daily_info"] = {}
        info["game_data"] = {}

    context.result["data"] = info

def create(context):
    """创建公会

    Args:
        name  社团名称
        icon  社团徽章

    Returns:

    """
    ki_user = context.user

    name = context.get_parameter("name")
    icon = context.get_parameter("icon")

    if ki_user.group.group_id:
        context.result['mc'] = MsgCode['GroupAlreadyInGroup']
        return

    # 检测等级
    need_level = game_config.user_func_cfg.get(GROUP_CREATE_FUNC_ID)
    if need_level > ki_user.game_info.role_level:
        context.result['mc'] = MsgCode['UserLevelTooLow']
        return

    # 检测花费
    if not user_logic.check_game_values1(ki_user, diamond=GROUP_CREATE_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    # 检测名字重复
    if name_service.check_name_repeated(name, 2):
        context.result['mc'] = MsgCode['GroupNameRepeated']
        return

    # 扣除消耗
    user_logic.consume_game_values1(ki_user, diamond=GROUP_CREATE_DIAMOND)
    # 创建公会
    creater = {"uid": ki_user.uid, "name": ki_user.name}
    group_id = GroupService.create(ki_user.sid, name, icon, creater)
    # 更改自己的公会数据
    ki_user.group.group_id = group_id
    ki_user.group.put()

    data = {}
    data["group_id"] = group_id

    context.result['data'] = data

def search(context):
    """查找公会

    Args:
        key 关键字 公会名称或ID

    Returns:

    """
    ki_user = context.user

    key = context.get_parameter("key")
    # 先根据名称查，然后根据ID查
    data = {}
    group_data = GroupService.find(ki_user.sid, key, 1)
    if not group_data:
        group_data = GroupService.find(ki_user.sid, key)

    context.result["data"] = {}
    context.result["data"]["group_data"] = build_group_info_s2c(ki_user.sid, group_data)

def quick_search(context):
    """快速加入

    遍历公会排行中玩家可直接加入满足加入限制等级、自由加入和人数未满的公会，
    选排名靠前的公会进行加入申请，弹出加入公会提示框，流程同手动申请流程

    Args:

    Returns:

    """
    ki_user = context.user

    if ki_user.group.group_id:
        context.result['mc'] = MsgCode['GroupAlreadyInGroup']
        return

    now = int(time.time())
    if now - ki_user.group.cd <= JOIN_CD:
        context.result['mc'] = MsgCode['GroupInCD']
        return

    data = {}
    group_data = GroupService.quick_search(ki_user.sid, ki_user.game_info.role_level)

    context.result["data"] = {}
    context.result["data"]["group_data"] = build_group_info_s2c(ki_user.sid, group_data)

def update(context):
    """更新公会信息

    Args:
        items 变更项

    Returns:

    """
    ki_user = context.user

    items = context.get_parameter("items", "{}")

    try:
        items = eval(items)
        if not isinstance(items, dict):
            raise 1

        # 可变更的属性
        can_update_fields = ["join_level_limit", "join_state", "notice", "icon"]
        if len(set(items.keys()).difference(can_update_fields)) != 0:
            raise 1
    except:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    group_id = ki_user.group.group_id
    # 检测权限
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    if not mydata or (mydata["position"] not in [GROUP_POSITION_MASTER, GROUP_POSITION_MASTER2]):
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    GroupService.update(ki_user.sid, group_id, items)
    context.result['mc'] = MsgCode['GroupUpdateSucc']

def appoint(context):
    """任命职务

    Args:
        member_uid 成员ID
        position 职位类型 1-会长 2-副会长 2-精英 4-成员

    Returns:

    """
    ki_user = context.user

    member_uid = context.get_parameter("member_uid")
    position = context.get_parameter("position")

    group_id = ki_user.group.group_id
    # 检测权限
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    # 不能任命自己
    if member_uid == ki_user.uid:
        context.result['mc'] = MsgCode['GroupCantAppointSelf']
        return

    mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    # 只有会长有任命别人的权利
    if not mydata or mydata["position"] != GROUP_POSITION_MASTER:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    member_data = GroupService.get_member_info_by_uid(ki_user.sid, group_id, member_uid)
    # 检测目标是否在公会
    if not member_data:
        context.result['mc'] = MsgCode['GroupMemberNotExist']
        return

    if member_data["position"] == position:
        context.result['mc'] = MsgCode['GroupMemberAlreayInPosition']
        return

    # 检测职位人数是否已达上限
    count = GroupService.get_position_number(ki_user.sid, group_id, position)
    if position == GROUP_POSITION_MASTER2 and count >= GROUP_POSITION_MASTER2_NUMBER:
        context.result['mc'] = MsgCode['GroupPositionFull']
        return
    elif position == GROUP_POSITION_ELITE and count >= GROUP_POSITION_ELITE_NUMBER:
        context.result['mc'] = MsgCode['GroupPositionFull']
        return
    else:
        pass

    # 执行任命操作
    GroupService.appoint(ki_user.sid, group_id, ki_user.uid, member_uid, position)

    context.result['mc'] = MsgCode['GroupAppointSucc']

def quit(context):
    """退出&解散公会

    如果退出者是工会最后一名成员  则解散公会

    Args:

    Returns:

    """
    ki_user = context.user

    group_id = ki_user.group.group_id
    # 判断玩家当前无公会
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    # 判断公会存在
    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    # 退出者如果为会长 则不能退出 除非只剩下自己一个人
    member_data = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    if member_data["position"] == GROUP_POSITION_MASTER and group_data["member_number"] > 1:
        context.result['mc'] = MsgCode['GroupMasterCantQuit']
        return

    GroupService.quit(ki_user.sid, group_id, ki_user.uid, ki_user.name)
    ki_user.group.quit()

    context.result['mc'] = MsgCode['GroupQuitSucc']

def kick(context):
    """踢人

    Args:
        member_uid 被踢者UID

    Returns:

    """
    ki_user = context.user

    member_uid = context.get_parameter("member_uid")

    # 不能任命自己
    if member_uid == ki_user.uid:
        context.result['mc'] = MsgCode['GroupCantKickSelf']
        return

    group_id = ki_user.group.group_id
    mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    # 只有会长 副会长有踢别人的权利
    if not mydata or mydata["position"] not in [GROUP_POSITION_MASTER, GROUP_POSITION_MASTER2]:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    member_data = GroupService.get_member_info_by_uid(ki_user.sid, group_id, member_uid)
    # 检测目标是否在公会
    if not member_data:
        context.result['mc'] = MsgCode['GroupMemberNotExist']
        return

    # 副会长不能踢副会长
    if mydata["position"] != GROUP_POSITION_MASTER2 \
        and member_data["position"] == GROUP_POSITION_MASTER2:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    # 会长不能被踢出
    if member_data["position"] == GROUP_POSITION_MASTER:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    GroupService.kick(ki_user.sid, group_id, member_uid)

    context.result['mc'] = MsgCode['GroupKickSucc']

def apply(context):
    """申请&加入公会

    如果申请对象进入状态为自由  则直接加入
    如果申请对象进入状态为需申请  则直接进入申请列表

    Args:
        group_id 目标公会ID

    Returns:

    """
    ki_user = context.user

    group_id = context.get_parameter("group_id")
    # 判断玩家当前无公会
    if ki_user.group.group_id:
        context.result['mc'] = MsgCode['GroupAlreadyInGroup']
        return

    now = int(time.time())
    if now - ki_user.group.cd <= JOIN_CD:
        context.result['mc'] = MsgCode['GroupInCD']
        return

    # 判断公会存在
    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    mylevel = ki_user.game_info.role_level
    if group_data["join_level_limit"] and mylevel < group_data["join_level_limit"]:
        context.result['mc'] = MsgCode['GroupLevelTooLow']
        return

    # 判断公会加入条件满足
    if group_data["join_state"] == GROUP_JOIN_STATE_BAN:
        context.result['mc'] = MsgCode['GroupCantJoin']
        return

    # 判断公会人数是否已满
    cfg = game_config.group_cfg.get(group_data["level"], {})
    max_number = cfg["max_member"] if cfg else 0
    if group_data["member_number"] >= max_number:
        context.result['mc'] = MsgCode['GroupFull']
        return

    if group_data["join_state"] == GROUP_JOIN_STATE_FREE:
        # 自由加入逻辑
        GroupService.agree(ki_user.sid, group_id, ki_user.uid, 2)
        ki_user.group.join(group_id)
    else:
        if GroupService.check_in_apply_list(ki_user.sid, group_id, ki_user.uid):
            context.result['mc'] = MsgCode['GroupAlreadyApplied']
            return

        # 申请逻辑
        GroupService.join_request(ki_user.sid, group_id, ki_user.uid)

    context.result['mc'] = MsgCode['GroupApplySucc']

def review(context):
    """审核，查询

    帮主或者副帮主审核玩家的加入申请

    Args:
        request_id 申请编号
        result 审核结果 0-拒绝 1-同意

    Returns:

    """
    ki_user = context.user

    request_id = context.get_parameter("request_id")
    result = context.get_parameter("result")

    group_id = ki_user.group.group_id
    mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    # 只有会长 副会长有审核申请的权利
    if not mydata or mydata["position"] not in [GROUP_POSITION_MASTER, GROUP_POSITION_MASTER2]:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    # 判断公会存在
    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    # 判断公会人数是否已满
    cfg = game_config.group_cfg.get(group_data["level"], {})
    max_number = cfg["max_member"] if cfg else 0
    if group_data["member_number"] >= max_number:
        context.result['mc'] = MsgCode['GroupFull']
        return

    if result:
        # 查找申请单子是否存在
        request = GroupService.search_request(ki_user.sid, group_id, request_id)
        if not request:
            context.result['mc'] = MsgCode['GroupRequestNotExist']
            return

        GroupService.delete_request(ki_user.sid, group_id, request_id)

        # 确认申请玩家当前是否已加入公会
        applyer_uid = request["uid"]
        if GroupService.check_player_has_group(ki_user.sid, applyer_uid):
            context.result['mc'] = MsgCode['GroupUserHasGroup']
            return

        GroupService.agree(ki_user.sid, group_id, str(request["uid"]), 1)
    else:
        # 如果拒绝玩家加入。直接删掉申请，减少操作复杂度
        GroupService.delete_request(ki_user.sid, group_id, request_id)

    context.result['mc'] = MsgCode['GroupReviewSucc']

def deny_all(context):
    """拒绝所有玩家申请

    帮主或者副帮主审核

    Args:

    Returns:

    """
    ki_user = context.user

    group_id = ki_user.group.group_id
    mydata = GroupService.get_member_info_by_uid(ki_user.sid, group_id, ki_user.uid)
    # 只有会长 副会长有审核申请的权利
    if not mydata or mydata["position"] not in [GROUP_POSITION_MASTER, GROUP_POSITION_MASTER2]:
        context.result['mc'] = MsgCode['GroupHaveNoAuth']
        return

    GroupService.delete_all_request(ki_user.sid, group_id)

    context.result['mc'] = MsgCode['GroupHandleSucc']

def donate(context):
    """公会成员捐献

    Args:
        target 捐献目标 1-公会经验 2-老虎机参与次数 3-老虎机改投次数 4-小鸟次数 5-小鸟金币上限加成
        type 捐献类型

    Returns:

    """
    ki_user = context.user

    target = context.get_parameter("target")
    dtype = context.get_parameter("type")

    if target not in [1,2,3,4,5] or dtype not in [1,2,3,4,5]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    if target == 1 and dtype == 3 and not vip_cfg["group_advance_donate"]:
        context.result['mc'] = MsgCode['UserVipTooLow']
        return

    group_daily_data = ki_user.daily_info.group_info
    # 每日次数已用完
    if group_daily_data["donate_times"] >= DAILY_DONATE_TIMES:
        context.result['mc'] = MsgCode['GroupDonateTimesUseUp']
        return

    # 判断公会存在
    group_data = GroupService.find(ki_user.sid, group_id)
    if not group_data:
        context.result['mc'] = MsgCode['GroupNotExist']
        return

    if target == 1 and group_data["daily_exp"] >= DAILY_MAX_GROUP_EXP:
        context.result['mc'] = MsgCode['GroupDailyExpMax']
        return

    # TODO 根据捐献类型获取玩家捐献消费和获得数值
    cfg = game_config.group_donate_cfg.get("%s-%s" % (target, dtype))
    if not pack_logic.check_items_enough(ki_user, cfg["consume"]):
        if 1 in cfg["consume"].keys():
            context.result['mc'] = MsgCode['GoldNotEnough']
            return

        if 2 in cfg["consume"].keys():
            context.result['mc'] = MsgCode['DiamondNotEnough']
            return

    pack_logic.remove_items(ki_user, cfg["consume"])
    exp, tag = cfg["exp"].get(target), "%s#%s" % (target, dtype)
    if target == 1:
        GroupService.donate(ki_user.sid, group_id, ki_user.uid, ki_user.name, exp, tag)
    else:
        ki_user.group.donate_game_exp(target, exp)
        GroupService.create_group_log(ki_user.sid, group_id, GROUP_LOG_TYPE_DONATE, ki_user.uid, ki_user.name, int(time.time()), tag)

    # 增加帮贡
    ki_user.game_info.group_point += cfg["group_point"]
    ki_user.game_info.put()

    # 更新公会成员贡献
    GroupService.set_member_info_by_uid(ki_user.sid, group_id, ki_user.uid, "donate", cfg["group_point"])

    ki_user.daily_info.group_update("donate_times")

    context.result['mc'] = MsgCode['GroupDonateSucc']

def game_tiger(context):
    """【公会游戏之老虎机】

    Args:
        type 操作类型 1-投掷 2-改投 3-领取

    Returns:

    """
    ki_user = context.user

    action_type = context.get_parameter("type")

    if action_type not in [1,2,3]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    data = {}
    group_daily_data = ki_user.daily_info.group_info
    if action_type == 1:
        max_times = get_game_max_times(1, ki_user.group.donate["tiger_exp1"])
        if group_daily_data["tiger_time1"] >= max_times:
            context.result['mc'] = MsgCode['GroupGameTigerTimesUseUp']
            return

        # 如果之前的还没领取，不能直接参与
        if ki_user.group.game_data["tiger_points"] != -1:
            context.result['mc'] = MsgCode['GroupGameTigerAlreayIn']
            return

        point = random_tiger_point(0)
        ki_user.group.tiger_update(point, 0)

        data["point"] = point

    elif action_type == 2:
        # 都还没投掷，改个毛线
        if ki_user.group.game_data["tiger_points"] == -1:
            context.result['mc'] = MsgCode['GroupGameTigerNotIn']
            return

        # 都已经满了 改个毛线
        if ki_user.group.game_data["tiger_points"] == 5:
            context.result['mc'] = MsgCode['GroupGameTigerFull']
            return

        max_free_times = get_game_max_times(2, ki_user.group.donate["tiger_exp2"])
        # 免费的已经用完，可以花钻石改投
        need_diamond = 0
        if group_daily_data["tiger_time2"] >= max_free_times:
            # 检测花费
            not_free_times = ki_user.group.game_data["tiger_change_times"]+1
            need_diamond = game_config.user_buy_refresh_cfg[not_free_times]["group_game_tiger_refresh"]
            if not user_logic.check_game_values1(ki_user, diamond=need_diamond):
                context.result['mc'] = MsgCode['DiamondNotEnough']
                return

        point = random_tiger_point(ki_user.group.game_data["tiger_points"])
        if need_diamond:
            user_logic.consume_game_values1(ki_user, diamond=need_diamond)
            ki_user.group.tiger_update(point, ki_user.group.game_data["tiger_change_times"]+1)  # 花了钱的
        else:
            ki_user.group.tiger_update(point, ki_user.group.game_data["tiger_change_times"])
            ki_user.daily_info.group_update("tiger_time2")

        data["point"] = point

    elif action_type == 3:
        point = ki_user.group.game_data["tiger_points"]
        if point == -1:
            context.result['mc'] = MsgCode['GroupGameTigerNotIn']
            return

        awards = game_config.group_game_tiger_awards_cfg[point]
        pack_logic.add_items(ki_user, awards)
        ki_user.group.tiger_update(-1, 0)
        ki_user.daily_info.group_update("tiger_time1")

        # 进入排行榜
        GroupService.update_game_tiger_rank(ki_user.sid, ki_user.uid, ki_user.group.group_id, point)

        if point == 5:
            GroupService.create_group_log(ki_user.sid, group_id, GROUP_LOG_TYPE_GAME_TIGER, ki_user.uid, ki_user.name, int(time.time()), point)
    else:
        pass

    context.result['mc'] = MsgCode['GroupGameTigerSucc']
    context.result['data'] = data

def game_bird(context):
    """【公会游戏之小鸟快飞】

    Args:
        type 游戏操作类型 1-开始 2-结算
        process 进度

    Returns:

    """
    ki_user = context.user

    action_type = context.get_parameter("type")
    process = context.get_parameter("process")

    if action_type not in [1,2]:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    group_id = ki_user.group.group_id
    if not group_id:
        context.result['mc'] = MsgCode['GroupHaveNoGroup']
        return

    data = {}
    group_daily_data = ki_user.daily_info.group_info
    if action_type == 1:
        max_times = get_game_max_times(3, ki_user.group.donate["bird_exp1"])
        if group_daily_data["bird_times"] >= max_times:
            context.result['mc'] = MsgCode['GroupGameBirdTimesUseUp']
            return

        ki_user.daily_info.group_update("bird_times")

    elif action_type == 2:
        awards = [v for k,v in game_config.group_game_bird_awards_cfg.items() if k <= process]  # [{1:2000}, {2:3}, {120001:1}]
        if not awards:
            context.result['mc'] = MsgCode['ParamIllegal']
            return

        daily_awards = group_daily_data["bird_awards"]
        awards1 = pack_logic.amend_goods(awards) # {1:2000, 2:3, 120001:1}
        gold_limit = get_game_max_times(4, ki_user.group.donate["bird_exp2"])
        history, add_awards = count_add_awards(awards1, daily_awards, gold_limit)

        # 背包增加物品
        pack_logic.add_items(ki_user, add_awards)

        if process > ki_user.group.game_data["bird_best_score"]:
            ki_user.group.bird_update(process)

        if process > group_daily_data["bird_daily_best"]:
            group_daily_data["bird_daily_best"] = process
            GroupService.update_game_bird_rank(ki_user.sid, ki_user.uid, ki_user.group.group_id, process) # 进入排行榜

        ki_user.daily_info.group_game_bird_update("bird_awards", history)

        # if process == 5:
        #     GroupService.create_group_log(ki_user.sid, group_id, GROUP_LOG_TYPE_GAME_TIGER, ki_user.uid, ki_user.name, int(time.time()), point)
    else:
        pass

    context.result['mc'] = MsgCode['GroupGameBirdSucc']

# =======================================================================
def build_group_info_s2c(sid, info):
    """
    """
    if not info:
        return {}

    base_info = "{'group_id':%(id)s,'icon':%(icon)s,'daily_exp':%(daily_exp)s,'exp':%(exp)s,'name':'%(name)s', \
                  'join_level_limit':%(join_level_limit)s,'join_state':%(join_state)s, \
                  'member_number':%(member_number)s,'notice':'%(notice)s'}" % info
    base_info = eval(base_info)
    base_info["rank"] = rank_service.grouprank(sid, info["id"])
    base_info["master"] = GroupService.get_master_name_by_uid(info["master"])

    return base_info

def get_game_max_times(etype, exp):
    """
    """
    if etype == 1:
        cfg = game_config.group_game_tiger_exp1_cfg
        field = "tiger_times_a"
    elif etype == 2:
        cfg = game_config.group_game_tiger_exp2_cfg
        field = "tiger_times_b"
    elif etype == 3:
        cfg = game_config.group_game_bird_exp1_cfg
        field = "bird_times_a"
    elif etype == 4:
        cfg = game_config.group_game_bird_exp2_cfg
        field = "bird_gold_limit"
    else:
        return 0

    level = common_helper.get_level_by_exp(cfg, exp)
    return game_config.group_cfg[level][field]

def random_tiger_point(point):
    """随机老虎机里威震天个数

    Args:
        point 当前威震天个数

    """
    cfgs = [{c["id"]: c["weight"]} for c in game_config.group_game_tiger_cfg.values() if c["cur_num"] == point]
    target = common_helper.weight_random(pack_logic.amend_goods(cfgs))

    return game_config.group_game_tiger_cfg[target]["final_num"]

def count_add_awards(awards, history, gold_limit):
    """计算最后获得的物品
    """
    his_gold = history.get(1, 0)
    add_gold = awards.get(1, 0) + his_gold
    gold = min(gold_limit, add_gold)

    his_diamond = history.get(2, 0)
    add_diamond = awards.get(2, 0) + his_diamond
    diamond = min(GAME_BIRD_DIAMOND_LIMIT, add_diamond)

    his_chip = history.get(GAME_BIRD_CHIP_ID, 0)
    add_chip = awards.get(GAME_BIRD_CHIP_ID, 0) + his_chip
    chip = min(GAME_BIRD_CHIP_LIMIT, add_chip)

    return {1:gold, 2:diamond, GAME_BIRD_CHIP_ID:chip}, {1:gold-his_gold, 2:diamond-his_diamond, GAME_BIRD_CHIP_ID:chip-his_chip}
