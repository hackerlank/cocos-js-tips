#-*- coding: utf-8 -*-
import sys, traceback
import cPickle as pickle
from threading import local

from ..core import app as app_config
enable_storage_context = app_config.enabled_storage_context()

class SerializerMetaClass(type):
    def __init__(self, name, bases, attrs):
        super(SerializerMetaClass, self).__init__(name, bases, attrs)
        app_config.init_model(self)                    # 用config.conf中的配置信息设置类属性
        # if hasattr(self, "seq_attrs") or hasattr(self, "adv_seq_attrs"):
        #     print >> sys.stderr, 'Warning: "seq_attrs" and "adv_seq_attrs were deprecated, please use "def_attrs".', self
        self._get_def_attrs(bases)

    def _get_def_attrs(self, bases):
        if hasattr(self, "def_attrs"):
            def_attrs = dict(getattr(self, "def_attrs"))
            for attr, v in def_attrs.items():
                if v<>"adv" and v<>"simple":
                    if not hasattr(self, v+"_loads") or not hasattr(self, v+"_dumps"):
                        raise ValueError("Invalid field define. Model:%s field:%s value:%s" % (self.__name__, attr, v))
        else:
            def_attrs = {}
        if not def_attrs:   # def_attrs is empty dict
            seq_attrs = getattr(self, "seq_attrs", [])
            adv_seq_attrs = getattr(self, "adv_seq_attrs", [])
            for attr in seq_attrs:
                if attr in adv_seq_attrs and not def_attrs.has_key(attr):
                    def_attrs[attr] = "adv"
                else:
                    def_attrs[attr] = "simple"
        for base in bases:
            if hasattr(base, "all_def_attrs"):
                base_def_attrs = getattr(base, "all_def_attrs")
                for k, v in base_def_attrs.items():
                    if not def_attrs.has_key(k):
                        def_attrs[k] = v

        setattr(self, "all_def_attrs", def_attrs)

class Serializer(object):
    __metaclass__ = SerializerMetaClass

    def __init__(self):
        super(Serializer, self).__init__()

    @classmethod
    def loads(cls, data):
        """
        将一个dict转换成model对象实例
            data: dict对象
        """
        def_attrs = cls.all_def_attrs
        o = cls()
        for attr in def_attrs:
            if attr in data:
                if def_attrs[attr] == "simple":
                    setattr(o, attr, data[attr])
                elif def_attrs[attr] == "adv":
                    if data[attr]:
                        setattr(o, attr, pickle.loads(str(data[attr])))
                    else:
                        print attr
                        setattr(o, attr, None)
                else:
                    loads_func = getattr(o, def_attrs[attr]+"_loads")
                    setattr(o, attr, loads_func(data[attr]))
        return o

    def dumps(self, attrs = None, shallow = False):
        def_attrs = self.all_def_attrs
        if attrs is not None:
            seq_attrs = attrs
        else:
            seq_attrs = def_attrs.keys()

        data = {}
        for attr in seq_attrs:
            val = getattr(self, attr)
            if def_attrs[attr] == "simple":
                if app_config.debug:
                    vtype = type(val)
                    if vtype==dict or vtype==list or vtype==tuple:
                        raise RuntimeError("dumps error! Model:%s Field:%s" % (self.__class__.__name__, attr))
                data[attr] = val
            elif def_attrs[attr] == "adv":
                data[attr] = val if shallow else pickle.dumps(val, pickle.HIGHEST_PROTOCOL)
            else:
                dumps_func = getattr(self, def_attrs[attr]+"_dumps")
                data[attr] = dumps_func(val)
        return data

class StorageContext(local):
    def __init__(self):
        self._keys = set()
        self._storage = {}

    def clear(self):
        """
        清除所有缓存的数据，未保存的数据会丢失
        """
        if enable_storage_context:
            self._keys.clear()
            self._storage.clear()

        app_config.reset_storage_engines()  # 重置存储相关状态（比如关闭数据库链接，关闭memcached链接）

    def put(self, key, obj, need_save=True):
        """
        缓存对象实例
            key:  缓存用的key
            obj:  需要缓存的对象实例
            need_save: 是否需要真实保存。
                True: 调用save()方法时会进行将数据存储到持久层
                False:  只是缓存数据
        """
        if enable_storage_context:
            self._storage[key] = obj
            if need_save:
                self._keys.add(key)

    def get(self, key):
        if enable_storage_context:
            return self._storage.get(key, None)

    def save(self):
        if enable_storage_context:
            for key in self._keys:
                obj = self._storage.get(key)
                if obj is not None:
                    obj.do_put()
            self.clear()

        app_config.reset_storage_engines()  # 重置存储相关状态（比如关闭数据库链接，关闭memcached链接）

    def delete(self, key):
        try:
            del self._storage[key]
        except:
            pass
        try:
            self._keys.remove(key)
        except:
            pass

storage_context = StorageContext()

class BaseModel(Serializer):
    def __init__(self):
        super(BaseModel, self).__init__()
        self.need_insert = True

    @classmethod
    def generate_cache_key(cls, pkey):
        return cls.cache_prefix + "|" + cls.__name__ + '|' + str(pkey)

    def get_cache_key(self):
        pkey = str(self.get_pkey())
        return self.__class__.generate_cache_key(pkey)

    def get_pkey(self):
        return getattr(self, self.pkey_field)

    @classmethod
    def get(cls, pkey):
        cache_key = cls.generate_cache_key(pkey)

        if enable_storage_context:
            obj = storage_context.get(cache_key)
            if obj is not None:
                return obj

        obj = cls.do_get(cache_key, pkey)
        if enable_storage_context:
            if  obj is not None:
                storage_context.put(cache_key, obj, False)

        return obj

    @classmethod
    def do_get(cls, cache_key, pkey):
        data = None
        level = 0
        # 从存储层获取dumps后的对象数据
        for engine_name in cls.engines:
            engine_obj = app_config.get_engine(engine_name)

            level += 1
            if not engine_obj.support_get:
                continue

            data = engine_obj.get_data(cls, pkey)
            if data is not None:
                break
        if data is None:
            return None
        # 获取到dumps数据，转换成为对象实例
        obj = cls.loads(data)
        # 数据版本升级
        if hasattr(obj, 'data_version'):
            v = obj.data_version if isinstance(obj.data_version, basestring) else '0'

            v = str(int(v) + 1)
            upgrade_method = 'upgrade_data_version_to_v' + v

            while hasattr(cls, upgrade_method):
                call_method = 'cls.' + upgrade_method + '(obj)'
                exec(call_method)
                obj.data_version = v

                v = str(int(v) + 1)
                upgrade_method = 'upgrade_data_version_to_v' + v

        obj.need_insert = False
        if level > 1 and cls.top_cache:  # 读出来的数据缓存到最上层
            top_engine_obj = app_config.get_engine(cls.engines[0])
            top_engine_obj.put_data(cls, pkey, data, False)

        return obj

    def put(self):
        if enable_storage_context:
            if self.need_insert:
                storage_context.save()
                self.do_put()
            else:
                storage_context.put(self.get_cache_key(), self, True)
        else:
            self.do_put()

    def do_put(self):
        cls = self.__class__
        if cls.bottom_async and not self.need_insert:    # 异步写模式下，最后一层不写 (新对象除外)
            es = cls.engines[:-1]
        else:                                            # 非异步写或者新对象，每层都要写
            es = cls.engines

        data = self.dumps()
        pkey = self.get_pkey()
        for engine_name in es:
            engine_obj = app_config.get_engine(engine_name)
            if engine_obj.support_get:
                engine_obj.put_data(cls, pkey, data, self.need_insert)
            else:   #  这层存储不需要支持get，不用真的写value
                engine_obj.put_data(cls, pkey, "1", self.need_insert)
        self.need_insert = False

    def put_only_bottom(self):
        """直接写到存储的最底一层
        """
        cls = self.__class__
        engine_name = self.__class__.engines[-1]
        data = self.dumps()
        pkey = self.get_pkey()
        engine_obj = app_config.get_engine(engine_name)
        engine_obj.put_data(cls, pkey, data, self.need_insert)

    def delete(self):
        if enable_storage_context:
            storage_context.delete(self.get_cache_key())
        self.do_delete()

    def do_delete(self):
        cls = self.__class__
        es = cls.engines
        pkey = self.get_pkey()
        for engine_name in es:
            engine_obj = app_config.get_engine(engine_name)
            engine_obj.delete_data(cls, pkey)
