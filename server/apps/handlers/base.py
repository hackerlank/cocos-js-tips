#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-30 17:32:06
# @Author : Jiank (http://jiankg.github.com)
# @doc
#
# @end
# @copyright (C) 2015, kimech

from torngas.handler import WebHandler
from apps.configs.msg_code import MsgCode

from torngas.logger import SysLogger

class BaseHandler(WebHandler):
    """do some your base things
    """

    def interal_error_handle(self, error):
        """内部错误处理接口
        """
        # TODO 记录日志
        error_msg_code = {"mc": MsgCode['ServerInternalError']}
        self.write(error_msg_code)
