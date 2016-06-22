#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging

from datetime import datetime

access_log = logging.getLogger('torngas.accesslog')

class AccessLogMiddleware(object):
    def process_init(self, application):
        application.settings['log_function'] = lambda _: None

    def process_endcall(self, handler, clear):
        request_time = 1000.0 * handler.request.request_time()
        remote_ip = handler.request.remote_ip
        if "X-Real-Ip" in handler.request.headers:
            remote_ip = handler.request.headers.get("X-Real-Ip")

        uri = handler.request.uri
        method = handler.request.method
        status = handler.get_status()
        content_length = handler._headers.get("Content-Length", "-")
        api_method = handler.get_argument("method", "")

        request_params = {}
        arguments = handler.request.arguments
        for arg in arguments if api_method not in ["arena.fight", ""] else []:
            if arg != "method":
                request_params[arg] = arguments[arg][0]

        try:
            uid = handler.request.request_context.user.uid
        except:
            uid = ""

        api = uri.replace("/", ".")[1:] if uri != "/game/api" else api_method
        _message = '[%s] ip:%s%sapi:%s args:%s len:%s utime:%.2fms' % (
            time.strftime("%Y%m%d %H:%M:%S"),
            remote_ip,
            (" id:%s " % uid) if uid else " ",
            api,
            request_params,
            content_length,
            request_time
        )

        if status != 200:
            _message += " status: %s" % status

        access_log.info(_message)
