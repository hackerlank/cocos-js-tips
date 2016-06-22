#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from tornado.options import define, options
from torngas.webserver import Server

define("runmode", default='runserver', help='run mode, runserver', type=str)

os.environ.setdefault('KIMECH_APP_SETTINGS', 'settings.local')

def pray_from_author():
    """
    """
    code = """
                       _ooOoo_
                      o8888888o
                      88" . "88
                      (| -_- |)
                      O\  =  /O
                   ____/`---'\____
                 .'  \\|     |//  `.
                /  \\|||  :  |||//  \\
               /  _||||| -:- |||||- \\
               |   | \\\  -  /// |   |
               | \_|  ''\---/''  |   |
               \  .-\__  `-`  ___/-. /
             ___`. .'  /--.--\  `. . __
          ."" '<  `.___\_<|>_/___.'  >'"".
         | | :  `- \`.;`\ _ /`;.`/ - ` : | |
         \  \ `-.   \_ __\ /__ _/   .-` /  /
    ======`-.____`-.___\_____/___.-`____.-'======
                       `=---='
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            佛祖镇楼             BUG辟易
    佛曰:
            写字楼里写字间，写字间里程序员；
            程序人员写程序，又拿程序换酒钱。
            酒醒只在网上坐，酒醉还来网下眠；
            酒醉酒醒日复日，网上网下年复年。
            但愿老死电脑间，不愿鞠躬老板前；
            奔驰宝马贵者趣，公交自行程序员。
            别人笑我忒疯癫，我笑自己命太贱；
            不见满街漂亮妹，哪个归得程序员？
    """

    print code

if __name__ == '__main__':
    """
    start server:

    eg: python runserver.py --address=192.168.1.101 --port=8000 --settings=settings.prod --plat=ios
    If you want to quickly start the service , you can do like this:
    from torngas.webserver import run

    run()
    """
    # 哈哈哈哈
    pray_from_author()

    server = Server()
    server.parse_command()

    if options.runmode == 'runserver':
        server.init_app_config()
        server.load_urls()
        server.load_application()
        server.load_httpserver()
        server.server_start()
    else:
        exit(0)
