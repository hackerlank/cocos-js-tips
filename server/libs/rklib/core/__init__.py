#-*- coding: utf-8 -*-
import sys

from ..utils.importlib import import_by_name

class Application(object):
    def __init__(self):
        super(Application, self).__init__()
        self.storage_config = Config()
        self.model_config = Config()
        self.logic_config = Config()
        self.plat = ""
        self.debug = False

    def init(self, **kwargs):
        # 指定应用的平台  根据平台来加载存储配置
        if kwargs.has_key('plat'):
            self.plat = kwargs['plat']

        #加载存储层配置
        if kwargs.has_key('storage_cfg_file'):
            self.storage_config.configure(kwargs['storage_cfg_file'])
            self._init_storage_engine_config()
        #加载model层配置
        if kwargs.has_key('model_cfg_file'):
            self.model_config.configure(kwargs['model_cfg_file'])
            self._init_model_default_config()
        #加载逻辑层配置
        if kwargs.has_key('logic_cfg_file'):
            self.logic_config.configure(kwargs['logic_cfg_file'])

    def get_engine(self, engine_name):
        """根据engine_name获取storage engine实例"""
        return self.storage_engines.get(engine_name)

    get_storage_engine = get_engine

    def reset_storage_engines(self):
        """重置存储相关状态（比如关闭数据库链接，关闭memcached链接）"""
        for engine_name, storage_engine in self.storage_engines.iteritems():
            storage_engine.reset()

    def enabled_storage_context(self):
        """是否启用storage_context"""
        return getattr(self.storage_config, "enable_storage_context", False)

    def init_model(self, model_cls):
        m_name = model_cls.__name__
        if m_name == "Serializer" or m_name == "BaseModel":
            return
        if self.model_default:
            for attr in self.model_default:
                setattr(model_cls, attr, self.model_default[attr])
        if self.model_config.models.has_key(m_name):
            for attr in self.model_config.models[m_name]:
                setattr(model_cls, attr, self.model_config.models[m_name][attr])

    def _init_storage_engine_config(self):
        self.storage_engines = {}
        if not hasattr(self.storage_config, "storage_engines"):
            sys.exit("Can't find 'storage_engines' in config file.")

        pconfigs = self.storage_config.storage_engines[self.plat]
        for se in pconfigs:
            se_cls = pconfigs[se]["class"]
            cls = import_by_name(se_cls)
            engine_obj = cls()
            engine_obj.configure(pconfigs[se]["config"])
            self.storage_engines[se] = engine_obj

    def _init_model_default_config(self):
        if hasattr(self.model_config, "model_default"):
            self.model_default = getattr(self.model_config, "model_default")

    def replace_class(self, old_cls_name, new_cls_name):
        tmp = old_cls_name.split(".")
        old_module_name = ".".join(tmp[0:-1])
        old_cls_name = tmp[-1]
        tmp = new_cls_name.split(".")
        new_module_name = ".".join(tmp[0:-1])
        new_cls_name = tmp[-1]
        old_module = __import__(old_module_name, globals(), locals(), [old_cls_name])
        new_module = __import__(new_module_name, globals(), locals(), [new_cls_name])
        new_cls = getattr(new_module, new_cls_name)
        setattr(old_module, old_cls_name, new_cls)

class Config(object):
    def __init__(self):
        super(Config, self).__init__()

    def configure(self, cfg_file):
        cf = open(cfg_file)
        try:
            gs = {}
            exec(cf.read(), gs)
            for k in gs:
                if k <> "__builtins__":
                    setattr(self, k, gs[k])
        finally:
            cf.close()

app = Application()
