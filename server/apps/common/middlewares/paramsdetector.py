#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-22 21:37:49
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     请求参数探测检查
# @end
# @copyright (C) 2015, kimech

import ujson

from torngas.settings_manager import settings
from apps.configs.msg_code import MsgCode
from apps.configs import game_proto

class ParamsDetectorMiddleware(object):
    def process_request(self, handler, clear):
        """匹配路由后，执行处理handler时调用,**支持异步**

        检测客户端请求参数非空，格式等初级检测，如果异常，直接打回这个请求

        :param handler: handler对象

        """
        request_path = handler.request.uri

        if request_path.startswith("/A6ksi"):
            return

        if request_path.startswith("/debug"):
            return

        if request_path.startswith("/notification/"):
            return

        context = handler.request.request_context
        api_method = context.get_parameter("method", "")
        if api_method:
            # 游戏业务API, proto key 为 m__api__...
            keys = request_path.split("/")[2:] + api_method.split(".")
        else:
            keys = request_path.split("/") + api_method.split(".")

        keys = filter(None, keys)
        proto_key = "m__%s__c2s" % reduce(lambda x,y: "%s__%s" % (x,y), keys)

        params_format = game_proto.GameProto.get(proto_key, {})
        if not params_format:
            handler.finish(ujson.dumps({"mc": MsgCode['UriNotExist']}))

        req_results = []
        for key, value in params_format.iteritems():
            result = _check_request_param(key, value, context)
            req_results.append(result)

        # 请求参数字段不合格的，直接打回去
        if False in req_results:
            handler.finish(ujson.dumps({"mc": MsgCode['ParamError']}))
            return 1

def _check_request_param(key, required_type, context):
    """检查单个参数是否合法

    Args:
        key  str  参数标识
        required_type  dict  参数要求类型
        context

    Returns:
        bool 是否合法
    """
    if key == "msg_id" or required_type == "ignore":
        return True
    else:
        try:
            value = context.get_parameter(key)
            if value:
                if required_type == str:
                    context.set_parameter(key, required_type(value).strip())
                else:
                    context.set_parameter(key, required_type(value))

                return True
            else:
                return False
        except Exception,e:
            return False
