#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date :
# @Author : Jiank
# @doc
#     !!! 前方配置高能, 均为自动生成, 随意改动可能会有不可思议的事情发生 !!!
# @end
# @copyright (C) 2015, kimech

activity_cfg = {

    1001:{
        "type": 303,
        "open_level": 1,
        "union": [1100],
    },

    1002:{
        "type": 400,
        "open_level": 1,
        "union": [1100],
    },

    1003:{
        "type": 400,
        "open_level": 1,
        "union": [1100],
    },

    1004:{
        "type": 326,
        "open_level": 1,
        "union": [1100],
    },

    1005:{
        "type": 306,
        "open_level": 1,
        "union": [1100],
    },

    1006:{
        "type": 327,
        "open_level": 1,
        "union": [1100],
    },

    1007:{
        "type": 325,
        "open_level": 1,
        "union": [1100],
    },

    1008:{
        "type": 324,
        "open_level": 1,
        "union": [1100],
    },

    1009:{
        "type": 202,
        "open_level": 1,
        "union": [1100],
    },

    1010:{
        "type": 321,
        "open_level": 1,
        "union": [1100],
    },

    1011:{
        "type": 401,
        "open_level": 1,
        "union": [1100],
    },

    1100:{
        "type": 328,
        "open_level": 1,
        "union": [],
    },

    2000:{
        "type": 200,
        "open_level": 1,
        "union": [],
    },

    2001:{
        "type": 300,
        "open_level": 1,
        "union": [],
    },

    2002:{
        "type": 100,
        "open_level": 1,
        "union": [],
    },

    2003:{
        "type": 303,
        "open_level": 1,
        "union": [],
    },

    2004:{
        "type": 310,
        "open_level": 1,
        "union": [],
    },

    2005:{
        "type": 335,
        "open_level": 1,
        "union": [],
    },

    2006:{
        "type": 335,
        "open_level": 1,
        "union": [],
    },

    3000:{
        "type": 329,
        "open_level": 1,
        "union": [],
    },

    3001:{
        "type": 701,
        "open_level": 1,
        "union": [],
    },

    3002:{
        "type": 900,
        "open_level": 1,
        "union": [],
    },

    3003:{
        "type": 901,
        "open_level": 1,
        "union": [],
    },

    3004:{
        "type": 309,
        "open_level": 1,
        "union": [],
    },

    3010:{
        "type": 702,
        "open_level": 1,
        "union": [],
    },

    3011:{
        "type": 311,
        "open_level": 1,
        "union": [],
    },

    3012:{
        "type": 322,
        "open_level": 1,
        "union": [],
    },

    3013:{
        "type": 323,
        "open_level": 1,
        "union": [],
    },

    3014:{
        "type": 334,
        "open_level": 1,
        "union": [],
    },

    3020:{
        "type": 334,
        "open_level": 1,
        "union": [],
    },

    4000:{
        "type": 302,
        "open_level": 1,
        "union": [],
    },

    4001:{
        "type": 322,
        "open_level": 1,
        "union": [],
    },

    4002:{
        "type": 323,
        "open_level": 1,
        "union": [],
    },

    4003:{
        "type": 903,
        "open_level": 1,
        "union": [],
    },

    4004:{
        "type": 902,
        "open_level": 1,
        "union": [],
    },

    4005:{
        "type": 903,
        "open_level": 1,
        "union": [],
    },

    4006:{
        "type": 330,
        "open_level": 1,
        "union": [],
    },

    4007:{
        "type": 331,
        "open_level": 1,
        "union": [],
    },

    4008:{
        "type": 332,
        "open_level": 1,
        "union": [],
    },

    4009:{
        "type": 333,
        "open_level": 1,
        "union": [],
    },

    5000:{
        "type": 100,
        "open_level": 1,
        "union": [],
    },

    5001:{
        "type": 310,
        "open_level": 1,
        "union": [],
    },

    5002:{
        "type": 322,
        "open_level": 1,
        "union": [],
    },

    5003:{
        "type": 323,
        "open_level": 1,
        "union": [],
    },

    8000:{
        "type": 501,
        "open_level": 1,
        "union": [],
    },

    9000:{
        "type": 600,
        "open_level": 1,
        "union": [],
    },

    9001:{
        "type": 902,
        "open_level": 1,
        "union": [],
    },

    9002:{
        "type": 902,
        "open_level": 1,
        "union": [],
    },

    9003:{
        "type": 902,
        "open_level": 1,
        "union": [],
    },

    9004:{
        "type": 904,
        "open_level": 1,
        "union": [],
    },

    9005:{
        "type": 902,
        "open_level": 1,
        "union": [],
    },

    9006:{
        "type": 303,
        "open_level": 1,
        "union": [],
    },

}

activity_type_cfg = {}
for act_id, act in activity_cfg.items():
    if act["type"] not in activity_type_cfg:
        activity_type_cfg[act["type"]] = [act_id]
    else:
        activity_type_cfg[act["type"]].append(act_id)

