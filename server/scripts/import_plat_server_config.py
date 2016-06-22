#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-10-09 20:47:03
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   定时排行脚本
# @end
# @copyright (C) 2015, kimech

import os
import sys
import time
import datetime
import traceback
import cPickle as pickle

if len(sys.argv) == 3:
    ENV = sys.argv[1]
    PLAT = sys.argv[2]
    ENV = ENV.upper()
else:
    print "useage: python import_plat_server_config.py [local|dev|prod] [ios|android|apple]\n"
    sys.exit()

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BASE_DIR + '/apps')

import settings
os.environ.setdefault('KIMECH_APP_SETTINGS', 'settings.%s' % ENV.lower())

from libs.rklib.core import app
app.init(plat = PLAT.lower(),
         storage_cfg_file = BASE_DIR + "/apps/configs/app_config/storage.conf",
         logic_cfg_file = BASE_DIR + "/apps/configs/app_config/logic.conf",
         model_cfg_file = BASE_DIR + "/apps/configs/app_config/model.conf")

if PLAT.lower() not in ["ios","android","banshu","local","dev","apple"]:
    print "useage: python import_plat_server_config.py [local|dev|prod] [ios|android|apple]\n"
    sys.exit()
else:
    deault_pconfig = {
        "cdn_url": "http://example/xtzj/ios/resources/",
        "remote_manifest_url": "http://example/xtzj/ios/version/project.manifest",
        "test_resource_version": "",
        "prod_resource_version": "",
    }

    platconfig = {
        "DEV": pickle.dumps({"sign": "DEV", "name": "", "checker": "auth_XTZJ"}),
        "LOCAL": pickle.dumps({"sign": "LOCAL", "name": "", "checker": "auth_XTZJ"}),

        "XY": pickle.dumps({"sign": "XY", "name": "", "checker": "auth_EZ"}),
        "HM": pickle.dumps({"sign": "HM", "name": "", "checker": "auth_EZ"}),
        "AS": pickle.dumps({"sign": "AS", "name": "", "checker": "auth_EZ"}),
        "XX": pickle.dumps({"sign": "XX", "name": "", "checker": "auth_EZ"}),
        "TB": pickle.dumps({"sign": "TB", "name": "", "checker": "auth_EZ"}),
        "LE": pickle.dumps({"sign": "TB", "name": "", "checker": "auth_EZ"}),
        "iTools": pickle.dumps({"sign": "iTools", "name": "", "checker": "auth_EZ"}),

        "KY": pickle.dumps({"sign": "KY", "name": "", "checker": "auth_WHWJ"}),
        "PP": pickle.dumps({"sign": "PP", "name": "", "checker": "auth_WHWJ"}),
        "WHWJ": pickle.dumps({"sign": "WHWJ", "name": "", "checker": "auth_WHWJ"}),

        "ANZHI": pickle.dumps({"sign": "ANZHI", "name": "ANZHI", "checker": "auth_WHWJ"}),
        "BAIDU": pickle.dumps({"sign": "BAIDU", "name": "BAIDU", "checker": "auth_WHWJ"}),
        "DOWNJOY": pickle.dumps({"sign": "DOWNJOY", "name": "DOWNJOY", "checker": "auth_WHWJ"}),
        "HUAWEI": pickle.dumps({"sign": "HUAWEI", "name": "HUAWEI", "checker": "auth_WHWJ"}),
        "JINLI": pickle.dumps({"sign": "JINLI", "name": "JINLI", "checker": "auth_WHWJ"}),
        "OPPO": pickle.dumps({"sign": "OPPO", "name": "OPPO", "checker": "auth_WHWJ"}),
        "VIVO": pickle.dumps({"sign": "VIVO", "name": "VIVO", "checker": "auth_WHWJ"}),
        "QIHOO": pickle.dumps({"sign": "QIHOO", "name": "QIHOO", "checker": "auth_WHWJ"}),
        "UC": pickle.dumps({"sign": "UC", "name": "UC", "checker": "auth_WHWJ"}),
        "XIAOMI": pickle.dumps({"sign": "XIAOMI", "name": "XIAOMI", "checker": "auth_WHWJ"}),
        "YSDK": pickle.dumps({"sign": "YSDK", "name": "YSDK", "checker": "auth_WHWJ"}),
        "KUPAI": pickle.dumps({"sign": "KUPAI", "name": "KUPAI", "checker": "auth_WHWJ"}),
        "LENOVO": pickle.dumps({"sign": "LENOVO", "name": "LENOVO", "checker": "auth_WHWJ"}),
        "MEIZU": pickle.dumps({"sign": "MEIZU", "name": "MEIZU", "checker": "auth_WHWJ"}),
        "PPS": pickle.dumps({"sign": "PPS", "name": "PPS", "checker": "auth_WHWJ"}),
        "PPTV": pickle.dumps({"sign": "PPTV", "name": "PPTV", "checker": "auth_WHWJ"}),
        "YOUKU": pickle.dumps({"sign": "YOUKU", "name": "YOUKU", "checker": "auth_WHWJ"}),
        "WDJ": pickle.dumps({"sign": "WDJ", "name": "WDJ", "checker": "auth_WHWJ"}),
        "SINA": pickle.dumps({"sign": "SINA", "name": "SINA", "checker": "auth_WHWJ"}),
        "WOGAME": pickle.dumps({"sign": "WOGAME", "name": "WOGAME", "checker": "auth_WHWJ"}),
        "MOBILE": pickle.dumps({"sign": "MOBILE", "name": "MOBILE", "checker": "auth_WHWJ"}),
        "HAIMA_A": pickle.dumps({"sign": "HAIMA_A", "name": "HAIMA_A", "checker": "auth_WHWJ"}),
        "MZW": pickle.dumps({"sign": "MZW", "name": "MZW", "checker": "auth_WHWJ"}),
        "DOUYU": pickle.dumps({"sign": "DOUYU", "name": "DOUYU", "checker": "auth_WHWJ"}),
        "AYX": pickle.dumps({"sign": "AYX", "name": "AYX", "checker": "auth_WHWJ"}),
        "GFENG": pickle.dumps({"sign": "GFENG", "name": "GFENG", "checker": "auth_WHWJ"}),
        "PYW": pickle.dumps({"sign": "PYW", "name": "PYW", "checker": "auth_WHWJ"}),
        "KUAIYONG": pickle.dumps({"sign": "KUAIYONG", "name": "KUAIYONG", "checker": "auth_WHWJ"}),
        "KPZS": pickle.dumps({"sign": "KPZS", "name": "KPZS", "checker": "auth_WHWJ"}),
        "TTYY": pickle.dumps({"sign": "TTYY", "name": "TTYY", "checker": "auth_WHWJ"}),
        "PAPA": pickle.dumps({"sign": "PAPA", "name": "PAPA", "checker": "auth_WHWJ"}),
        "YLY": pickle.dumps({"sign": "YLY", "name": "YLY", "checker": "auth_WHWJ"}),
        "HTC": pickle.dumps({"sign": "HTC", "name": "HTC", "checker": "auth_WHWJ"}),
        "YYH": pickle.dumps({"sign": "YYH", "name": "YYH", "checker": "auth_WHWJ"}),
        "MUMAYI": pickle.dumps({"sign": "MUMAYI", "name": "MUMAYI", "checker": "auth_WHWJ"}),
        "YOUYI": pickle.dumps({"sign": "YOUYI", "name": "YOUYI", "checker": "auth_WHWJ"}),
        "ANQU": pickle.dumps({"sign": "ANQU", "name": "ANQU", "checker": "auth_WHWJ"}),
        "DWYY": pickle.dumps({"sign": "DWYY", "name": "DWYY", "checker": "auth_WHWJ"}),
        "YOUMI": pickle.dumps({"sign": "YOUMI", "name": "YOUMI", "checker": "auth_WHWJ"}),
        "PIAOJIAO": pickle.dumps({"sign": "PIAOJIAO", "name": "PIAOJIAO", "checker": "auth_WHWJ"}),
        "LINYOU": pickle.dumps({"sign": "LINYOU", "name": "LINYOU", "checker": "auth_WHWJ"}),
        "LEWAN": pickle.dumps({"sign": "LEWAN", "name": "LEWAN", "checker": "auth_WHWJ"}),
        "SHOUMENG": pickle.dumps({"sign": "SHOUMENG", "name": "SHOUMENG", "checker": "auth_WHWJ"}),
        "HUPU": pickle.dumps({"sign": "HUPU", "name": "HUPU", "checker": "auth_WHWJ"}),
        "GUOPAN_A": pickle.dumps({"sign": "GUOPAN_A", "name": "GUOPAN_A", "checker": "auth_WHWJ"}),
        "MOGE": pickle.dumps({"sign": "MOGE", "name": "MOGE", "checker": "auth_WHWJ"}),
        "LESHI": pickle.dumps({"sign": "LESHI", "name": "LESHI", "checker": "auth_WHWJ"}),
        "SHUNWANG": pickle.dumps({"sign": "SHUNWANG", "name": "SHUNWANG", "checker": "auth_WHWJ"}),
        "07073GAME": pickle.dumps({"sign": "07073GAME", "name": "07073GAME", "checker": "auth_WHWJ"}),
        "SHANGFANG": pickle.dumps({"sign": "SHANGFANG", "name": "SHANGFANG", "checker": "auth_WHWJ"}),
        "NUBIA": pickle.dumps({"sign": "NUBIA", "name": "NUBIA", "checker": "auth_WHWJ"}),

    }
    if PLAT.lower() == "android":
        pconfig = deault_pconfig
        sconfig = {
            "server_id": 1,
            "server_config": {
                "server_id": 1,
                "server_name": "心跳战姬",
                "domain": "http://android.xtzj.luckyfuturetech.com",
                "plat": "android",
                "state": 1,
                "tags": 0,
                "open_time": int(time.time()),
            }
        }

    elif PLAT.lower() == "ios":
        pconfig = deault_pconfig
        sconfig = {
            "server_id": 1,
            "server_config": {
                "server_id": 1,
                "server_name": "心跳战姬",
                "domain": "http://120.92.4.217:8000",
                "plat": "ios",
                "state": 1,
                "tags": 0,
                "open_time": 1462789941,
            }
        }

    elif PLAT.lower() == "dev":
        pconfig = deault_pconfig
        platconfig = {
            "DEV": pickle.dumps({"sign": "DEV", "name": "", "checker": "auth_XTZJ"}),
            "LOCAL": pickle.dumps({"sign": "LOCAL", "name": "", "checker": "auth_XTZJ"}),
        }
        sconfig = {
            "server_id": 1,
            "server_config": {
                "server_id": 1,
                "server_name": "开发一服",
                "domain": "http://192.168.1.211:8000",
                "plat": "dev",
                "state": 1,
                "tags": 0,
                "open_time": int(time.time()),
            }
        }

    elif PLAT.lower() == "local":
        pconfig = deault_pconfig
        platconfig = {
            "DEV": pickle.dumps({"sign": "DEV", "name": "", "checker": "auth_XTZJ"}),
            "LOCAL": pickle.dumps({"sign": "LOCAL", "name": "", "checker": "auth_XTZJ"}),
        }
        sconfig = {
            "server_id": 1,
            "server_config": {
                "server_id": 1,
                "server_name": "本地一服",
                "domain": "http://127.0.0.1:8000",
                "plat": "dev",
                "state": 1,
                "tags": 0,
                "open_time": int(time.time()),
            }
        }
    else:
        sys.exit()

#  ==================== REDIS & MYSQL ======================  #
redis_client = app.get_storage_engine('redis').client.current

redis_client.hmset("xtzj.%s.config" % PLAT.lower(), pconfig)
redis_client.hmset("xtzj.%s.plats" % PLAT.lower(), platconfig)
redis_client.hset("xtzj.%s.servers" % PLAT.lower(), sconfig["server_id"], pickle.dumps(sconfig["server_config"]))

# from sqlalchemy import create_engine
# mysql = app.get_storage_engine("mysql")
# mysql_master_config = mysql.servers["master"] # ("10.137.218.249:3306", "admin", "Whwj12345*", "xtzj_game_whwj")

# pair = mysql_master_config[0].split(":")
# mysql_host = pair[0]

# admin_mysql_name = "xtzj_admin"
# mysql_engine = create_engine("mysql://%s:%s@%s/%s?charset=utf8&connect_timeout=3" % (mysql_master_config[1], mysql_master_config[2], mysql_host, admin_mysql_name), pool_recycle=7200)

# admin_platform_table_sql = "DROP TABLE IF EXISTS `platforms`;CREATE TABLE `platforms` (`sign` varchar(40) NOT NULL,`name` varchar(40) NOT NULL,`mysql_db_name` varchar(40) NOT NULL,`mysql_db_host` varchar(40) NOT NULL,`mysql_db_port` int(11) NOT NULL,`mysql_db_user` varchar(40) NOT NULL,`mysql_db_password` varchar(40) DEFAULT NULL,`redis_host` varchar(40) DEFAULT NULL,`redis_port` int(11) NOT NULL,`redis_password` varchar(40) DEFAULT NULL,`tip` varchar(100) DEFAULT NULL,PRIMARY KEY (`sign`)) ENGINE=InnoDB DEFAULT CHARSET=utf8;"

# game_orders_table_sql = """
# CREATE TABLE `orders` (
#   `id` int(11) NOT NULL AUTO_INCREMENT,
#   `orderid` varchar(100) NOT NULL COMMENT '订单编号',
#   `account_id` varchar(64) NOT NULL COMMENT '玩家账户',
#   `uid` varchar(64) NOT NULL COMMENT '玩家游戏唯一UID',
#   `plat` varchar(11) DEFAULT NULL COMMENT '所属平台',
#   `sid` int(11) NOT NULL DEFAULT '1' COMMENT '所属服务器',
#   `charge_id` int(11) NOT NULL COMMENT '充值券编号',
#   `price` int(11) DEFAULT NULL COMMENT '金额',
#   `charged_amount` int(11) DEFAULT '0' COMMENT '实际充值金额',
#   `status` int(11) NOT NULL DEFAULT '1' COMMENT '订单状态',
#   `created_at` int(16) NOT NULL COMMENT '发起充值时间戳',
#   `completed_at` int(16) DEFAULT NULL COMMENT '完成订单时间戳',
#   `extra` varchar(100) DEFAULT NULL COMMENT '保留字段，以备处理各个渠道特殊字段',
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='充值数据表';
# """

# redis = app.get_storage_engine('redis')

# insert_new_plat_sql = """
# INSERT INTO `platforms` (`sign`, `name`, `mysql_db_name`, `mysql_db_host`, \
# `mysql_db_port`, `mysql_db_user`, `mysql_db_password`, `redis_host`, \
# `redis_port`, `redis_password`, `tip`) VALUES ('%s','%s','%s','%s',%s, \
# '%s','%s','%s',%s,'%s','');
# """ % (PLAT.lower(), PLAT.lower(), mysql_master_config[-1], mysql_host, 3306, mysql_master_config[1], mysql_master_config[2], redis.redis_host, redis.redis_port, redis.redis_passwd)

# def _check_table_exist(name):
#     tables = mysql_engine.execute("show tables;")
#     exist_tables = [str(table[0]) for table in tables.fetchall()]

#     if name not in exist_tables:
#         return False
#     else:
#         return True

# # 检查admin数据库
# if _check_table_exist("platforms"):
#     mysql_engine.execute(insert_new_plat_sql)
# else:
#     mysql_engine.execute(admin_platform_table_sql)
#     mysql_engine.execute(insert_new_plat_sql)

# # 检查game数据库
# if not _check_table_exist("orders"):
#     mysql_engine.execute(game_orders_table_sql)
