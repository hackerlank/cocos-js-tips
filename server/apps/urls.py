# !/usr/bin/env python
# -*- coding: utf-8 -*-
from torngas import Url, route

u = Url('apps.handlers')

#
urls = route(
    u(name='index', pattern=r'/?', handler='admin.Index'),

    u(name='PlatformVersion', pattern=r'/platform/version?', handler='platform.Version'),
    u(name='PlatformRegist', pattern=r'/platform/regist?', handler='platform.Regist'),
    u(name='PlatformExpress', pattern=r'/platform/express?', handler='platform.Express'),
    u(name='PlatformBind', pattern=r'/platform/bind?', handler='platform.Bind'),
    u(name='PlatformAuth', pattern=r'/platform/auth?', handler='platform.Auth'),
    u(name='GameLogin', pattern=r'/game/login?', handler='game.Login'),
    u(name='GameApi', pattern=r'/game/api?', handler='game.Api'),
    u(name='Notification', pattern=r'/notification/(.*)', handler='charge.Notification'),

    u(name='Admin', pattern=r'/A6ksi?', handler='admin.Admin'),
    u(name='Debug', pattern=r'/debug?', handler='debug_tools.Debug'),
)
