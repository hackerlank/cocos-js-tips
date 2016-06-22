#-*- coding: utf8 -*-
import time
import logging
import datetime

from apps.common.middlewares import middleware_exception

class TimeviewMiddleware(object):
    @middleware_exception
    def process_request(self, handler, clear):
        self.start_time = time.time()

    @middleware_exception
    def process_response(self, handler, clear, chunk):
        end_time = time.time()
        path_name = handler.request.uri.strip('/').replace('/', '.')
        exec_time = end_time - self.start_time
        if exec_time != 0:
            method = handler.request.request_context.get_parameter('method')
            if method is None:
                logging.error('%s timeit view: %s: %.3f' % (str(datetime.datetime.now()), path_name, exec_time))
            else:
                logging.error('%s timeit view: %s.%s: %.3f' % (str(datetime.datetime.now()), path_name, method, exec_time))
