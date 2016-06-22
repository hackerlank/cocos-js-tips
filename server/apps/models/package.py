#!/usr/bin/env python
# encoding: utf-8
"""
package.py

"""
from apps.configs import game_config
from libs.rklib.model import BaseModel

class Package(BaseModel):
    """角色包裹信息

    示例：
    items = {100001: 1,}

    Attributes:
        uid     # 角色ID :str
        items   # 包裹信息 :dict
    """
    def __init__(self, uid=None):
        """
        初始化角色包裹信息

        Args:
            uid: 平台角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.items = {}  # 包裹信息

    @classmethod
    def install(cls, uid):
        """为新角色初始安装包裹信息

        Args:
            uid: 角色ID

        Returns:
            package: 角色包裹信息对象实例
        """
        package = cls(uid)

        # DEBUG 模式
        # items = {}
        # for i in game_config.item_cfg:
        #     items.update({i:1000})

        # package.items = items

        package.put()

        return cls.get(uid)

    def get_all_info(self):
        """所有道具信息

        Args:

        Returns:
            data: 所有道具信息
        """
        package_data = {}
        package_data["items"] = self.items

        return package_data

    def get_item_num_by_id(self, item_id):
        """根据道具id获得物品数量

        Args:
            item_id  道具id
        Returns:
            item_info 道具信息
        """
        return self.items.get(item_id, 0)

    def add(self, item_id, num, instant_save=False):
        """新增道具物品

        Args:
            item_id: 道具模板Id
            num: 获得数量
            instant_save: 即时存储
        """
        if item_id not in self.items:
            self.items[item_id] = num
        else:
            self.items[item_id] += num

        cfg = game_config.item_cfg.get(item_id)
        if cfg:
            self.items[item_id] = min(cfg["stack_limit"], self.items[item_id])

        if instant_save:
            self.put()

    def remove(self, item_id, num, instant_save=False):
        """使用物品

        Args:
            item_id: 道具模板Id
            num: 消耗数量
            instant_save: 即时存储
        """
        if item_id in self.items:
            self.items[item_id] -= min(num, self.items[item_id])

            if self.items[item_id] == 0:
                del self.items[item_id]

        if instant_save:
            self.put()

    def _reset(self):
        """重置
        """
        self.items = {}

        self.put()
