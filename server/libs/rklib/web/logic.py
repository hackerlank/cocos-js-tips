#-*- coding: utf-8 -*-
import sys
import time
import logging

from apps.misc import utils

from ..core import app as app_config
from ..utils.importlib import import_by_name

class KiRequestContext(object):
    """客户端请求对象类

    Attributes:
            data : 客户端请求传递的参数
            user : 玩家对象
            result : 处理结果
    """
    def __init__(self, handler):
        super(KiRequestContext, self).__init__()
        self.user = None
        self.result = {}

        # self._handler = handler
        self._data = {}
        self._fetch_origin_datas(handler)

    @property
    def data(self):
        """用于存储handler链处理过程中的临时数据
        """
        return self._data

    @property
    def params(self):
        return self._data.keys()

    @property
    def cookies(self):
        if self._data.has_key("cookie_info"):
            return self._data["cookie_info"]
        else:
            return None

    @property
    def path(self):
        return self._handler.request.uri

    def _fetch_origin_datas(self, handler):
        arguments = handler.request.arguments
        for arg in arguments:
            self._data[arg] = arguments[arg][0]

    def set_parameter(self, name, value=None):
        self._data[name] = value

    def get_parameter(self, name, default=None):
        try:
            return self._data.get(name, default)
        except Exception, e:
            return None

class ResponseContext(object):
    def __init__(self):
        pass

    @property
    def raw_response(self):
        raise NotImplementedError

    def set_cookie(self, key, value, expires, **kwargs):
        """设置Cookies
        """
        raise NotImplementedError

    def reset_to(self, content="", **kwargs):
        """重置Response内容
        """
        raise NotImplementedError

class Gateway(object):
    def configure(self, cfg_value):
        self._cfg = cfg_value
        self._api_method_name = cfg_value.get("api_method_name", "method")
        self._logic_package = cfg_value.get("logic_package", "apps.logics")

        self._global_pre_handlers = []
        self._api_pre_handlers = {}
        self._handlers = {}
        self._api_post_handlers = {}
        self._global_post_handlers = []

        # import and cache handler function
        # self._prepare_api_handlers()
        self._prepare_global_handlers()

    def process(self, reuqest_ctx):
        api_method = reuqest_ctx.get_parameter(self._api_method_name)
        func = self._get_handler(api_method)

        # global pre handlers
        if self._global_pre_handlers:
            for pre_func in self._global_pre_handlers:
                pre_func(reuqest_ctx)

        # api special pre handlers
        pre_handlers = self._api_pre_handlers.get(api_method)
        if pre_handlers:
            for pre_func in pre_handlers:
                pre_func(reuqest_ctx)

        # api handler
        func(reuqest_ctx)

        # api special post handlers
        post_handlers = self._api_post_handlers.get(api_method)
        if post_handlers:
            for post_handler in post_handlers:
                post_handler(reuqest_ctx)

        # global post handlers
        if self._global_post_handlers:
            for post_func in self._global_post_handlers:
                post_func(reuqest_ctx)

        return reuqest_ctx.result

    def _prepare_api_handlers(self):
        def _import_handlers(handlers, handlers_cfg):
            for method in handlers_cfg:
                method_cfg = handlers_cfg[method]
                funcs = []
                for func_name in method_cfg:
                    try:
                        func = import_by_name(func_name)
                        funcs.append(func)
                    except:
                        print >> sys.stderr, "Import failed! [%s][%s]" % (method, func_name)
                        raise
                handlers[method] = funcs

        _import_handlers(self._api_pre_handlers, self._cfg.get("api_pre_handlers"))
        _import_handlers(self._api_post_handlers, self._cfg.get("api_post_handlers"))

    def _prepare_global_handlers(self):
        def _import_handlers(handlers, handlers_cfg):
            for func_name in handlers_cfg:
                try:
                    func = import_by_name(func_name)
                    handlers.append(func)
                except:
                    print >> sys.stderr, "Import failed! [%s]" % (func_name)
                    raise

        _import_handlers(self._global_pre_handlers, self._cfg.get("global_pre_handlers"))
        _import_handlers(self._global_post_handlers, self._cfg.get("global_post_handlers"))

    def _get_handler(self, api_method):
        func = self._handlers.get(api_method)
        if func is not None:
            return func

        func = import_by_name(self._logic_package + "." + api_method)
        self._handlers[api_method] = func
        try:
            func = import_by_name(self._logic_package + "." + api_method)
            self._handlers[api_method] = func
        except ImportError,e:
            raise e
            print >> sys.stderr, "Import failed! [%s]" % (self._logic_package + "." + api_method)
            raise ApiMethodNotExists(self._logic_package, api_method)
        except AttributeError:
            raise ApiMethodNotExists(self._logic_package, api_method)

        return func

class ApiMethodNotExists(Exception):
    def __init__(self, package, method):
        self.package = package
        self.method = method

    def __str__(self):
        return 'The API method %s.%s does not exist.' % (self.package, self.method)

gateway = Gateway()
gateway.configure(app_config.logic_config.handlers)
