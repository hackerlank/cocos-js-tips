#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-10 21:44:47
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     排行榜逻辑
# @end
# @copyright (C) 2015, kimech

from apps.services import rank as rank_service
from apps.services.group import GroupService
from torngas.settings_manager import settings

from apps.configs.msg_code import MsgCode

# ========================= GAME API ==============================
def get(context):
    """获取排行榜数据

    Args:
        rtype 排行榜类型
        start 排行榜起始位置
        end 排行榜结束位置

    Returns:
        my_rank 我的名次
        rank_datas 对应条件的排行榜数据
    """
    rtype = context.get_parameter("rtype")
    start = context.get_parameter("start")
    stop = context.get_parameter("stop")

    if rtype not in rank_service.RANK_KEY_MAPPING:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    ki_user = context.user
    if rtype == 3:
        my_rank = rank_service.rank(ki_user.sid, rtype, "%s_%s" % (ki_user.uid, ki_user.hero.get_max_fight_hero()))
    elif rtype == 2:
        my_rank = rank_service.rank(ki_user.sid, rtype, ki_user.group.group_id)
        if not my_rank and ki_user.group.group_id:
            group_data = GroupService.find(ki_user.sid, ki_user.group.group_id)
            my_rank = _build_group_data_s2c(group_data, ki_user.sid)
    else:
        my_rank = rank_service.rank(ki_user.sid, rtype, ki_user.uid)

    rank_datas = rank_service.top(ki_user.sid, rtype, start, stop)

    data = {}
    data["my_rank"] = my_rank
    data["rank_datas"] = rank_datas

    context.result["data"] = data

# ============================================================
def _build_group_data_s2c(data, sid):
    """未上榜的公会只传基础数据
    """
    temp = {}
    temp["name"] = data["name"]
    temp["master"] = GroupService.get_master_name_by_uid(data["master"])
    temp["icon"] = data["icon"]
    temp["level"] = data["level"]
    temp["rank"] = 0
    temp["fight"] = sum([member["fight"] for member in GroupService.members(sid, int(data["id"])) if isinstance(member, dict)])

    return temp
