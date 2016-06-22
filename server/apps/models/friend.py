#!/usr/bin/env python
# encoding: utf-8
"""
friend.py

"""
from libs.rklib.model import BaseModel

class Friend(BaseModel):
    """
    角色好友信息

    Attributes:
        uid        # 角色ID   :str
        friends    # 好友列表  :list
    """
    def __init__(self, uid=None):
        """
        Args:
            uid: 角色ID
        """
        BaseModel.__init__(self)

        self.uid = uid  # 角色ID
        self.friends = []  # 好友信息

    @classmethod
    def install(cls, uid):
        """
        Args:
            uid: 角色ID

        Returns:
            friend: 角色好友信息对象实例

        """
        friend = cls(uid)
        friend.put()

        return cls.get(uid)

    def _reset(self):
        """
            初始化friend
        """
        self.friends = []  # 好友信息
        self.put()
