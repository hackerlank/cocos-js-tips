#!/usr/bin/env python
# encoding: utf-8

# @Date : 2015-08-19 14:18:34
# @Author : Jiank (http://jiankg.github.com)
# @doc
#      用户数据
# @end
# @copyright (C) 2015, kimech

import time
import logging
import datetime

from apps.misc import utils
from apps.misc import auth_utils
from apps.configs import static_const
from libs.rklib.model import BaseModel
from apps.configs import game_config
from apps.logics.helpers import act_helper

from apps.logics.helpers import common_helper

from apps.services.mail import MailService
from apps.services import name as name_service
from apps.services import pregift as pregift_service
from apps.services.statistics import Statictics as stat_service

from apps.models.account import Account

from libs.rklib.core import app
from apps.configs import rediskey_config

redis_client = app.get_storage_engine('redis').client.current

class User(BaseModel):
    """
    角色基本信息

    Attributes:
        uid  # 角色ID :str
        name  # 名称 :str
        update_name_times # 修改名字的次数
        avatar # 头像 存储的机甲的ID
        sign  # 个人签名
        account_id  # 平台赋予玩家的id :str
        platform  # 角色当前所在平台 :str
        sid  # 玩家当前所在服务器id :str
        state  # 账号状态(0-正常 1-冻结) :int
        create_time  # 添加应用时间 :timestamp
        last_request  # 上一次请求时间 :timestamp
        last_sign_time # 上一次登录时间
        total_login_days # 总共登陆天数 :int
        login_history_dates  # 本次登录与上一次登录间隔天数

        login_info  # 登录信息

        game_info  # 角色游戏信息
        daily_info  # 每日数据信息
        task      # 任务数据
        package  # 角色包裹
        hero     # 姬甲
        equip  # 装备
        skill  # 技能
        spirit # 战魂
        mission # 副本数据
        array   # 阵列数据
        talent   # 天赋数据
        warship  # 战舰数据
        mall    # 商店数据
        group   # 帮派数据
        arena    # 竞技场数据
        trial    # 试炼数据
        activity     # 运维活动数据
    """

    def __init__(self, uid=None):
        """初始化角色基本信息

        Args:
            uid: 角色游戏ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色uid
        self.name = ""
        self.update_name_times = 0   # 更改名字的次数
        self.avatar = static_const.USER_DEFAULT_HERO  # 默认头像为第一个机甲的ID
        self.user_sign = ""      # 个性签名

        self.account_id = None  # 账户ID
        self.platform = None   # 平台
        self.sid = None    # 服务器id
        self.state = 1  # 角色状态 0 冻结, 1 正常
        self.type = 0  # 角色类型 0 普通玩家, 1 内部账号 维护更新时，内部账户可随意进出游戏

        self.create_time = 0  # 角色创建时间
        self.last_request = 0  # 客户端和服务器最后交互时间
        self.last_sign_time = 0   # 上次登录签名时间，用于验证多端登录
        self.total_login_days = 0  # 累计登录天数
        self.login_history_dates = []  # 登录历史日期
        self.used_cdkey_tags = []    # 玩家已经使用过的物品兑换码

        self._game_info = None  # 角色游戏属性
        self._ext_info = None  # 角色附加属性
        self._vip = None  # 角色vip属性
        self._daily_info = None # 每日数据
        self._task = None    # 任务数据
        self._package = None  # 角色包裹
        self._hero = None  # 卡牌信息
        self._equip = None  # 装备信息
        self._skill = None  # 技能信息
        self._spirit = None  # 战魂信息
        self._array = None # 阵列信息
        self._mission = None  # 副本任务
        self._talent = None  # 天赋信息
        self._warship = None  # 战舰信息
        self._mall = None     # 商店数据
        self._group = None    # 帮派数据
        self._arena = None    # 竞技场数据
        self._trial = None    # 试炼数据
        self._sign = None    # 签到数据
        self._activity = None     # 运维活动数据

    @property
    def game_info(self):
        """角色游戏属性
        """
        if not self._game_info:
            from apps.models.game_info import GameInfo

            self._game_info = GameInfo.get(self.uid)

            if not self._game_info:
                self._game_info = GameInfo.install(self.uid)

        return self._game_info

    @property
    def ext_info(self):
        """角色附带属性
        """
        if not self._ext_info:
            from apps.models.ext_info import ExtInfo

            self._ext_info = ExtInfo.get(self.uid)

            if not self._ext_info:
                self._ext_info = ExtInfo.install(self.uid)

        return self._ext_info

    @property
    def daily_info(self):
        """每日数据
        """
        if not self._daily_info:
            from apps.models.daily_info import DailyInfo

            self._daily_info = DailyInfo.get(self.uid)

            # 如不存在则初始化，如已经到了第二天五点则重置
            if not self._daily_info or common_helper.time_to_refresh(self._daily_info.date, 5):
                self._daily_info = DailyInfo.install(self.uid)

        return self._daily_info

    @property
    def task(self):
        """任务数据
        """
        if not self._task:
            from apps.models.task import Task

            self._task = Task.get(self.uid)
            if not self._task:
                self._task = Task.install(self.uid)

        return self._task

    @property
    def package(self):
        """角色包裹
        """
        if not self._package:
            from apps.models.package import Package

            self._package = Package.get(self.uid)
            if not self._package:
                self._package = Package.install(self.uid)

        return self._package

    @property
    def hero(self):
        """姬甲信息
        """
        if not self._hero:
            from apps.models.hero import Hero

            self._hero = Hero.get(self.uid)

            if not self._hero:
                self._hero = Hero.install(self.uid)

        return self._hero

    @property
    def equip(self):
        """装备信息
        """
        if not self._equip:
            from apps.models.equip import Equip

            self._equip = Equip.get(self.uid)

            if not self._equip:
                self._equip = Equip.install(self.uid)

        return self._equip

    @property
    def skill(self):
        """技能信息
        """
        if not self._skill:
            from apps.models.skill import Skill

            self._skill = Skill.get(self.uid)

            if not self._skill:
                self._skill = Skill.install(self.uid)

        return self._skill

    @property
    def spirit(self):
        """战魂信息
        """
        if not self._spirit:
            from apps.models.spirit import Spirit

            self._spirit = Spirit.get(self.uid)

            if not self._spirit:
                self._spirit = Spirit.install(self.uid)

        return self._spirit

    @property
    def array(self):
        """阵列信息
        """
        if not self._array:
            from apps.models.array import Array

            self._array = Array.get(self.uid)

            if not self._array:
                self._array = Array.install(self.uid)

        return self._array

    @property
    def mission(self):
        """副本信息
        """
        if not self._mission:
            from apps.models.mission import Mission

            self._mission = Mission.get(self.uid)
            if not self._mission:
                self._mission = Mission.install(self.uid)

        return self._mission

    @property
    def talent(self):
        """天赋信息
        """
        if not self._talent:
            from apps.models.talent import Talent

            self._talent = Talent.get(self.uid)
            if not self._talent:
                self._talent = Talent.install(self.uid)

        return self._talent

    @property
    def warship(self):
        """战舰信息
        """
        if not self._warship:
            from apps.models.warship import Warship

            self._warship = Warship.get(self.uid)
            if not self._warship:
                self._warship = Warship.install(self.uid)

        return self._warship

    @property
    def mall(self):
        """商店信息
        """
        if not self._mall:
            from apps.models.mall import Mall

            self._mall = Mall.get(self.uid)
            if not self._mall:
                self._mall = Mall.install(self.uid)

        return self._mall

    @property
    def group(self):
        """帮派信息
        """
        if not self._group:
            from apps.models.group import Group

            self._group = Group.get(self.uid)
            if not self._group:
                self._group = Group.install(self.uid)

        return self._group

    @property
    def arena(self):
        """竞技场信息
        """
        if not self._arena:
            from apps.models.arena import Arena

            self._arena = Arena.get(self.uid)
            if not self._arena:
                self._arena = Arena.install(self.sid, self.uid)

            # 如已经到了第二天则重置
            if common_helper.time_to_refresh(self._arena.daily_update, 0):
                self._arena.daily_reset()

        return self._arena

    @property
    def trial(self):
        """终级试炼信息
        """
        if not self._trial:
            from apps.models.trial import Trial

            self._trial = Trial.get(self.uid)
            if not self._trial:
                self._trial = Trial.install(self.uid)

            # 如已经到了第二天五点则重置
            if common_helper.time_to_refresh(self._trial.daily_update, 5):
                self._trial.daily_reset()

        return self._trial

    @property
    def sign(self):
        """签到信息
        """
        if not self._sign:
            from apps.models.sign import Sign

            self._sign = Sign.get(self.uid)
            if not self._sign:
                self._sign = Sign.install(self.uid)

        return self._sign

    @property
    def vip(self):
        """vip信息
        """
        if not self._vip:
            from apps.models.vip import Vip

            self._vip = Vip.get(self.uid)
            if not self._vip:
                self._vip = Vip.install(self.uid)

        return self._vip

    @property
    def activity(self):
        """运维活动信息
        """
        if not self._activity:
            from apps.models.activity import Activity

            self._activity = Activity.get(self.uid)
            if not self._activity:
                self._activity = Activity.install(self.uid)

        return self._activity

    @classmethod
    def install(cls, user_login_data):
        """检测安装角色

        Args:
            user_login_data 角色基本登录信息

        """
        loop = 0
        # 多次取数据是防止网络闪烁等原因造成取数据失败，所以失败之后重新取数据，尝试取3次
        # 如果都失败，则被视为新号，初始化账号数据
        while True:
            ki_user = cls.get(user_login_data['uid'])
            if isinstance(ki_user, cls):
                break
            else:
                loop += 1
                if loop > 2:
                    break

        if not isinstance(ki_user, cls):
            ki_user = cls._install_new_user(user_login_data)
            # 新创角色默认获得配置,默认获得姬甲，排布阵容等
            if isinstance(ki_user, cls):
                ki_user.install_default_datas()

            try:
                stat_service.regist(ki_user.sid, ki_user.uid)
            except:
                pass
        else:
            ki_user.update_user_request_info()

        return ki_user

    @classmethod
    def debug_install(cls, uid):
        """检测安装角色

        Args:
            user_login_data 角色基本登录信息

        """
        loop = 0
        # 多次取数据是防止网络闪烁等原因造成取数据失败，所以失败之后重新取数据，尝试取3次
        # 如果都失败，则被视为新号，初始化账号数据
        while True:
            ki_user = cls.get(uid)
            if isinstance(ki_user, cls):
                break
            else:
                loop += 1
                if loop > 2:
                    break

        if not isinstance(ki_user, cls):
            return {}

        return ki_user

    def update_user_login_info(self, server_time):
        """
        每次登录时更新玩家某些必要信息
        并更新last_sign_time作为防双开标记

        Args:
            server_time  当前服务器时间，即当前登录时间
        """
        self.last_sign_time = server_time
        self.put()

    def update_user_request_info(self):
        """
        每次请求时更新玩家某些必要信息
        """
        now_time = int(time.time())

        old_last_request = self.last_request
        self.last_request = now_time     # 更新最近请求时间
        this_day = datetime.datetime.fromtimestamp(now_time)
        last_request_date = datetime.datetime.fromtimestamp(old_last_request)

        if last_request_date.date() != this_day.date():
            self.total_login_days += 1 # 更新登录总天数
            self.login_history_dates.append(time.strftime('%Y%m%d'))
            act_helper.update_after_login(self) # 更新上线登录活动，怕玩家一直不下线重新登录所做！！
            # 每日元宝返还活动【只限ios越狱正式1服&&android公测2服】
            pregift_service.payback_diamonds(self.sid, self.platform, self.account_id, self.uid, self.total_login_days)
            stat_service.dau(self) # dau统计

        # 更新在线统计的sorted list
        stat_service.online(self.sid, self.uid)

        self.put()

    @classmethod
    def _install_new_user(cls, user_login_data):
        """安装新角色，初始化角色及游戏数据

        Args:
            user_login_data: 角色基本信息
        """
        from apps.models.game_info import GameInfo
        from apps.models.vip import Vip
        from apps.models.daily_info import DailyInfo
        from apps.models.task import Task
        from apps.models.package import Package
        from apps.models.hero import Hero
        from apps.models.equip import Equip
        from apps.models.skill import Skill
        from apps.models.spirit import Spirit
        from apps.models.array import Array
        from apps.models.mission import Mission

        # from apps.models.talent import Talent
        # from apps.models.warship import Warship
        # from apps.models.mall import Mall
        # from apps.models.group import Group
        from apps.models.arena import Arena
        # from apps.models.trial import Trial
        # from apps.models.sign import Sign
        # from apps.models.activity import Activity

        now = int(time.time())
        uid = user_login_data["uid"]

        ki_user = cls(uid)
        ki_user.name = cls.default_name_generater(uid)
        ki_user.account_id = user_login_data["aid"]
        ki_user.platform = user_login_data["pf"]
        ki_user.sid = user_login_data["sid"]
        ki_user.state = 1
        ki_user.create_time = now
        ki_user.last_request = 0
        ki_user.total_login_days = 0

        ki_user.put()

        GameInfo.install(uid)
        Vip.install(uid)
        DailyInfo.install(uid)
        Task.install(uid)
        Package.install(uid)
        Hero.install(uid)
        Equip.install(uid)
        Skill.install(uid)
        Spirit.install(uid)
        Array.install(uid)
        Mission.install(uid)

        # 注释掉的内容未后期开放，
        # 为了节约内存，玩家角色等级达到之后再行创建

        # Talent.install(uid)
        # Warship.install(uid)
        # Mall.install(uid)
        # Group.install(uid)
        Arena.install(uid)
        # Trial.install(uid)
        # Sign.install(uid)
        # Activity.install(uid)

        return ki_user

    def install_default_datas(self):
        """默认获得姬甲，排布阵容等
        """
        from apps.logics import hero as hero_logic
        hero_logic.add_heros(self, [{100050: 1}])
        self.array.update(1, [0, 100050, 0, 0, 0, 0])
        self.arena.init_when_install(self.sid)

        # 创建角色时，检测是否需要发[ 应用宝的预约礼包 | uc封测测试奖励 | 360封测测试奖励 ]
        if self.platform in ["YSDK", "UC", "QIHOO"]:
            account = Account.get_account("%s_%s" % (self.platform, self.account_id))
            if not isinstance(account, Account):
                return

            if self.platform == "YSDK" and redis_client.sismember(rediskey_config.YYB_ORDERED_SET % self.sid, account.open_id):
                order_awards_cfg = game_config.gift_key_config.get("YY02", {})
                if order_awards_cfg:
                    MailService.send_game(self.uid, 5003, [], order_awards_cfg["award"])

            if self.platform in ["UC", "QIHOO"]:
                # 1.最终等级达到x级 2.累计登陆x天 3.竞技场最终排名x
                awards,logins = pregift_service.uc_qihoo_test_award_4003(self.sid, self.platform, account.open_id)
                if awards:
                    MailService.send_game(self.uid, 5000, [logins], awards)

                awards1,days = pregift_service.uc_qihoo_test_award_4004(self.sid, self.platform, account.open_id)
                if awards1:
                    MailService.send_game(self.uid, 5001, [days], awards1)

                awards2,rank = pregift_service.uc_qihoo_test_award_4005(self.sid, self.platform, account.open_id)
                if awards2:
                    MailService.send_game(self.uid, 5002, [rank], awards2)

    def get_user_group_info(self):
        """获取公会所需的玩家数据
        """
        user_info = {}
        user_info['uid'] = self.uid
        user_info['name'] = self.name
        user_info['avatar'] = self.avatar
        user_info['login'] = self.last_request
        user_info['fight'] = self.game_info.fight
        user_info['level'] = self.game_info.role_level

        return user_info

    def get_user_game_info(self):
        """获取角色信息
        """
        user_info = {}
        user_info['uid'] = self.uid
        user_info['name'] = self.name
        user_info['avatar'] = self.avatar
        user_info['sign'] = self.user_sign
        user_info['role_exp'] = self.game_info.role_exp
        user_info['role_level'] = self.game_info.role_level
        user_info['diamond'] = self.game_info.diamond
        user_info['gold'] = self.game_info.gold
        user_info['energy'] = self.game_info.energy
        user_info['energy_last_update'] = self.game_info.energy_update

        user_info['vip_level'] = self.game_info.vip_level
        user_info['vip_exp'] = self.game_info.vip_exp

        user_info['skill_point'] = self.game_info.skill_point
        user_info['skill_point_recover_interval'] = self.game_info.skill_point_recover_interval
        user_info['skill_point_update_time'] = self.game_info.skill_point_update_time

        user_info['honor_point'] = self.game_info.honor_point
        user_info['trial_point'] = self.game_info.trial_point
        user_info['talent_point'] = self.game_info.talent_point
        user_info['group_point'] = self.game_info.group_point
        user_info['weak_point'] = self.game_info.weak_point
        user_info['box_key'] = self.game_info.box_key
        user_info['clone_point'] = self.game_info.clone_point

        user_info['last_guide_id'] = self.game_info.last_guide_id

        return user_info

    def update_name(self, name=None):
        """修改玩家名
        """
        self.update_name_times += 1
        self.name = name
        self.put()

    def update_avatar(self, avatar=None):
        """修改玩家头像
        """
        self.avatar = avatar
        self.put()

    def update_sign(self, sign=None):
        """修改玩家签名
        """
        self.user_sign = sign
        self.put()

    @staticmethod
    def default_name_generater(uid):
        """
        """
        seq = int(uid[-6:])

        times = seq / 65000
        index = seq % 65000

        if times == 0:
            default_name = game_config.user_default_name_cfg.get(index)
        else:
            default_name = game_config.user_default_name_cfg.get(index) + str(times)

        name_service.add_registered_name(default_name, uid)

        return default_name
