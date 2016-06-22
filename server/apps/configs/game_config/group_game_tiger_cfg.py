#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date :
# @Author : Jiank
# @doc
#     !!! 前方配置高能, 均为自动生成, 随意改动可能会有不可思议的事情发生 !!!
# @end
# @copyright (C) 2015, kimech

group_game_tiger_cfg = {

    1000:{
        "id": 1000,
        "cur_num": 0,
        "weight":  0,
        "final_num":  0,
    },

    1001:{
        "id": 1001,
        "cur_num": 0,
        "weight":  1600,
        "final_num":  1,
    },

    1002:{
        "id": 1002,
        "cur_num": 0,
        "weight":  1600,
        "final_num":  2,
    },

    1003:{
        "id": 1003,
        "cur_num": 0,
        "weight":  200,
        "final_num":  3,
    },

    1004:{
        "id": 1004,
        "cur_num": 0,
        "weight":  200,
        "final_num":  4,
    },

    1005:{
        "id": 1005,
        "cur_num": 0,
        "weight":  50,
        "final_num":  5,
    },

    1006:{
        "id": 1006,
        "cur_num": 1,
        "weight":  0,
        "final_num":  1,
    },

    1007:{
        "id": 1007,
        "cur_num": 1,
        "weight":  10000,
        "final_num":  2,
    },

    1008:{
        "id": 1008,
        "cur_num": 1,
        "weight":  10000,
        "final_num":  3,
    },

    1009:{
        "id": 1009,
        "cur_num": 1,
        "weight":  1000,
        "final_num":  4,
    },

    1010:{
        "id": 1010,
        "cur_num": 1,
        "weight":  100,
        "final_num":  5,
    },

    1011:{
        "id": 1011,
        "cur_num": 2,
        "weight":  10000,
        "final_num":  2,
    },

    1012:{
        "id": 1012,
        "cur_num": 2,
        "weight":  10000,
        "final_num":  3,
    },

    1013:{
        "id": 1013,
        "cur_num": 2,
        "weight":  1000,
        "final_num":  4,
    },

    1014:{
        "id": 1014,
        "cur_num": 2,
        "weight":  100,
        "final_num":  5,
    },

    1015:{
        "id": 1015,
        "cur_num": 3,
        "weight":  10000,
        "final_num":  3,
    },

    1016:{
        "id": 1016,
        "cur_num": 3,
        "weight":  2000,
        "final_num":  4,
    },

    1017:{
        "id": 1017,
        "cur_num": 3,
        "weight":  1000,
        "final_num":  5,
    },

    1018:{
        "id": 1018,
        "cur_num": 4,
        "weight":  10000,
        "final_num":  4,
    },

    1019:{
        "id": 1019,
        "cur_num": 4,
        "weight":  2000,
        "final_num":  5,
    },

}

gg_tiger_map = {}
for a in group_game_tiger_cfg.values():
    try:
        gg_tiger_map[a["cur_num"]].append(a["id"])
    except KeyError:
        gg_tiger_map[a["cur_num"]] = [a["id"]]

