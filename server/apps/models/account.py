#!/usr/bin/env python
# encoding: utf-8
"""
account.py

Copyright (c) 2011 Rekoo Media. All rights reserved.
"""

import copy
import time
from apps.misc import utils

from libs.rklib.model import BaseModel
from apps.services.sequence import Sequence

class Account(BaseModel):
    """角色账号映射信息

    Attributes:
        id: 角色account_id str
        uids: 游戏角色ID字典 dict  eg: {1: 110000001, 2: 210000002}
        created_at: 创建时间戳
    """
    def __init__(self, id=None):
        """初始化角色账号映射信息

        Args:
            id: account_id
        """
        BaseModel.__init__(self)

        self.id = id
        self.password = ""
        self.type = 0
        self.uids = {}
        self.login_history = []
        self.created_at = int(time.time())
        self.open_id = "" # 平台原始id

    @classmethod
    def get_account(cls, account_id):
        """获取账户
        """
        account = cls.get_account_data(account_id)
        if not isinstance(account, cls):
            account = cls(account_id)
            account.put()

            return account
        else:
            return account

    @classmethod
    def register(cls, account_id, password, account_type=1):
        """注册用户
        """
        account = cls.get_account(account_id)

        account.password = utils.md5(password)
        account.type = account_type
        account.put()

    def update_open_id(self, open_id):
        """更新用户open_id目前只有应用宝用到
        """
        self.open_id = open_id
        self.put()

    @classmethod
    def check_account_exist(cls, account_id):
        """注册用户
        """
        account = cls.get_account_data(account_id)

        if not isinstance(account, cls):
            return False
        else:
            return True

    @classmethod
    def account_type(cls, account_id):
        account = cls.get_account_data(account_id)

        if not isinstance(account, cls):
            return None
        else:
            return account.type

    @classmethod
    def check_user_password(cls, account_id, password):
        """验证用户
        """
        account = cls.get_account_data(account_id)

        if not isinstance(account, cls):
            return False
        else:
            return account.password == utils.md5(password)

    @classmethod
    def get_user_id(cls, account_id, server_id):
        """为每一个角色生成对应的应用自身维护的角色ID

        Args:
            account_id, server_id

        Returns:
            uid: 应用自身维护的角色ID, sid + sequence
            eg: 1100000000
        """
        account = cls.get_account_data(account_id)
        if not isinstance(account, cls):
            account = cls(account_id)
            uid = Sequence.generate_user_id(server_id)
            account.uids[server_id] = uid
            account.login_history.append(server_id)
            account.put()

            # 账号并发保存校验
            _account = cls.get(account_id)
            if isinstance(_account, cls) and _account.uids[server_id] != uid:
                account.uids[server_id] = uid
                account.put()

            return uid
        else:
            uid = account.uids.get(server_id, None)
            if not uid:
                uid = Sequence.generate_user_id(server_id)
                account.uids[server_id] = uid

            # 更新登录历史
            login_history = copy.copy(account.login_history)
            if server_id not in login_history:
                login_history.append(server_id)
            else:
                login_history.remove(server_id)
                login_history.append(server_id)

            account.login_history = login_history[-5:]
            account.put()

            return uid

    @classmethod
    def get_login_history(cls, account_id):
        """获取登录历史

        Args:
            platform 平台标识
            account_id 账户

        Returns:
            login_history 登录历史服务器 list
        """
        account = cls.get(account_id)

        if not isinstance(account, cls):
            return []
        else:
            login_history = copy.copy(account.login_history)
            login_history.reverse()

            return login_history

    @classmethod
    def bind_account_auth_data(cls, tmp_account_id, account_id, password):
        """更新游客的登录验证信息
        """
        tmp_account = cls.get_account_data(tmp_account_id)

        if not isinstance(tmp_account, cls):
            return False
        else:
            try:
                account = cls.get_account(account_id)
                account.id = account_id
                account.password = utils.md5(password)
                account.type = 1
                account.uids = tmp_account.uids
                account.login_history = tmp_account.login_history
                account.created_at = tmp_account.created_at

                account.put()
                tmp_account.delete()

                return True
            except Exception, e:
                return False

    @classmethod
    def get_account_data(cls, account_id):
        """
        """
        loop = 0
        # 这个地方多次取数据是防止网络闪烁等原因造成取数据失败，所以失败之后重新取数据，尝试取3次
        # 如果都失败，则被视为新号，初始化账号数据
        while True:
            account = cls.get(account_id)
            if isinstance(account, cls):
                break
            else:
                loop += 1
                if loop > 2:
                    break

        return account
