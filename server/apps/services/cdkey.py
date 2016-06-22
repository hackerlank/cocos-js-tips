#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-10 11:15:58
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     物品兑换码服务
# @end
# @copyright (C) 2015, kimech

from libs.rklib.core import app

mysql_engine = app.get_storage_engine("mysql")

def check_code_exist(code):
    """检测兑换码是否存在

    Args:
        code 兑换码
    """
    key_tag = code[:4]
    try:
        result = mysql_engine.master_get("SELECT * FROM cdkey_%s WHERE code = '%s'" % (key_tag, code))
        if result:
            return True
        else:
            return False
    except:
        return False

def check_code_used_by_other(code):
    """检测兑换码是否被别人使用

    Args:
        code 兑换码
    """
    try:
        key_tag = code[:4]
        result = mysql_engine.master_get("SELECT * FROM cdkey_%s WHERE code = '%s'" % (key_tag, code))

        if result.uid is None:
            return False
        else:
            return True
    except:
        return True

def update_cdkey_info(code, uid):
    """更新兑换码的信息

    Args:
        code :兑换码
        uid :使用者UID
    """
    try:
        sql = "UPDATE cdkey_%s SET uid ='%s' WHERE code = '%s'" % (code[:4], uid, code)
        mysql_engine.master_execute(sql)
    except:
        pass
