#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cPickle as pickle

class ReadonlyDict:
    def __init__(self, d):
        self._raw = d
        self._dict = pickle.loads(pickle.dumps(d))    # make one copy of the config data

        for k,v in self._dict.items():
            if isinstance(v, dict):
                self._dict[k] = self.__class__(v)
            elif isinstance(v, list) or isinstance(v, tuple):
                l = list(v)
                for n,i in enumerate(l):
                    if isinstance(i, dict):
                        l[n] = self.__class__(i)
                self._dict[k] = tuple(l)

    def copy(self, key=None):
        if key is None:
            obj = self._raw
        elif key in self._raw:
            obj = self._raw[key]
        else:
            raise Exception("Error: the specified key `%s' doesn't exist!" % key)

        if isinstance(obj, str) or isinstance(obj, tuple):
            return obj
        else:
            return pickle.loads(pickle.dumps(obj))

    def __getitem__(self, key):
        return self._dict[key]

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def __setitem__(self, key, value):
        raise Exception("Error: setitem operation is denied!")

    def items(self):
        return self._dict.items()
