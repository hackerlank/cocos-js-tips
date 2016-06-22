#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-24 11:21:52
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   玩家业务逻辑接口
#       1.命名 2.+(-)金币 3.+(-)元宝 4.+经验 5.+(-)体力 6.+等级
# @end
# @copyright (C) 2015, kimech

import datetime

from apps.configs import game_config
from apps.configs import static_const

from apps.misc import utils
from apps.services import name as name_service
from apps.services import cdkey as cdkey_service
from apps.services.group import GroupService

from apps.configs.msg_code import MsgCode

from .helpers import user_helper
from .helpers import common_helper
from .helpers import task_helper
from .helpers import act_helper

UPDATE_NAME_DIAMOND = 100
SKILL_POINT_DIAMOND = 50

BUY_SKILL_POINT_EACH_TIME = 20
BUY_ENERGY_EACH_TIME = 120
MAX_SIGN_LENGTH = 50
MAX_NAME_LENGTH = 12

# 兑换码的类型
CDKEY_TYPE_1 = 1  # 同类型之中，我能且仅能使用一次 别人也可以使用
CDKEY_TYPE_2 = 2  # 同类型之中，我能且仅能使用一次，我用了别人就不能再用【绝对唯一】

CDKEY_TYPE_3 = 3  # 这个类型的码我可以无限使用，但每个码只能用一次

# ========================= GAME API ==============================
def debug(context):
    """api调试工具
    """
    # 测试副本获得星星，更新临时排行榜中数据

    ki_user = context.user
    action = context.get_parameter("action")

    if action == "clean_sign_data":
        ki_user.sign.last_sign = 0
        ki_user.sign.put()

    if action == "send_mails":
        from apps.services.mail import MailService
        # send(ids, mtype, title, fromwho, msg, attachments)
        for i in range(10):
            if i % 2 == 0:
                MailService.send_system(["110000004"], "test_%s" % i, "军需官", "我要一个打五个！！", {1:10000+i})
            else:
                MailService.send_system(["110000004"], "test_%s" % i, "军需官", "我要一个打五个！！", {})

    if action == "add_items":
        items = context.get_parameter("items", "{}")
        try:
            items = eval(items)
            if not isinstance(items, dict):
                raise 1
        except:
            context.result['mc'] = MsgCode['ParamIllegal']
            return

        import apps.logics.package as pack_logic
        pack_logic.add_items(ki_user, items)

    context.result["mc"] = 100

def get_user_info(context):
    """获取其他玩家的基本数据

    Args:
        uid = "110000001"

    Returns:
        user_data
    """
    uid = context.get_parameter("uid")

    from apps.models.user import User
    user = User.get(uid)
    if not isinstance(user, User):
        context.result['mc'] = MsgCode['UserNotExist']
        return
    else:
        user_data = {}
        user_data['name'] = user.name
        user_data['level'] = user.game_info.role_level
        user_data['avatar'] = user.avatar
        user_data['vip'] = user.game_info.vip_level
        user_data['group_name'] = GroupService.get_name_by_id(user.sid, user.group.group_id)
        user_data['heros'] = user_helper.build_array_hero_data(user.array.mission, user.hero.heros)

        context.result["data"] = {}
        context.result["data"]["user_data"] = user_data

def update_name(context):
    """新玩家进入游戏给自己取名

    每个新玩家取名，只能免费取一次，之后每次花费100钻石

    Returns:
        MsgCode['UserChangeNameSucc']  40100  取名成功
        MsgCode['UserNameRepeated']  40002  该角色名已被使用
        MsgCode['UserNameIllegal']  40003  角色名包含敏感字符
    Raises:

    """
    ki_user = context.user
    register_name = context.get_parameter("name")

    need_diamond = 0 if ki_user.update_name_times == 0 else UPDATE_NAME_DIAMOND
    if not check_game_values1(ki_user, diamond=need_diamond):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    if not name_service.check_sensitive_character(register_name):
        context.result['mc'] = MsgCode['UserNameIllegal']
        return

    if utils.gbk_words_len(register_name) > MAX_NAME_LENGTH:
        context.result['mc'] = MsgCode['UserNameTooLong']
        return

    if name_service.check_name_repeated(register_name):
        context.result['mc'] = MsgCode['UserNameRepeated']
        return

    consume_game_values1(ki_user, diamond=need_diamond)
    ki_user.update_name(register_name)
    name_service.add_registered_name(register_name, ki_user.uid)

    context.result['mc'] = MsgCode['UserChangeNameSucc']

def update_avatar(context):
    """更改玩家头像

    Args:
        hero_id 新头像所属机甲ID

    Returns:

    """
    ki_user = context.user
    hero_id = context.get_parameter("hero_id")

    hero = ki_user.hero.get_by_hero_id(hero_id)
    if not hero:
        context.result['mc'] = MsgCode['HeroNotExist']
        return

    ki_user.update_avatar(hero_id)

    context.result["mc"] = MsgCode['UserUpdateAvatarSucc']

def update_sign(context):
    """更改玩家签名

    Args:
        sign 新的签名内容

    Returns:

    """
    ki_user = context.user
    sign = context.get_parameter("sign")

    if not name_service.check_sensitive_character(sign):
        context.result['mc'] = MsgCode['UserSignIllegal']
        return

    if utils.gbk_words_len(sign) > MAX_SIGN_LENGTH:
        context.result['mc'] = MsgCode['UserSignTooLong']
        return

    ki_user.update_sign(sign)

    context.result["mc"] = MsgCode['UserUpdateSignSucc']

def buy_energy(context):
    """玩家购买体力

    Args:

    Returns:

    """
    ki_user = context.user

    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)
    used_times = ki_user.daily_info.buy_energy_times
    if used_times >= vip_cfg["buy_energy_times"]:
        context.result['mc'] = MsgCode['UserTimesUseUp']
        return

    cfg = game_config.user_buy_refresh_cfg.get(used_times+1)
    if not cfg:
        last = max(game_config.user_buy_refresh_cfg.keys())
        cfg = game_config.user_buy_refresh_cfg.get(last)

    if not check_game_values1(ki_user, diamond=cfg["buy_energy"]):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    consume_game_values1(ki_user, diamond=cfg["buy_energy"])
    ki_user.game_info.update_energy(BUY_ENERGY_EACH_TIME)

    ki_user.daily_info.buy_energy_times += 1
    ki_user.daily_info.put()

    context.result["mc"] = MsgCode['UserBuyEnergySucc']

def buy_skill_point(context):
    """玩家购买技能点

    Args:

    Returns:

    """
    ki_user = context.user

    if not check_game_values1(ki_user, diamond=SKILL_POINT_DIAMOND):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    consume_game_values1(ki_user, diamond=SKILL_POINT_DIAMOND)
    ki_user.game_info.buy_skill_points(BUY_SKILL_POINT_EACH_TIME)

    context.result["mc"] = MsgCode['UserBuySkillPointSucc']

def buy_gold(context):
    """购买金币

    Args:

    Returns:

    """
    ki_user = context.user

    gtimes = context.get_parameter("type")
    vip_cfg = game_config.vip_priv_cfg.get(ki_user.game_info.vip_level)

    used_times = ki_user.daily_info.buy_gold_times
    if used_times + gtimes > vip_cfg["buy_gold_times"]:
        context.result['mc'] = MsgCode['UserTimesUseUp']
        return

    consume = 0
    for i in xrange(gtimes):
        cfg = game_config.user_buy_refresh_cfg.get(used_times+i+1)
        if not cfg:
            last = max(game_config.user_buy_refresh_cfg.keys())
            cfg = game_config.user_buy_refresh_cfg.get(last)

        consume += cfg["buy_gold"]

    if not check_game_values1(ki_user, diamond=consume):
        context.result['mc'] = MsgCode['DiamondNotEnough']
        return

    random_lib = game_config.user_buy_gold_crit_cfg.get(ki_user.game_info.vip_level)

    get_gold = 0
    all_crit_times = []
    for i in xrange(gtimes):
        crit_times = common_helper.weight_random(random_lib)
        all_crit_times.append(crit_times)
        get_gold += (22000 + (ki_user.game_info.role_level - 1) * 200) * crit_times

    consume_game_values1(ki_user, diamond=consume)
    add_game_values(ki_user, {1: get_gold})

    ki_user.daily_info.buy_gold_times += gtimes
    ki_user.daily_info.put()

    context.result["data"] = {}
    context.result["data"]["gold"] = get_gold
    context.result["data"]["crit_times"] = all_crit_times

def cdkey(context):
    """激活码兑换奖品

    Args:

    Returns:

    """
    ki_user = context.user
    code = context.get_parameter("code")

    if len(code) != 10:
        context.result['mc'] = MsgCode['ParamIllegal']
        return

    # 大小写不敏感
    code = code.upper()
    key_tag = code[:4]
    tag_cfg = game_config.gift_key_config.get(key_tag, {})
    # 检测是否存在
    if not tag_cfg:
        context.result['mc'] = MsgCode['CDKeyNotExist']
        return

    # 检测是否生效，过期
    if not _check_key_effective(tag_cfg["date_start"], tag_cfg["date_end"]):
        context.result['mc'] = MsgCode['CDKeyNotEffective']
        return

    # 检测是否存在
    if not cdkey_service.check_code_exist(code):
        context.result['mc'] = MsgCode['CDKeyNotExist']
        return

    # 同类型是否在重复使用
    if tag_cfg["type"] in [CDKEY_TYPE_1, CDKEY_TYPE_2] and key_tag in ki_user.used_cdkey_tags:
        context.result['mc'] = MsgCode['CDKeyCantRepeat']
        return

    # 兑换码是否被其他玩家使用
    if tag_cfg["type"] in [CDKEY_TYPE_2, CDKEY_TYPE_3] and cdkey_service.check_code_used_by_other(code):
        context.result['mc'] = MsgCode['CDKeyAlreadyUsedByOther']
        return

    import apps.logics.package as pack_logic
    pack_logic.add_items(ki_user, tag_cfg["award"])

    if tag_cfg["type"] in [CDKEY_TYPE_1, CDKEY_TYPE_2]:
        ki_user.used_cdkey_tags.append(key_tag)
        ki_user.put()

    if tag_cfg["type"] in [CDKEY_TYPE_2, CDKEY_TYPE_3]:
        cdkey_service.update_cdkey_info(code, ki_user.uid)

    data = {}
    data["award"] = tag_cfg["award"]

    context.result["data"] = data

def skip_guide(context):
    """跳过某步引导

    Args:

    Returns:

    """
    ki_user = context.user

    step = context.get_parameter("step")

    ki_user.game_info.last_guide_id = step
    ki_user.game_info.put()

    context.result["mc"] = MsgCode['UserSkipGuideSucc']

# ========================= PROCESS API =============================
def add_game_values(user, items):
    """游戏数值增长接口

    金币，钻石，体力，经验，vip经验...

    Args:
        user  用户对象
        items  参数字典  eg: {1:1000, 2:1000}

    Returns:

    """
    for key, value in items.iteritems():
        if key == static_const.ROLE_EXP:
            add_items = user.game_info.add_role_exp(value)
            # 升级给物品。为了引导而搞
            if add_items:
                from apps.logics import package as pack_logic
                pack_logic.add_items(user, pack_logic.amend_goods(add_items))

        elif key == static_const.VIP_EXP:
            user.game_info.add_vip_exp(value)

        elif key == static_const.ENERGY:
            user.game_info.update_energy(value)

        else:
            # 等级和vip等级不能直接修改数值，只能通过经验来更变
            if key in [5,7]:
                return

            value_tag = static_const.SPECIAL_ITEMS_MAPPING.get(key, None)
            if value_tag:
                exec("user.game_info.%s += %s" % (value_tag, value))

    user.game_info.put()

def consume_game_values(user, items):
    """玩家使用游戏数值

    金币，钻石，体力，荣誉点....

    Args:
        user  用户对象
        items  参数字典 eg: {1:1000, 2:1000}

    Returns:

    """
    for key, value in items.iteritems():
        # 1 -> "gold", 2 -> "diamond" ....
        value_tag = static_const.SPECIAL_ITEMS_MAPPING.get(key, None)
        if value_tag:
            exec("user.game_info.%s -= value" % value_tag)

    user.game_info.put()

    # 消耗了钻石，检测每日任务中消耗钻石类的任务
    for key, value in items.iteritems():
        if key == static_const.DIAMOND:
            task_helper.task_checker_13(user, value)
            act_helper.update_after_use_diamond(user, value)

def consume_game_values1(user, **kwargs):
    """玩家使用游戏数值

    使用示例：consume_game_values1(user, gold=100, diamond=10, role_exp=1000)

    Args:
        kwargs: {"gold": 100, "diamond": 10, "role_exp": 1000}
    """
    for key, value in kwargs.iteritems():
        try:
            exec("user.game_info.%s -= %s" % (key, value))
        except:
            pass

    user.game_info.put()

    try:
        # 消耗了钻石，检测每日任务中消耗钻石类的任务
        for key, value in kwargs.iteritems():
            if key == "diamond":
                task_helper.task_checker_13(user, value)
                act_helper.update_after_use_diamond(user, value)
    except Exception,e:
        print e

def check_game_values(user, items):
    """检测玩家的xx东西是否足够

    Args:
        user  User  玩家对象
        items  参数字典 eg: {1:1000, 2:1000}

    Returns:
        bool

    """
    result_set = []
    for key, value in items.iteritems():
        # 1 -> "gold", 2 -> "diamond" ....
        value_tag = static_const.SPECIAL_ITEMS_MAPPING.get(key, None)
        try:
            had = eval("user.game_info.%s" % value_tag)
        except:
            had = 0

        result_set.append(had >= value)

    return False not in result_set

def check_game_values1(user, **kwargs):
    """检测玩家的xx东西是否足够

    使用示例：check_game_values1(user, gold=100, diamond=10, role_exp=1000)

    Args:
        kwargs: {"gold": 100, "diamond": 10, "role_exp": 1000}
    """
    result_set = []

    for key, value in kwargs.iteritems():
        try:
            had = eval("user.game_info.%s" % key)
        except:
            had = 0

        result_set.append(had >= value)

    return False not in result_set

def fetch_user_info(uid):
    """根据玩家uid获取基础信息

    使用场景：
    1. 聊天信息，私聊对象的名字

    Args:
        uid 玩家UID

    """
    user_data = {}
    from apps.models.user import User
    user = User.get(uid)
    if isinstance(user, User):
        user_data['name'] = user.name
        user_data['level'] = user.game_info.role_level
        user_data['avatar'] = user.avatar
        user_data['vip'] = user.game_info.vip_level
        user_data['group_name'] = GroupService.get_name_by_id(user.sid, user.group.group_id)

    return user_data

def _check_key_effective(start, end):
    """检测激活码是否生效

    Args:
        start :(2015, 11, 11) 生效的年月日
        end :(2015, 11, 11) 过期的年月日

    Returns:
        bool
    """
    today = datetime.date.today()
    today_set = (today.year, today.month, today.day)

    if start <= today_set < end:
        return True
    else:
        return False
