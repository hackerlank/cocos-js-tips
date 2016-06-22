#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date :
# @Author : Jiank (http://jiankg.github.com)
# @doc
#       !!! 前方协议文件高能, 自动生成, 随意改动可能会有不可思议的事情发生 !!!
# @end
# @copyright (C) 2015, kimech
        
GameProto = {
    "m__platform__version__c2s": {
        "msg_id": 10001,
        "platform": str,
    }, 

    "m__platform__auth__c2s": {
        "msg_id": 10002,
        "platform": str,
        "auth_params": str,
    }, 

    "m__game__login__c2s": {
        "msg_id": 10003,
        "platform": str,
        "account_id": str,
        "server_id": int,
        "session_id": str,
    }, 

    "m__api__system__heartbeat__c2s": {
        "msg_id": 10004,
    }, 

    "m__platform__regist__c2s": {
        "msg_id": 10005,
        "platform": str,
        "auth_params": str,
    }, 

    "m__platform__express__c2s": {
        "msg_id": 10006,
        "platform": str,
    }, 

    "m__platform__bind__c2s": {
        "msg_id": 10007,
        "platform": str,
        "tmp_auth_params": str,
        "auth_params": str,
    }, 

    "m__api__user__update_name__c2s": {
        "msg_id": 20002,
        "name": str,
    }, 

    "m__api__user__update_sign__c2s": {
        "msg_id": 20003,
        "sign": str,
    }, 

    "m__api__user__update_avatar__c2s": {
        "msg_id": 20004,
        "hero_id": int,
    }, 

    "m__api__user__buy_energy__c2s": {
        "msg_id": 20005,
    }, 

    "m__api__user__buy_gold__c2s": {
        "msg_id": 20006,
        "type": int,
    }, 

    "m__api__user__buy_skill_point__c2s": {
        "msg_id": 20007,
    }, 

    "m__api__user__get_user_info__c2s": {
        "msg_id": 20008,
        "uid": int,
    }, 

    "m__api__user__cdkey__c2s": {
        "msg_id": 20009,
        "code": str,
    }, 

    "m__api__user__skip_guide__c2s": {
        "msg_id": 20011,
        "step": int,
    }, 

    "m__api__user__debug__c2s": {
        "msg_id": 20010,
        "action": str,
        "items": "ignore",
    }, 

    "m__api__package__use__c2s": {
        "msg_id": 30001,
        "items": "ignore",
    }, 

    "m__api__package__sale__c2s": {
        "msg_id": 30002,
        "items": "ignore",
    }, 

    "m__api__package__express_buy__c2s": {
        "msg_id": 30003,
        "item_id": int,
        "item_num": int,
    }, 

    "m__api__hero__pick__c2s": {
        "msg_id": 40001,
        "ptype": int,
    }, 

    "m__api__hero__intensify__c2s": {
        "msg_id": 40002,
        "hero_id": int,
        "items": "ignore",
    }, 

    "m__api__hero__upgrade__c2s": {
        "msg_id": 40003,
        "hero_id": int,
    }, 

    "m__api__hero__weak__c2s": {
        "msg_id": 40004,
        "hero_id": int,
    }, 

    "m__api__hero__synthesis__c2s": {
        "msg_id": 40005,
        "index": int,
    }, 

    "m__api__hero__exchange_chip__c2s": {
        "msg_id": 40006,
        "target_chip_id": int,
        "exchange_type": int,
    }, 

    "m__api__hero__feed__c2s": {
        "msg_id": 40007,
        "hero_id": int,
        "items": "ignore",
    }, 

    "m__api__hero__marry__c2s": {
        "msg_id": 40008,
        "hero_id": int,
        "marry_id": int,
    }, 

    "m__api__hero__divorce__c2s": {
        "msg_id": 40009,
        "hero_id": int,
    }, 

    "m__api__equip__intensify__c2s": {
        "msg_id": 50001,
        "hero_id": int,
        "position": int,
        "to_level": int,
    }, 

    "m__api__equip__intensify2__c2s": {
        "msg_id": 50002,
        "hero_id": int,
        "position": int,
        "items": "ignore",
    }, 

    "m__api__equip__upgrade__c2s": {
        "msg_id": 50003,
        "hero_id": int,
        "position": int,
    }, 

    "m__api__equip__weak__c2s": {
        "msg_id": 50004,
        "hero_id": int,
        "position": int,
    }, 

    "m__api__equip__anti_weak__c2s": {
        "msg_id": 50005,
        "hero_id": int,
        "position": int,
    }, 

    "m__api__skill__intensify__c2s": {
        "msg_id": 60001,
        "hero_id": int,
        "skill_id": int,
        "level": int,
    }, 

    "m__api__spirit__intensify__c2s": {
        "msg_id": 70001,
        "hero_id": int,
        "spirit_id": int,
        "items": "ignore",
    }, 

    "m__api__spirit__intensify2__c2s": {
        "msg_id": 70002,
        "hero_id": int,
        "spirit_id": int,
    }, 

    "m__api__array__update__c2s": {
        "msg_id": 80001,
        "atype": int,
        "array": "ignore",
    }, 

    "m__api__mission__enter__c2s": {
        "msg_id": 90001,
        "mission_id": int,
        "fight": "ignore",
    }, 

    "m__api__mission__past__c2s": {
        "msg_id": 90002,
        "mission_id": int,
        "star": int,
    }, 

    "m__api__mission__reset__c2s": {
        "msg_id": 90003,
        "mission_id": int,
    }, 

    "m__api__mission__mission_award__c2s": {
        "msg_id": 90004,
        "mission_id": int,
        "award_type": int,
    }, 

    "m__api__mission__chapter_award__c2s": {
        "msg_id": 90005,
        "chapter_type": int,
        "chapter_id": int,
        "star": int,
    }, 

    "m__api__mission__hangup__c2s": {
        "msg_id": 90006,
        "mission_id": int,
        "htimes": int,
    }, 

    "m__api__talent__intensify__c2s": {
        "msg_id": 100001,
        "talent_id": int,
    }, 

    "m__api__talent__reset__c2s": {
        "msg_id": 100002,
    }, 

    "m__api__warship__intensify__c2s": {
        "msg_id": 110001,
        "ship_id": int,
        "to_level": int,
    }, 

    "m__api__warship__upgrade__c2s": {
        "msg_id": 110002,
        "ship_id": int,
    }, 

    "m__api__warship__weak__c2s": {
        "msg_id": 110003,
        "ship_id": int,
    }, 

    "m__api__warship__intensify_skill__c2s": {
        "msg_id": 110004,
        "ship_id": int,
        "skill_id": int,
    }, 

    "m__api__warship__set_position__c2s": {
        "msg_id": 110005,
        "team": "ignore",
    }, 

    "m__api__mall__pick__c2s": {
        "msg_id": 120001,
        "ptype": int,
    }, 

    "m__api__mall__info__c2s": {
        "msg_id": 120002,
        "mtype": int,
    }, 

    "m__api__mall__refresh__c2s": {
        "msg_id": 120003,
        "mtype": int,
    }, 

    "m__api__mall__buy__c2s": {
        "msg_id": 120004,
        "mtype": int,
        "item_tag": int,
    }, 

    "m__api__rank__get__c2s": {
        "msg_id": 130001,
        "rtype": int,
        "start": int,
        "stop": int,
    }, 

    "m__api__arena__info__c2s": {
        "msg_id": 140001,
    }, 

    "m__api__arena__admire__c2s": {
        "msg_id": 140002,
        "fighter_id": str,
    }, 

    "m__api__arena__fight__c2s": {
        "msg_id": 140003,
        "fighter_id": str,
        "fighter_rank": int,
        "result": int,
        "logs": "ignore",
        "fight": "ignore",
    }, 

    "m__api__arena__refresh__c2s": {
        "msg_id": 140004,
    }, 

    "m__api__arena__clean_cd__c2s": {
        "msg_id": 140005,
    }, 

    "m__api__arena__add_times__c2s": {
        "msg_id": 140006,
    }, 

    "m__api__arena__award__c2s": {
        "msg_id": 140007,
        "index": int,
    }, 

    "m__api__arena__daily_award__c2s": {
        "msg_id": 140008,
        "index": int,
    }, 

    "m__api__arena__history__c2s": {
        "msg_id": 140009,
    }, 

    "m__api__arena__replay__c2s": {
        "msg_id": 140010,
        "log_id": int,
    }, 

    "m__api__arena__fighter_data__c2s": {
        "msg_id": 140011,
        "fighter_id": str,
    }, 

    "m__api__trial__info__c2s": {
        "msg_id": 150001,
    }, 

    "m__api__trial__choose_fighter__c2s": {
        "msg_id": 150002,
        "fighter_id": str,
    }, 

    "m__api__trial__fight__c2s": {
        "msg_id": 150003,
        "fighter_id": str,
        "star": int,
        "my_states": "ignore",
        "fighter_states": "ignore",
        "fight": "ignore",
    }, 

    "m__api__trial__buy_buff__c2s": {
        "msg_id": 150004,
        "index": int,
        "buff_id": int,
        "hero_id": int,
    }, 

    "m__api__trial__open_box__c2s": {
        "msg_id": 150005,
    }, 

    "m__api__trial__skip__c2s": {
        "msg_id": 150006,
    }, 

    "m__api__trial__award__c2s": {
        "msg_id": 150007,
        "index": int,
    }, 

    "m__api__mail__info__c2s": {
        "msg_id": 160001,
    }, 

    "m__api__mail__read__c2s": {
        "msg_id": 160002,
        "mail_id": int,
    }, 

    "m__api__mail__get_attachments__c2s": {
        "msg_id": 160003,
        "mail_ids": "ignore",
    }, 

    "m__api__chat__info__c2s": {
        "msg_id": 170001,
        "ctype": int,
        "start": int,
        "end": int,
    }, 

    "m__api__chat__send__c2s": {
        "msg_id": 170002,
        "ctype": int,
        "msg": str,
        "receiver": str,
    }, 

    "m__api__task__submit__c2s": {
        "msg_id": 180001,
        "task_id": int,
    }, 

    "m__api__task__daily_submit__c2s": {
        "msg_id": 180002,
        "task_id": int,
    }, 

    "m__api__sign__sign__c2s": {
        "msg_id": 190001,
    }, 

    "m__api__sign__award__c2s": {
        "msg_id": 190002,
        "index": int,
    }, 

    "m__api__sign__resign__c2s": {
        "msg_id": 190003,
    }, 

    "m__api__act_mission__info__c2s": {
        "msg_id": 200001,
        "mtype": int,
    }, 

    "m__api__act_mission__enter__c2s": {
        "msg_id": 200002,
        "mission_id": int,
        "fight": "ignore",
    }, 

    "m__api__act_mission__past__c2s": {
        "msg_id": 200003,
        "mission_id": int,
        "hurt_percent": str,
        "hurt": int,
        "star": int,
    }, 

    "m__api__act_mission__award__c2s": {
        "msg_id": 200004,
        "mtype": int,
        "award_ids": "ignore",
    }, 

    "m__api__act_mission__hangup__c2s": {
        "msg_id": 200005,
        "mission_id": int,
        "htimes": int,
    }, 

    "m__api__activity__info__c2s": {
        "msg_id": 210001,
    }, 

    "m__api__activity__award__c2s": {
        "msg_id": 210002,
        "act_id": int,
        "index": int,
    }, 

    "m__api__activity__buy_level_fund__c2s": {
        "msg_id": 210003,
        "act_id": int,
    }, 

    "m__api__activity__info1__c2s": {
        "msg_id": 210004,
        "act_id": int,
    }, 

    "m__api__activity__gamble__c2s": {
        "msg_id": 210005,
        "act_id": int,
    }, 

    "m__api__activity__online_awards__c2s": {
        "msg_id": 210006,
    }, 

    "m__api__group__info__c2s": {
        "msg_id": 220001,
    }, 

    "m__api__group__info1__c2s": {
        "msg_id": 220002,
        "itype": int,
        "start": int,
        "end": int,
    }, 

    "m__api__group__create__c2s": {
        "msg_id": 220003,
        "name": str,
        "icon": int,
    }, 

    "m__api__group__search__c2s": {
        "msg_id": 220004,
        "key": str,
    }, 

    "m__api__group__quick_search__c2s": {
        "msg_id": 220005,
    }, 

    "m__api__group__update__c2s": {
        "msg_id": 220006,
        "items": "ignore",
    }, 

    "m__api__group__appoint__c2s": {
        "msg_id": 220007,
        "member_uid": str,
        "position": int,
    }, 

    "m__api__group__quit__c2s": {
        "msg_id": 220008,
    }, 

    "m__api__group__kick__c2s": {
        "msg_id": 220009,
        "member_uid": str,
    }, 

    "m__api__group__apply__c2s": {
        "msg_id": 220010,
        "group_id": int,
    }, 

    "m__api__group__review__c2s": {
        "msg_id": 220011,
        "request_id": int,
        "result": int,
    }, 

    "m__api__group__deny_all__c2s": {
        "msg_id": 220012,
    }, 

    "m__api__group__donate__c2s": {
        "msg_id": 220013,
        "target": int,
        "type": int,
    }, 

    "m__api__group__game_info__c2s": {
        "msg_id": 220014,
        "game_type": int,
    }, 

    "m__api__group__game_tiger__c2s": {
        "msg_id": 220015,
        "type": int,
    }, 

    "m__api__group__rank__c2s": {
        "msg_id": 220016,
        "type": int,
        "start": int,
        "end": int,
    }, 

    "m__api__group__game_bird__c2s": {
        "msg_id": 220017,
        "type": int,
        "process": int,
    }, 

    "m__api__gtrain__info__c2s": {
        "msg_id": 220018,
    }, 

    "m__api__gtrain__unlock__c2s": {
        "msg_id": 220019,
        "slot": int,
    }, 

    "m__api__gtrain__fill__c2s": {
        "msg_id": 220020,
        "hero_id": int,
        "slot": int,
    }, 

    "m__api__gtrain__group_train_info__c2s": {
        "msg_id": 220021,
    }, 

    "m__api__gtrain__members_train__c2s": {
        "msg_id": 220022,
        "uid": str,
    }, 

    "m__api__gtrain__help__c2s": {
        "msg_id": 220023,
        "uid": str,
        "hero_id": int,
    }, 

    "m__api__vip__charge__c2s": {
        "msg_id": 230001,
        "index": int,
    }, 

    "m__api__vip__buy__c2s": {
        "msg_id": 230002,
        "index": int,
    }, 

    "m__api__vip__refresh_pay__c2s": {
        "msg_id": 230003,
    }, 

    "m__api__vip__info__c2s": {
        "msg_id": 230004,
    }, 

    "m__api__worldboss__info__c2s": {
        "msg_id": 240001,
    }, 

    "m__api__worldboss__rank__c2s": {
        "msg_id": 240002,
        "rtype": int,
        "start": int,
        "end": int,
    }, 

    "m__api__worldboss__enter__c2s": {
        "msg_id": 240003,
        "fight": "ignore",
    }, 

    "m__api__worldboss__fight__c2s": {
        "msg_id": 240004,
        "dmg": int,
    }, 

    "m__api__worldboss__encourage__c2s": {
        "msg_id": 240005,
    }, 

    "m__api__worldboss__cleancd__c2s": {
        "msg_id": 240006,
    }, 

    "m__api__worldboss__support__c2s": {
        "msg_id": 240007,
        "uid": str,
    }, 

}