#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
from datetime import datetime
from fabric.api import *

# 服务器登录用户名:
env.user = 'root'
# sudo用户为root:
env.sudo_user = 'root'
# 服务器地址，可以有多个，依次部署:
env.key_filename = "~/.ssh/xtzj"

_TAR_FILE = '%s_%s_xtzj.tar.gz'
_TMP_STORAGE_CONFIG_FILE = 'cfgs/%s_%s_storage.conf'
_STORAGE_CONFIG_FILE = 'apps/configs/app_config/storage.conf'

_REMOTE_TMP_TAR = '/tmp/xtzj/xtzj.tar.gz'
_PROJECT_NAME = 'xtzj'
_REMOTE_BASE_DIR = '/xtzj'

env.roledefs = {
    'prod_ios_dev_servers': ["120.92.4.217"],
    'prod_android_servers': [],
}

admin_ips = {
    "ios": {
        "prod": ['123.206.67.27'],
        "test": ['123.206.70.121'],
        "dev": ['120.92.4.217'],
    },
}

def build(plat, env):
    if plat not in ["ios","android"] or env not in ["prod", "test", "dev"]:
        print "usage: fab build:[ios | android]"
        print "usage: fab build:plat=[ios | android]"
        print "usage: fab build:[ios | android],[arg2]"
        sys.exit()
    else:
        # local('sh ../tools/build_py.sh %s' % plat)
        # 清除历史 *.pyc 文件
        local('find %s -iname "*.pyc" -exec rm -f {} \;' % os.path.abspath('.'))
        local("""echo "ADMIN_WHITE_IPS = %s" >> settings/prod.py""" % admin_ips[plat][env])
        # 编译新的 *.pyc 文件
        local('python -m compileall apps && \
               python -m compileall libs && \
               python -m compileall torngas && \
               python -m compileall scripts && \
               python -m compileall settings && \
               python -m compileall runserver.py')

        includes = os.listdir(os.path.abspath('.'))
        excludes = ['dist', 'log', 'cfgs', 'logs', 'apps/*.py', 'libs/*.py', \
                    'torngas/*.py', 'scripts/*.py', 'settings/*.py', \
                    '*.pyo', '.DS_Store', '.git*', 'runserver.py', \
                    'fabfile.py', 'deploy', 'start.sh']

        local('cp %s %s' % (_TMP_STORAGE_CONFIG_FILE % (plat, env), _STORAGE_CONFIG_FILE))  # 放置正确的存储配置
        local('rm -f dist/%s' % (_TAR_FILE % (plat, env)))
        cmd = ['tar', '--dereference', '-czvf', 'dist/%s' % (_TAR_FILE % (plat, env))]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)

        local(' '.join(cmd))
        local("git co settings/prod.py apps/configs/app_config/storage.conf")        # 把PROD文件和存储配置文件恢复到初始状态

def pre_deploy(plat, env):
    """正式发布预处理
    """
    newdir = '%s_%s' % (_PROJECT_NAME, datetime.now().strftime('%y_%m_%d_%H_%M_%S'))
    run('rm -f %s' % _REMOTE_TMP_TAR)             # 删除已有的tar文件
    put('dist/%s' % _TAR_FILE % (plat, env), _REMOTE_TMP_TAR)   # 上传新的tar文件

    # 创建新目录:
    with cd(_REMOTE_BASE_DIR):
        run('mkdir %s' % newdir)

    # 解压到新目录:
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        run('tar -xzvf %s' % _REMOTE_TMP_TAR)

    # 重置软链接:
    with cd(_REMOTE_BASE_DIR):
        run('rm -f %s' % _PROJECT_NAME)
        run('ln -s %s %s' % (newdir, _PROJECT_NAME))
        run('cp start.sh %s/' % _PROJECT_NAME)

# def start():
#     """启动supervisord服务
#     """
#     with settings(warn_only=True):
#         sudo('supervisord -c /etc/supervisord.conf')

# def stop():
#     """停止supervisord服务
#     """
#     with settings(warn_only=True):
#         sudo('supervisorctl shutdown')

# def restart():
#     """重启python服务，绑定进程和CPU
#     """
#     with settings(warn_only=True):
#         sudo('supervisorctl stop %s:*' % _PROJECT_NAME)
#         sudo('supervisorctl start %s:*' % _PROJECT_NAME)

#     # 绑定CPU核心和工作进程:
#     with settings(warn_only=True):
#         work_processes = run("ps aux | grep python | grep -v grep | grep -v supervisord | awk '{print $2}'")
#         for index,pid in enumerate(work_processes.split('\r\n')):
#             if index:
#                 run('taskset -pc %s %s' % (index, pid))
def start():
    """启动supervisord服务
    """
    with cd(_REMOTE_BASE_DIR+"/"+_PROJECT_NAME):
        sudo('sh start.sh prod ios start')

def stop():
    """停止supervisord服务
    """
    with cd(_REMOTE_BASE_DIR+"/"+_PROJECT_NAME):
        sudo('sh start.sh prod ios stop')

def restart():
    """重启python服务，绑定进程和CPU
    """
    with cd(_REMOTE_BASE_DIR+"/"+_PROJECT_NAME):
        sudo('sh start.sh prod ios restart')

def do_deploy(plat, env, cmd):
    """
    """
    if cmd == "start" or cmd == "restart":
        pre_deploy(plat, env)
        exec(cmd+"()")
    else:
        exec(cmd+"()")

@roles('prod_ios_dev_servers')
def prod_ios_deploy(plat, env, cmd):
    do_deploy(plat, env, cmd)

@roles('prod_android_servers')
def prod_android_deploy(plat, env, cmd):
    do_deploy(plat, env, cmd)

def deploy(plat, env, cmd):
    if plat not in ["ios","android"]:
        print "usage: fab deploy:[ios | android]"
        print "usage: fab deploy:plat=[ios | android]"
        print "usage: fab deploy:[ios | android],[arg2]"
        sys.exit()
    else:
        if plat == "ios":
            execute(prod_ios_deploy, plat, env, cmd)
        elif plat == "android":
            execute(prod_android_deploy, plat, env, cmd)
        else:
            pass
