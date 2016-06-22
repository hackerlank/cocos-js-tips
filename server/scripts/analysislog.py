#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import redis
import logging
import datetime

from sqlalchemy import create_engine

CHANNEL = "ios"
LOG_PATH = "/xtzj/game_logs/tmp"
PLATFORM_SERVER_KEY = "xtzj.%s.servers" % CHANNEL
#  ==================== REDIS & MYSQL ======================  #
database = {
    "mysql": {
        "host": "10.137.218.47",
        "port": 3306,
        "user": "admin",
        "passoword": "Whwj160408",
        "db_name": "xtzj_game_%s" % CHANNEL,
    },
    "redis": {
        "host": "10.137.194.112",
        "port": 6379,
        "passoword": "",
    }
}

_mysql_engine = create_engine("mysql://%s:%s@%s/%s?charset=utf8&connect_timeout=5" % (
                                database["mysql"]["user"], database["mysql"]["passoword"],
                                    database["mysql"]["host"], database["mysql"]["db_name"]),
                                        pool_recycle=7200)

_redis_client = redis.StrictRedis(host=database["redis"]["host"],
                                    port=database["redis"]["port"],
                                        password=database["redis"]["passoword"],
                                            socket_timeout=10)

#  ========================================================  #
TODAY = time.strftime('%Y%m%d')

stat_dau_table_sql = """
CREATE TABLE IF NOT EXISTS `stat_dau_%s` (
  `uid` varchar(64) NOT NULL COMMENT '用户ID',
  `account_id` varchar(64) NOT NULL COMMENT '账户',
  `platform` varchar(32) NOT NULL COMMENT '平台',
  `server` int(32) NOT NULL COMMENT '服务器',
  `create_at` int(32) NOT NULL COMMENT '创建时间',
  `login_at` int(32) NOT NULL COMMENT '今日最后一次登录时间',
  `stay` int(16) NOT NULL COMMENT '留存天数',
  `login_times` int(16) NOT NULL COMMENT '今日登录次数',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户登录数据表';
"""

access_api_report_table_sql = """
CREATE TABLE IF NOT EXISTS `access_api_report_%s` (
  `api` varchar(64) NOT NULL COMMENT '游戏接口',
  `success` int(32) NOT NULL COMMENT '成功次数',
  `fail` int(32) NOT NULL COMMENT '失败次数',
  `avg` float NOT NULL COMMENT '平均处理时长',
  `max` float NOT NULL COMMENT '最大处理时长',
  `min` float NOT NULL COMMENT '最小处理时长',
  PRIMARY KEY (`api`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='处理请求报告';
"""

access_hour_report_table_sql = """
CREATE TABLE IF NOT EXISTS `access_hour_report_%s` (
  `hour` int(32) NOT NULL COMMENT '',
  `connect` int(32) NOT NULL COMMENT '',
  `avg_use_time` float NOT NULL COMMENT '',
  PRIMARY KEY (`hour`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

game_data_table_sql = """
CREATE TABLE IF NOT EXISTS `game_data` (
  `date` varchar(32) NOT NULL COMMENT '日期',
  `platform` varchar(32) NOT NULL COMMENT '平台',
  `sid` int(32) NOT NULL COMMENT '服务器ID',
  `regist` int(32) default 0 COMMENT '今日注册',
  `login` int(32) default 0 COMMENT '今日活跃',
  `retention_1` float default 0 COMMENT '次日留存',
  `retention_3` float default 0 COMMENT '3日留存',
  `retention_4` float default 0 COMMENT '4日留存',
  `retention_5` float default 0 COMMENT '5日留存',
  `retention_6` float default 0 COMMENT '6日留存',
  `retention_7` float default 0 COMMENT '7日留存',
  `retention_8` float default 0 COMMENT '8日留存',
  `retention_14` float default 0 COMMENT '14日留存',
  `retention_30` float default 0 COMMENT '30日留存',
  PRIMARY KEY (`date`, `platform`, `sid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='关键数据汇总';
"""

# ==========================================================================================
def _check_table_exist(table_name):
    tables = _mysql_engine.execute("show tables;")
    exist_tables = [str(table[0]) for table in tables.fetchall()]

    return table_name in exist_tables

def _split_log_line(string):
    def target(start, end):
        test1 = string.split(start)
        try:
            _tar = test1[1].split(end)[0]
        except:
            _tar = test1[1]

        return _tar

    if "status" in string:
        status = target(" status:", "")
    else:
        status = 200

    return target(" ip:", " api:"), target("[", "] "), target("api:", " args:"), int(status), float(target("utime:", "ms"))

def datestamp(datestring):
    """对应日期零点的时间戳

    Args:
        20151204

    Returns:
        1449205100
    """
    format = "%Y%m%d"
    date = datetime.datetime.strptime(datestring, format)

    return int(date.strftime("%s"))

def get_type_log(target, log_type, files):
    tmp = target
    if os.path.isfile(target):
        if target.find(log_type) > 1 and target.endswith(".log"):
            files.append(target)

    elif os.path.isdir(target):
        for s in os.listdir(target):
            tmp = os.path.join(target, s)

            get_type_log(tmp, log_type, files)

    return files

# =========================================================================================
def stat_access_log():
    """对访问日志进行分析
    """
    # 遍历所有行
    log_num = 0
    log_dict = dict()
    log_time_count = dict()
    log_time_avg_use_time = dict()
    log_error_info = {}

    try:
        lines = []
        for accesslog in get_type_log(LOG_PATH, "access", []):
            if os.path.exists(accesslog):
                log_file = open(accesslog)
                lines += log_file.readlines()
                log_file.close()
    except Exception, e:
        raise e

    for _line in lines:
        _line = _line.strip()
        # 充值日志暂时不统计
        if "notification" in _line:
            continue

        content = _split_log_line(_line)
        if content[1][:8] != TODAY or content[2] in [""]:
            continue

        log_time = datetime.datetime.strptime(content[1], "%Y%m%d %H:%M:%S")
        log_api = content[2]
        api_use_time = content[-1]

        if content[3] == 500:
            if log_api in log_error_info:
                log_error_info[log_api] += 1
            else:
                log_error_info[log_api] = 1

        # 记录连接次数
        if log_time.hour not in log_time_count:
            log_time_count[log_time.hour] = 1
        else:
            log_time_count[log_time.hour] += 1

        # 记录 平均响应时间
        if log_time.hour not in log_time_avg_use_time:
            log_time_avg_use_time[log_time.hour] = [api_use_time]
        else:
            log_time_avg_use_time[log_time.hour].append(api_use_time)

        if log_api not in log_dict:
            log_dict[log_api] = [api_use_time]
        else:
            log_dict[log_api].append(api_use_time)

        log_num += 1

    if log_dict:
        # # 创建表
        if not _check_table_exist('access_api_report_%s' % TODAY):
            _mysql_engine.execute(access_api_report_table_sql % TODAY)

        # 需要计算内容
        # 对应api 的连接次数 平均响应时间 最高响应时间 和最低响应时间
        sql = "REPLACE INTO access_api_report_%s (api, success, fail, avg, max, min) VALUES " % TODAY
        for key, val in log_dict.items():
            if key in log_error_info:
                fail = log_error_info[key]
            else:
                fail = 0

            print "Api:%s Num:%s Fail:%s Avg:%.2f(ms) Max:%.2f(ms) Min:%.2f(ms)" % (key, str(len(val) - fail), fail, round(sum(val)/len(val), 4), max(val), min(val))

            record = '("%s", %s, %s, %.2f, %.2f, %.2f),' % (key, str(len(val) - fail), fail, round(sum(val)/len(val), 4), max(val), min(val))
            sql += record

        _mysql_engine.execute(sql[:-1]+";")

    if log_time_count:
        # 创建表
        if not _check_table_exist('access_hour_report_%s' % TODAY):
            _mysql_engine.execute(access_hour_report_table_sql % TODAY)

        # 每小时连接次数
        sql1 = "REPLACE INTO access_hour_report_%s (hour, connect, avg_use_time) VALUES " % TODAY
        for _hour in xrange(0,25):
            _connect_num = log_time_count.get(_hour, 0)
            _connect_use_time_lst = log_time_avg_use_time.get(_hour, [])
            if _connect_use_time_lst:
                _connect_avg_use_time = round(sum(_connect_use_time_lst) / len(_connect_use_time_lst), 4)
            else:
                _connect_avg_use_time = 0

            print "Hour:" + str(_hour) + " connect:" + str(_connect_num) + " avg_use_time:%.2fms" % _connect_avg_use_time

            record = '(%s, %s, %.2f),' % (_hour, _connect_num, _connect_avg_use_time)
            sql1 += record

        _mysql_engine.execute(sql1[:-1]+";")

def stat_dau():
    """分析玩家每日登陆数据

    日志 format:
        账户 / 角色ID / 创建角色时间戳 / 最近登录时间戳 / 留存天数(今日登录日期 - 创建日期)
        DEV_account1/110000001/1448519912/1448519910/1

    mysql 表名:
        stat_dau_20151203

    mysql 数据表结构
        uid: 110000001
        account_id: DEV_account1
        create_at: 1448519912
        login_at: 1448519910
        stay: 1
        login_times: 12

    mysql 分表:
        按日期

    """
    try:
        lines = []
        for logfile in get_type_log(LOG_PATH, "login", []):
            if os.path.exists(logfile):
                log_file = open(logfile)
                lines += log_file.readlines()
                log_file.close()

    except Exception, e:
        raise e

    user_dict = {}
    for _line in lines:
        _line = _line.strip()
        contents = _line.split("/")

        platform = contents[0].split("_")[0]
        server = contents[1][:-8]

        # 登录时间大于今日零点
        if int(contents[-2]) < datestamp(TODAY):
            continue

        if contents[1] not in user_dict:
            user_dict[contents[1]] = [contents[1], contents[0], platform, server, contents[2], contents[3], int(contents[4]), 1]
        else:
            user_dict[contents[1]][-3] = contents[-2]
            user_dict[contents[1]][-1] += 1

    if user_dict:
        if _check_table_exist('stat_dau_%s' % TODAY):
            _mysql_engine.execute("TRUNCATE table stat_dau_%s" % TODAY)

        sql = "REPLACE INTO stat_dau_%s (uid, account_id, platform, server, create_at, login_at, stay, login_times) VALUES "
        for user in user_dict:
            child_sql = '("%s", "%s", "%s", %s, %s, %s, %s, %s),' % tuple(user_dict[user])
            sql += child_sql

        # 创建表
        if not _check_table_exist('stat_dau_%s' % TODAY):
            _mysql_engine.execute(stat_dau_table_sql % TODAY)

        _mysql_engine.execute((sql[:-1]+";") % TODAY)

# ====================================================
def _query(sql):
    try:
        results = _mysql_engine.execute(sql)
        return results.fetchall()
    except Exception, e:
        raise e

def _fetch_plats(sid, date):
    """抓取有玩家来源的渠道

        PP KY等..
    """
    sql = "SELECT DISTINCT(`platform`) FROM `stat_dau_%s` WHERE server=%s;" % (date, sid)
    results = _query(sql)

    return [str(i[0]) for i in results]

def _grep_create_login_data(plat, sid, date):
    """抓取每日注册和活跃数据

    Args:
        plat 平台
        sid 服务器ID
        date 目标日期 20151207

    Returns:
        {"create": 0, "login": 0}
    """
    if plat != CHANNEL:
        sql = "SELECT * FROM stat_dau_%s WHERE platform='%s' and server=%s;" % (date,plat,sid)
    else:
        sql = "SELECT * FROM stat_dau_%s WHERE server=%s;" % (date,sid)

    results = _query(sql)

    begin = datestamp(date)
    end = begin + 86400

    login = len(results)
    create = len([r for r in results if begin <= r["create_at"] < end])

    return login, create

def stat_create_login_data(sid, date):
    """
    """
    plats = _fetch_plats(sid, date)
    # 算完个平台之后再算一次汇总的
    plats.append(CHANNEL)
    # 创建表
    if not _check_table_exist('game_data'):
        _mysql_engine.execute(game_data_table_sql)

    for p in plats:
        login, create = _grep_create_login_data(p, sid, date)

        sql = "REPLACE INTO game_data (date, platform, sid, regist, login) VALUES ('%s', '%s', %s, %s, %s);" % (date, p, sid, create, login)
        _mysql_engine.execute(sql)

        print "[SID: %s PLAT: %s] ** CREATE&LOGIN **: create: %s, login: %s" % (sid, p, create, login)

def _build_gamer_retention_sql(tag, date, create_begin, create_end, plat, sid):
    """计算留存

    Args:
        tag 1/3/7/14/30
        date 20151205
        create_begin 创建起始时间戳
        create_end 创建结束时间戳

    Returns:
        "SELECT ..."
    """
    dateformat = "%Y%m%d"
    rdate = datetime.datetime.strptime(date, dateformat) - datetime.timedelta(days = tag)
    date1 = rdate.strftime("%Y%m%d")

    if plat != CHANNEL:
        sql = "SELECT count(*) FROM stat_dau_%s WHERE `create_at` BETWEEN %s AND %s AND platform='%s' AND server=%s;" % (date1, create_begin, create_end, plat, sid)
    else:
        sql = "SELECT count(*) FROM stat_dau_%s WHERE `create_at` BETWEEN %s AND %s AND server=%s;" % (date1, create_begin, create_end, sid)

    return _check_table_exist("stat_dau_%s" % date1), sql, date1

def stat_retention_data(sid, date):
    """抓取每日注册和活跃数据

    20号零点过5分 统计19号会影响到的留存数据的日期
    比如 18号的次留 17号的三留 13号的7日留存...

    先查寻18号注册总人数  然后再查这些人里19号登陆过的人数  以此求留存

    Args:
        sid 服务器ID
        date 目标日期 20151207

    Returns:
        {"create": 0, "login": 0}
    """
    plats = _fetch_plats(sid, date)
    # 算完个平台之后再算一次汇总的
    plats.append(CHANNEL)
    for p in plats:
        # 因为包含当日，所以19号的次留 应该算是19号注册的玩家 21号登陆过的玩家 中间只差两天。
        for tag in [1,2,3,4,5,6,7,13,29]:
            begin, end = datestamp(date) - 86400 * tag, datestamp(date) - 86400 * (tag - 1) # 当日注册人数
            if p != CHANNEL:
                sql = "SELECT count(*) FROM stat_dau_%s WHERE `create_at` BETWEEN %s AND %s AND platform='%s' AND server=%s;" % (date, begin, end, p, sid)
            else:
                sql = "SELECT count(*) FROM stat_dau_%s WHERE `create_at` BETWEEN %s AND %s AND server=%s;" % (date, begin, end, sid)

            results = _query(sql)
            login = 0 if not results else int(results[0][0])

            table_exist, sql, create_date = _build_gamer_retention_sql(tag, date, begin, end, p, sid)
            if table_exist:
                results = _query(sql)
                create = 0 if not results else int(results[0][0])
                try:
                    rate = '%.4f' % (login / float(create))
                except Exception, e:
                    rate = 0
            else:
                create = 0
                rate = 0

            date_tag = tag if tag == 1 else tag+1
            sql = "UPDATE game_data SET retention_%s=%s WHERE date='%s' AND platform='%s' and sid=%s;" % (date_tag, rate, create_date, p, sid)
            _mysql_engine.execute(sql)

            print "[SID: %s PLAT: %s] ** RETENTION **: login_date: %s, create_date: %s, create: %s, login: %s, rate: %.4f" % (sid, p, date, create_date, create, login, float(rate))

# =========================================== MAIN ==============================================
def main():
    today = datetime.datetime.today()
    date = today - datetime.timedelta(days=0)
    target_date = date.strftime("%Y%m%d")

    _message = " ================ run auto_stat_per_hour at: %s ================" % datetime.datetime.now()
    print _message

    stat_access_log()
    print " >>>>>>>>>>>>>>> stat access log done <<<<<<<<<<<<<<<<"

    stat_dau()
    print " >>>>>>>>>>>>>>> stat daily active user done <<<<<<<<<<<<<<<<"

    results = _redis_client.hgetall(PLATFORM_SERVER_KEY)
    for sid in results:
        try:
            stat_create_login_data(sid, target_date)
            print "[%s - s%s] >>>>>>>>>>>>>>> stat today's create and login done <<<<<<<<<<<<<<<<" % (CHANNEL, sid)
        except Exception,e:
            print "[%s - s%s] stat_create_login_data ERROR, reason: %s" % (CHANNEL, sid, e)

        try:
            stat_retention_data(sid, target_date)
            print "[%s - s%s] >>>>>>>>>>>>>>> stat today's retention done <<<<<<<<<<<<<<<<" % (CHANNEL, sid)
        except Exception,e:
            print "[%s - s%s] stat_retention_data ERROR, reason: %s" % (CHANNEL, sid, e)

if __name__ == '__main__':
    main()
