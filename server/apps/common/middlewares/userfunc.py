#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-22 21:37:49
# @Author : Jiank (http://jiankg.github.com)
# @doc
#     请求参数探测检查
# @end
# @copyright (C) 2015, kimech

import ujson
from apps.configs import game_config
from apps.configs import static_const
from apps.configs.msg_code import MsgCode
from torngas.settings_manager import settings

class UserFuncMiddleware(object):
    def process_request(self, handler, clear):
        """匹配路由后，执行处理handler时调用,**支持异步**

        检测玩家功能是否开启，未开启 打回！

        Args:
            handler: handler对象

        """
        request_path = handler.request.uri
        # 非游戏业务逻辑接口，直接跳过功能开启检测
        if request_path != settings.GAME_API_URL:
            return

        context = handler.request.request_context
        api_method = context.get_parameter("method", "")

        if api_method in ["system.heartbeat", "system.apple_pay_notification"]:
            return

        elif api_method in ["equip.upgrade", "equip.weak", "equip.anti_weak"]:
            return

        elif api_method in ["mission.enter", "mission.past", "mission.reset", "mission.hangup", "mission.mission_award", "mission.chapter_award"]:
            return

        elif api_method in ["mall.info", "mall.refresh", "mall.buy"]:
            return

        elif api_method in ["act_mission.info", "act_mission.enter", "act_mission.past", "act_mission.award", "act_mission.hangup"]:
            return

        else:
            # 业务逻辑接口方法不能为空
            func_id = static_const.USER_FUNC_MAPPING.get(api_method, 0)
            if not func_id:
                open_level = 0
            else:
                open_level = game_config.user_func_cfg.get(func_id, 1)

            if open_level > context.user.game_info.role_level:
                handler.finish(ujson.dumps({"mc": MsgCode['UserModuleNotOpen']}))
                return
