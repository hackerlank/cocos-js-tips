#-*- coding: utf8 -*-

from libs.rklib.model import storage_context
from libs.rklib.web.logic import KiRequestContext

from apps.models.user import User

class KiContextMiddleware(object):
    def process_request(self, handler, clear):
        """
        匹配路由后，执行处理handler时调用,**支持异步**
        :param handler: handler对象

        """
        request_context = KiRequestContext(handler)
        handler.request.request_context = request_context

        storage_context.clear()

    def process_response(self, handler, clear, chunk):
        """
        请求结束后响应时调用，此方法在render之后，finish之前执行，可以对chunk做最后的封装和处理
        :param handler: handler对象
        :param chunk : 响应内容，chunk为携带响内容的list，你不可以直接对chunk赋值，
            可以通过chunk[index]来改写响应内容，或再次执行handler.write()
        """
        storage_context.save()
