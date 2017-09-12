# coding: utf-8

class RedisStr:
    '''
    suffix: Field(域名),ZKey(有序集合), HKey(哈希表), Key(普通键值对), SKey(集合), GKey(地理位置), LKey(跳跃表)
    也可以是suffixPtn的模式
    '''
    AppVersionHKey = "APP:V"
    AppCurVerCodeField = "VC"
    AppCurVerNameField = "VN"
    AppMinVerCodeNeedField = "MV"
    AppDownloadUrlField = "DL"
    AppCurVerIntroduceField = "VI"

    TopicListHkey = "TPS"

    HobbySKey = "hobby"  # Hbs
    HostsSKey = "HTS"

    SMSHKeyPtn = 'V:%s'
    SMSCodeField = 'Cd'
    SMSStatusField = 'St'
    SMSIdFiled = 'Id'

    TopicHKeyPattern = "T:%s"
    TopicViewNumField = "VN"
    TopicActiveNumField = "AN"

    ActiveHKeyPtn = 'A:%s'
    ActiveLikedUserSKeyPtn = 'A:Lk:%s'
    ActivesLocationGKey = "Ge:A"
    ActiveTmpUserInLocSet = '0'

    ActiveViewNumZKey = 'A:VN'
    ActiveLikeNumZKey = 'A:LN'
    ActiveCommentNumZKey = 'A:CN'
    ActivePushFlagKeyPtn = 'LP:%s:%s'
    FreshActiveIdLKeyPtn = 'a:new:%s'  # A:nNw:%s

    UserHKeyPtn = "usr:%s"  # U:%s
    UserInfoCacheHKeyPtn = "UC:%s"

    UsersLocationGKey = "Ge:U"

    UserLastHeartBeatField = "LH"
    UserCurrentStatusField = 'St'
    UserCreditField = "R:Cd"
    UserLastLoginField = "Lg:Lt"
    UserLoginDaysField = "Lg:D"
    UserLoginRewardField = "Lg:Rd"
    UserLoginTypeField = 'LgT'
    UserLoginDeviceField = 'Dvc'
    UserAvatarField = 'At'  # 保存的是实际的头像地址
    UserShowPicsField = 'SP'  # 保存的是实际地址
    UserLocationField = 'Loc'
    UserVipLevelField = 'VL'
    UserRechargeField = 'VL:C'
    UserRechargePointField = 'VL:P'
    UserNickNameField = 'NN'
    UserBornDateField = 'BD'
    UserGenderField = 'Gen'
    UserHobbiesField = 'Hbs'
    UserLatitudeField = 'Lat'
    UserLongitudeField = 'Lon'
    UserSignField = 'Sn'
    UserOnlineTimeFieldPtn = 'OT'
    UserIsAnchorField = 'IA'
    YunxinTokenField = 'YX:Tk'
    UserTokenValueField = "Tk:V"
    UserTokenMachineField = "Tk:M"  # 此token绑定的哪台手机

    UserCharmZKey = 'Rk:Cm'
    UserTotalFortuneZKey = 'Rk:Ft'

    UserHeartbeatHKeyPtn = 'Hb:%s'
    UserCurrentPanelField = 'P'
    UserPanelDataField = 'D'

    RecentVisitorsZKeyPtn = 'Vs:%s'
    RequestIdKeyPtn = 'Rq:%s'
    TopicParticipantsZKeyPtn = 'TP:%s'

    LivingListSKey = 'Lving'

    LiveHKeyPtn = 'Lv:%s'
    LiveOwnerField = 'Onr'
    LiveCurrentViewNumField = 'CVN'
    LiveTotalViewNumField = 'TVN'
    LivePushUrlField = 'Ps'
    LiveHttpPullUrlField = 'Pl:0'
    LiveHlsPullUrlField = 'Pl:1'
    LiveRtmpPullUrlField = 'Pl:2'
    LiveExpireTime = 'L:ET'
    LiveChannelIdField = 'CI'
    LiveCoverField = 'Cv'
    LiveLocationField = 'Loc'
    LiveOrderNumberField = 'ON'
    RoomGameTypeField = 'GT'
    LiveTitleField = 'Tt'
    LiveUpdateTimeField = 'UT'
    LiveChatRoomField = 'CR'
    LiveGameStorageField = 'GS'
    LiveHeartBeatField = 'HB'
    LiveFortuneEarnedField = 'FE'
    LiveTotalTimeField = 'LT'
    LiveGiftReceived = 'GN'
    LiveGameStorageFieldPtn = 'GS:%s'
    RoomIsLivingField = 'CSt'

    LiveGuardersSKeyPtn = 'Gd:%s'
    LiveFansSKeyPtn = 'Fs:%s'
    LiveGiftNumZKey = 'Lv:Gf'
    LiveViewNumZKey = 'Lv:Vw'
    LiveSpecialZKeyPtn = 'Lv:S:%s'

    LiveGiftRequestKeyPtn = 'L:%s:%s'

    ServerStatisticsHKey = 'S:Srv'
    GameTotalTaxField = "GT:A"
    GameTaxFieldPtn = "GT:%s"
    GameTotalDailyLiveField = "GD:A"
    GameDailyLiveFieldPtn = "GD:%s"

    ConfigChannel = "CONFIG_CHANNEL"

    AppConfigHKey = "App.Cfg"
    AppCargoConfField = "cargo"
    AppVersionConfField = "ver"
    AppBannerConfField = "banner"

    DailyRankingZKeyPtn = 'DR:%s'
    TotalRankingZKeyPtn = 'TR:%s'
