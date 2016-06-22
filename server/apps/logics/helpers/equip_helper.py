#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-18 16:54:43
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   装备工具模块
# @end
# @copyright (C) 2015, kimech

import random

def init_random_attrs(attrs_list):
    """初始化随机属性

    新获得一件装备时，按配置要求生成装备的随机属性项。

    Args:
        attrs_list: 随机属性库, eg: [[130001, 130002, 130003], [130001, 130002, 130003]]

    Returns:
        生成的随机属性列表, eg: [130001, 130002]

    Raises:
        KeyError
    """
    attr_list = []
    for attrs in attrs_list:
        attr_list.append(random_attr(attrs))

    return attr_list

def random_attr(attrs_lib):
    """根据随机属性库随机出一条属性

    Args:
        attrs_list list 属性库,eg:[130001, 130002, 130003]
    Returns:
        attr_id int 属性id
    """
    _random_weight, _random_dict = 0, {}

    for attr_id in attrs_lib:
        cfg = game_config.hero_rand_attr_cfg[int(attr_id)]
        _random_dict[attr_id] = cfg["weight"]
        _random_weight += cfg["weight"]

    _random_value = random.randint(1, _random_weight)
    tmp = tuple()

    while _random_value > 0:
        tmp = _random_dict.popitem()
        _random_value -= tmp[1]

    return tmp[0]
