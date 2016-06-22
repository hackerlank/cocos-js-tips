#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 11:10:29
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     请求预检查处理和请求结束后检查处理
# @end
# @copyright (C) 2015, kimech

import time

def pre(context):
    """
    """
    pass

def post(context):
    """请求结束后的收尾处理
    """
    # 正常结束的游戏业务请求都在这里统一加上“正常”的消息状态码100
    # 其作用是为了在之后的任务检测中，只有正常状态的业务请求才会检测任务更新情况
    if 'mc' not in context.result:
        context.result['mc'] = 100
