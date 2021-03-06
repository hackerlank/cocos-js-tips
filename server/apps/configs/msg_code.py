#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   前后端通信代号制定规则：
#       1. 1打头的code全是各模块共用的错误code，类如前端传递来的参数为空等等。
#       2. 每个模块使用100+的代号为操作成功code，其余全是错误code。
#       eg:
#              操作是否成功，0-失败，1-成功
#                  |
#                40100 - 最后两位错误码序列号，自增
#                |
#            功能模块代号
# @end
# @copyright (C) 2015, kimech

MsgCode = {
    'Success': 100,

    'Forbidden': 403,
    'UriNotExist': 404,
    'GameConfigNotExist': 405,
    'ServerInternalError': 500,

    'ParamError': 10000,
    'ParamIllegal': 10001,
    'HandleRequestError': 10002,
    'InvalidOperation': 10003,
    'GoldNotEnough': 10004,
    'DiamondNotEnough': 10005,
    'WithoutUserCookie': 10006,
    'ApiNotOpen': 10007,
    'CookieAuthFailed': 10008,
    'PowerNotEnough': 10009,

    'AccountBindSucc': 20101,
    'AccountAuthParamError': 20000,
    'AccountAuthFail': 20001,
    'PlatformNotExist': 20002,
    'AccountPasswordError': 20003,
    'AccountAlreadyExist': 20004,
    'AccountRegistParamsError': 20005,
    'AccountBindFail': 20006,
    'AccountBindRepeat': 20007,

    'GameLoginSucc': 30100,
    'GameLoginFail': 30001,
    'ServerAuthParamError': 30002,
    'ServerNotOpen': 30003,
    'ServerNotExist': 30004,
    'GameLoginByOthers': 30005,
    'ServerUpdateing': 30006,
    'ServerSessionExpired': 30007,

    'UserChangeNameSucc': 40100,
    'UserAddValueSucc': 40101,
    'UserUpdateAvatarSucc': 40102,
    'UserUpdateSignSucc': 40103,
    'UserBuyEnergySucc': 40104,
    'UserBuySkillPointSucc': 40105,
    'UserSkipGuideSucc': 40106,

    'UserAuthFail': 40000,
    'UserTokenExpired': 40001,
    'UserNameRepeated': 40002,
    'UserNameIllegal': 40003,
    'UserNameTooLong': 40004,
    'UserSignIllegal': 40005,
    'UserSignTooLong': 40006,
    'UserTimesUseUp': 40007,
    'UserGetDataFailed': 40008,
    'UserFrozen': 40009,
    'UserLevelTooLow': 40010,
    'UserHasNoGroup': 40011,
    'UserVipTooLow': 40012,
    'UserNotExist': 40013,
    'UserModuleNotOpen': 40014,
    'UserFightCheckFailed': 40015,

    'HeroIntensifySucc': 50100,
    'HeroUpgradeSucc': 50101,
    'HeroWeakSucc': 50102,
    'HeroSynthesisSucc': 50103,
    'HeroExchangeChipSucc': 50104,
    'HeroFeedSucc': 50105,
    'HeroFavorMarrySucc': 50106,
    'HeroFavorDivorceSucc': 50107,
    'HeroNotExist': 50000,
    'HeroUpLevelFail': 50001,
    'HeroMaxQuality': 50002,
    'HeroQualityLvLimit': 50003,
    'HeroMaxStar': 50004,
    'HeroAlreadyExist': 50005,
    'HeroUserLevelLimit': 50006,
    'HeroFavorAlreadyMax': 50007,
    'HeroMarryFavorNotEnough': 50008,
    'HeroAlreadyMarried': 50009,
    'HeroFavorNoMarried': 50010,
    'HeroFoodTypeError': 50011,

    'MissionEnterSucc': 60100,
    'MissionResetSucc': 60101,
    'MissionAwardSucc': 60102,
    'MissionHangupSucc': 60103,
    'MissionTooMany': 60001,
    'MissionNotExist': 60002,
    'MissionCondsNotEnough': 60003,
    'MissionTimesError': 60004,
    'MissionNotIn': 60005,
    'MissionIllegal': 60006,
    'MissionTimesExist': 60007,
    'MissionResetTimesEmpty': 60008,
    'MissionNoPass': 60009,
    'MissionFirstAwarded': 60010,
    'MissionBestAwarded': 60011,
    'MissionChapterNull': 60012,
    'MissionStarNotEnough': 60013,
    'MissionChapterAwarded': 60014,
    'MissionEnergyNotEnough': 60015,
    'MissionNotOpen': 60016,
    'MissionAwardNotSatisfied': 60017,
    'MissionAwardNotExist': 60018,
    'MissionAlreadyAwarded': 60019,
    'MissionInCD': 60020,
    'MissionStarNotEnough': 60021,

    'EquipIntensifySucc': 70100,
    'EquipUpgradeSucc': 70101,
    'EquipWeakSucc': 70102,
    'EquipAntiWeakSucc': 70103,
    'EquipNotExist': 70000,
    'EquipLvOverLimit': 70001,
    'EquipQualityLevelLimit': 70002,

    'SkillLevelUpSucc': 80100,
    'SkillNotWeaken': 80001,
    'SkillLevelMax': 80002,
    'SkillLevelFull': 80003,
    'SkillPointNotEnough': 80004,

    'PackageItemUseSucc': 90100,
    'PackageItemSaleSucc': 90101,
    'PackageExpressBuySucc': 90102,
    'PackageItemNotExist': 90000,
    'PackageItemNotEnough': 90001,
    'PackageItemUseFail': 90002,
    'PackageIsFull': 90003,
    'PackageItemNotAvailable': 90004,
    'PackageItemNotSold': 90005,

    'SpiritLevelUpSucc': 100100,
    'SpiritNotWeaken': 100001,
    'SpiritLevelMax': 100002,

    'ArraySetPositionSucc': 110100,
    'ArrayCantEmpty': 110001,
    'ArrayHeroTypeError': 110002,
    'ArrayCantRepeat': 110003,

    'TalentIntensifySucc': 120100,
    'TalentResetSucc': 120101,
    'TalentNotExist': 120001,
    'TalentUserLevelLimit': 120002,
    'TalentFrontNotSatisfied': 120003,
    'TalentMaxLevel': 120004,
    'TalentCondsNotEnough': 120005,

    'WarshipIntensifySucc': 130101,
    'WarshipUpgradeSucc': 130102,
    'WarshipWeakSucc': 130103,
    'WarshipSkillIntensifySucc': 130104,
    'WarshipSetPositionSucc': 130105,
    'WarshipNotExist': 130001,
    'WarshipLevelOverLimit': 130002,
    'WarshipQualityMax': 130003,
    'WarshipLimitsNotEnough': 130004,
    'WarshipStarMax': 130005,
    'WarshipSkillUnlock': 130006,
    'WarshipSkillLevelMax': 130007,

    'MallBuySucc': 140101,
    'MallItemSaleOut': 140001,
    'MallMysteryExpired': 140002,

    'ArenaAdmireSucc': 150101,
    'ArenaStartFightSucc': 150102,
    'ArenaCleanCDSucc': 150103,
    'ArenaAddTimesSucc': 150104,
    'ArenaGetAwardSucc': 150105,

    'ArenaAlreadyAdmired': 150001,
    'ArenaFightCD': 150002,
    'ArenaFightTimesUseUp': 150003,
    'ArenaFighterRankChanged': 150004,
    'ArenaRefreshTimesUseUp': 150005,
    'ArenaNotInCD': 150006,
    'ArenaAddTimesUseUp': 150007,
    'ArenaRankTooLow': 150008,
    'ArenaAwarded': 150009,
    'ArenaScoreNotEnough': 150010,
    'ArenaChallengeTimesExist': 150011,
    'ArenaFighterNotInList': 150012,
    'ArenaFighterNotAdmiredList': 150013,

    'TrialChoseFighterSucc': 160101,
    'TrialGetAwardSucc': 160102,
    'TrialFightSucc': 160103,
    'TrialBuyBuffSucc': 160104,

    'TrialWrongType': 160001,
    'TrialFighterNotExist': 160002,
    'TrialFighterChosen': 160003,
    'TrialFighterNotInList': 160004,
    'TrialBuffNotInList': 160005,
    'TrialStarsNotEnough': 160006,
    'TrialHeroCantUseBuff': 160007,
    'TrialProcessMax': 160008,
    'TrialCantSkip': 160009,
    'TrialGetAwardWrong': 160010,
    'TrialScoresTooLow': 160011,
    'TrialAwarded': 160012,
    'TrialFighterWrong': 160013,
    'TrialBuffAlreadyBuy': 160014,

    'MailReadSucc': 170101,
    'MailGetAttachmentsSucc': 170102,

    'MailNotExist': 170001,
    'MailAlreadyRead': 170002,
    'MailAlreadyGot': 170003,

    'ChatSendMsgSucc': 180101,
    'ChatPrivateTargetEmpty': 180001,
    'ChatCantToSelf': 180002,

    'TaskSubmitSucc': 190101,

    'TaskNotExist': 190001,
    'TaskAlreadySubmit': 190002,
    'TaskCantSubmit': 190003,

    'SignSucc': 200101,
    'SignAwardSucc': 200102,
    'SignAlreadyToday': 200001,
    'SignAlreadyAwarded': 200002,
    'SignDaysNotEnough': 200003,
    'SignNotToday': 200004,
    'SignCantResignToday': 200005,

    'CDKeyNotExist': 210001,
    'CDKeyNotEffective': 210002,
    'CDKeyCantRepeat': 210003,
    'CDKeyAlreadyUsedByOther': 210004,

    'ActAwardSucc': 220101,
    'ActBuyLevelFundSucc': 220102,

    'ActNotExist': 220001,
    'ActAlreadyAwarded': 220002,
    'ActAwardNotSatisfied': 220003,
    'ActAwardFail': 220004,
    'ActAlreadyFinish': 220005,
    'ActAwardEmpty': 220006,
    'ActLevelFundAlreadyActive': 220007,
    'ActGambleTimesUseUp': 220008,

    'GroupCreateSucc': 230101,
    'GroupUpdateSucc': 230102,
    'GroupAppointSucc': 230103,
    'GroupApplySucc': 230104,
    'GroupKickSucc': 230105,
    'GroupReviewSucc': 230106,
    'GroupHandleSucc': 230107,
    'GroupDonateSucc': 230108,
    'GroupQuitSucc': 230109,
    'GroupGameTigerSucc': 230110,
    'GroupGameBirdSucc': 230111,

    'GroupHaveNoGroup': 230001,
    'GroupNotExist': 230002,
    'GroupNameRepeated': 230003,
    'GroupHaveNoAuth': 230004,
    'GroupMemberNotExist': 230005,
    'GroupMemberAlreayInPosition': 230006,
    'GroupPositionFull': 230007,
    'GroupMasterCantQuit': 230008,
    'GroupAlreadyInGroup': 230009,
    'GroupInCD': 230010,
    'GroupLevelTooLow': 230011,
    'GroupCantJoin': 230012,
    'GroupFull': 230013,
    'GroupAlreadyApplied': 230014,
    'GroupRequestNotExist': 230015,
    'GroupUserHasGroup': 230016,
    'GroupUserDataNotExist': 230017,
    'GroupDonateTimesUseUp': 230018,
    'GroupDailyExpMax': 230019,
    'GroupCantAppointSelf': 230020,
    'GroupCantKickSelf': 230021,
    'GroupGameTigerTimesUseUp': 230022,
    'GroupGameTigerAlreayIn': 230023,
    'GroupGameTigerNotIn': 230024,
    'GroupGameTigerFull': 230025,
    'GroupGameBirdTimesUseUp': 230026,

    'GroupTrainSlotUnlockSucc': 230112,
    'GroupTrainFillSucc': 230113,
    'GroupTrainHelpOtherSucc': 230114,
    'GroupTrainSlotUnlocked': 230027,
    'GroupTrainSlotLocked': 230028,
    'GroupTrainHeroNotOn': 230029,
    'GroupTrainTimesMax': 230030,
    'GroupTrainHisTimesMax': 230031,

    'VipGiftBuySuccess': 240101,
    'VipChargeIndexNotExist': 240001,
    'VipChargeFailed': 240002,
    'VipGiftAlreadyBought': 240003,
    'VipGiftNotExist': 240004,
    'VipChargeTmpAccountCantCharge': 240005,

    'ApplePayCheckSuccess': 250101,
    'ApplePayCheckParamsError': 250001,
    'ApplePayCheckHttpRequestError': 250002,
    'ApplePayCheckHttpRequestFailed': 250003,
    'ApplePayCheckServerHandleFailed': 250004,

    'BossEnterSucc': 260101,
    'BossFightSucc': 260102,
    'BossEncourageSucc': 260103,
    'BossCleanCDSucc': 260104,
    'BossSupportSucc': 260105,

    'BossInCD': 260001,
    'BossNotStart': 260002,
    'BossEnd': 260003,
    'BossEncourageFailed': 260004,
    'BossCleanCDFailed': 260005,
    'BossSupportEnd': 260006,
    'BossSupportRepeated': 260007,
    'BossSupportFailed': 260008,
}
