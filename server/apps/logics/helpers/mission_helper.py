#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-11-23 11:11:40
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   副本辅助模块
# @end
# @copyright (C) 2015, kimech

import copy
import random

def random_mission_award(awards, num):
    """随机副本掉落物品

    Args:
        awards 掉落库
            物品包ID:权值。[{300000: 125}, {300001: 125}, {300001: 125}],
        num 掉落包个数

    Returns:
        物品掉落包 ： [30000, 300001]
    """
    award_packs = []
    chose_indexes = []
    for i in xrange(num):
        awards_tmp = copy.deepcopy([item for index, item in enumerate(awards) if index not in chose_indexes])
        rand_sum = sum([a.values()[0] for a in awards_tmp])
        rand = random.randint(0, rand_sum)
        for index, item in enumerate(awards_tmp):
            rand -= item.values()[0]
            if rand <= 0:
                chose_indexes.append(index)
                award_packs.append(item.keys()[0])
                break

    return award_packs

