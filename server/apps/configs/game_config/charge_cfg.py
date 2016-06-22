#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date :
# @Author : Jiank
# @doc
#     !!! 前方配置高能, 均为自动生成, 随意改动可能会有不可思议的事情发生 !!!
# @end
# @copyright (C) 2015, kimech

charge_cfg = {

    1:{
        "dimaond": 60,
        "rmb": 6,
        "first_extra": 60,
    },

    2:{
        "dimaond": 300,
        "rmb": 30,
        "first_extra": 300,
    },

    3:{
        "dimaond": 980,
        "rmb": 98,
        "first_extra": 980,
    },

    4:{
        "dimaond": 1980,
        "rmb": 198,
        "first_extra": 1980,
    },

    5:{
        "dimaond": 3280,
        "rmb": 328,
        "first_extra": 3280,
    },

    6:{
        "dimaond": 6480,
        "rmb": 648,
        "first_extra": 6480,
    },

}

money_index_mapping = {}
for index,cfg in charge_cfg.items():
    money_index_mapping[cfg["rmb"]] = index

