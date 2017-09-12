# coding: utf-8


import handlers.active_handler as ActiveHandlers
import handlers.common_handler as CommonHandlers
import handlers.game_handler as game_handler
import handlers.live_handler as live_handler
import handlers.login_handler as LoginHandlers
import handlers.user_info_handler as UserInfoHandelers

check_token_dict = {'need_token': True}
uncheck_token_dict = {'need_token': False}

ROUTING_TABLE = [
    (r"/login/sendsms$", LoginHandlers.SendRegisterVerifyCodeHandler, uncheck_token_dict),
    (r"/login/sendpwsms$", LoginHandlers.SendResetPwVerifyCodeHandler, uncheck_token_dict),
    (r"/login/checkcode", LoginHandlers.ValidateSMSCode, uncheck_token_dict),
    (r"/login/register", LoginHandlers.RegisterUser, uncheck_token_dict),
    (r"/login/update", UserInfoHandelers.ModifyUser, check_token_dict),
    (r"/login/gethobby", CommonHandlers.GetHobby, check_token_dict),
    (r"/login/gethobbies", CommonHandlers.GetAllHobbiesHandle, check_token_dict),
    (r"/login/savehobby", UserInfoHandelers.SelectHobby, check_token_dict),
    (r"/login/login", LoginHandlers.UserLoginHandler, uncheck_token_dict),
    (r"/login/logout", LoginHandlers.UserOfflineHandler, check_token_dict),
    (r"/login/wx", LoginHandlers.WeChatUserLoginHandler, uncheck_token_dict),
    (r"/login/resetpw", UserInfoHandelers.ResetPasswordHandler, uncheck_token_dict),

    (r"/login/ver", CommonHandlers.GetAppVersionInfoHandler, uncheck_token_dict),

    (r"/ground/topic/get", ActiveHandlers.GetTopicsHandler, uncheck_token_dict),
    (r"/ground/active/add", ActiveHandlers.CreateActiveHandler, check_token_dict),
    (r"/ground/active/get", ActiveHandlers.GetActivesHandler, uncheck_token_dict),
    (r"/ground/active/delete", ActiveHandlers.DeleteActiveHandler, check_token_dict),
    (r"/ground/active/like", ActiveHandlers.LikeActiveHandler, check_token_dict),
    (r"/ground/active/refresh", ActiveHandlers.GetActiveMutableData, check_token_dict),
    (r"/ground/active/nearby", ActiveHandlers.GetActivesNearbyEpHandler, uncheck_token_dict),

    (r"/ground/active/comment/add", ActiveHandlers.AddCommentHandler, check_token_dict),
    (r"/ground/active/comment/delete", ActiveHandlers.DeleteCommentHandler, check_token_dict),
    (r"/ground/active/comment/get", ActiveHandlers.GetActiveCommentsHandler, check_token_dict),

    (r"/token/pic/upload", CommonHandlers.Get7CowUploadCertificate, check_token_dict),
    (r"/token/pic/download", CommonHandlers.Get7CowDownloadCertificate, check_token_dict),

    (r"/contactus/report", CommonHandlers.ReportHandler, check_token_dict),
    (r"/contactus/feedback", CommonHandlers.SuggestionHandler, check_token_dict),

    (r"/user/getsome", UserInfoHandelers.GetUserInfoHandler, uncheck_token_dict),
    (r"/user/detail", UserInfoHandelers.GetUserDetailHandler, uncheck_token_dict),
    (r"/user/details", UserInfoHandelers.GetUsersDetailHandler, uncheck_token_dict),
    (r"/user/visitors", UserInfoHandelers.GetUserVisitorsHandler, check_token_dict),
    (r"/user/sites", UserInfoHandelers.GetUserLocationHandler, check_token_dict),
    (r"/user/gold", UserInfoHandelers.GetUserGoldHandler, check_token_dict),

    (r"/discovery/users", CommonHandlers.GetRecommendUsersHandler, uncheck_token_dict),

    (r'/heartbeat/report', CommonHandlers.ReportHeartbeatHandler, check_token_dict),
]

import handlers.operation_handler as OpHandlers
import handlers.wshandler as ExpHandler

LIVE_TABLE = [
    (r'/live/create', live_handler.CreateLiveHandler, check_token_dict),
    (r'/live/resetpush', live_handler.ResetLivePushAddrHandler, check_token_dict),
    (r'/live/list', live_handler.GetLiveListHandler, uncheck_token_dict),
    # (r'/live/rank', live_handler.LiveFunctionalHandler, check_token_dict),
    (r'/live/detail', live_handler.GetLiveDetailHandler, check_token_dict),
    (r'/live/play', game_handler.GameCtrlHandler, check_token_dict),
    (r'/live/games', game_handler.GetGameListHandler, check_token_dict),
    (r'/live/rank', live_handler.RankHandler, check_token_dict),
    (r'/sock/live', ExpHandler.HostHandler),
    (r'/sock/watch', ExpHandler.WatcherHandler)
]

OP_TABLE = [
    (r"/op/hobby/add", OpHandlers.AddHobbyPageHandler),
    (r"/op/hobby/query", OpHandlers.ShowHobbiesHandler),
    (r"/op/topic/add", OpHandlers.AddTopicHandler),
    (r"/op/topic/update", OpHandlers.UpdateTopicHandler),
    (r"/op/topic/query", OpHandlers.QueryTopicHandler),
    (r"/op/switch/redis", OpHandlers.SwitchRedisHandler),
    (r"/op/appver/set", OpHandlers.ChangeVersionHandler),
    (r"/op/appver/get", OpHandlers.GetVersionHandler),
    (r"/op/user/control", OpHandlers.UserOperationHandler)
]

import pay.pay_handlers as pay_handlers

PAY_TABLE = [
    (r'/pay/cb/wx', pay_handlers.WeinXinCallbackHandler),
    (r'/pay/cb/zfb', pay_handlers.AliPayCallbackHandler),
    (r'/pay/q', pay_handlers.OrderQueryHandler, check_token_dict),
    (r'/pay/do', pay_handlers.PayHandler, check_token_dict),
    (r'/pay/his', pay_handlers.OrdersHandler, check_token_dict),
    (r'/pay/cargo', CommonHandlers.GetCargoConfHandler, check_token_dict)
]

import handlers.db_handler as db_handler

DB_TABLE = [
    (r'/db/user/addhobby', db_handler.UpdateUserHobbyToDBHandler),
    (r'/db/user/detail', db_handler.GetUserDetailFromDBHandler),
    (r'/db/user/getsome', db_handler.GetUserInfoFromDBHandler),
    (r'/db/user/recommend', db_handler.GetRecommendUserFromDBHandler),
    (r'/db/user/avatar', db_handler.GetUsersAvatarHandler),
    (r'/db/hello', db_handler.HelloServiceHandler),
    (r'/db/wx/new', db_handler.CreateUserByWxHandler),
    (r'/db/wx/login', db_handler.LoginByWxHandler),
    (r'/db/wx/update', db_handler.UpdateTokenByWxHandler)
]
