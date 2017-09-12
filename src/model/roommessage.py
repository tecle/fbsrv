# coding:utf-8
import json

from model.response.coredata import DataShell

from model.response.livedata import LiveBizData

json_separators = (',', ":")


class JsonRespStr(object):
    Type = 'Type'
    RequestId = 'ReqId'
    Data = 'Data'


class HttpResponseType(object):
    GiftResponse = 1
    GameSnapshot = 2
    HeartBeat = 3
    StartGameResponse = 4
    SimpleResponse = 5


msg_SimpleResponse = 1
msg_GameStatusTrans = 2
msg_GameBetStatusTick = 3
msg_GameResultStatusTick = 4
msg_GameCommonStatusTick = 5
msg_BetResponse = 6
msg_GameSnapshot = 7
msg_HostEndLiving = 8
msg_SendGiftResponse = 9
msg_GameStart = 10
msg_GameStop = 11
msg_LiveStart = 12


def make_message(msg_type, msg_data, err_code=0):
    return json.dumps({
        "t": msg_type,
        "data": msg_data,
        "code": err_code
    }, separators=(',', ":"))


def make_send_gift_response(req_id, is_success, t, gold=0, charm=0):
    lbd = LiveBizData()
    lbd.reqId = req_id
    lbd.data_type = t
    lbd.gold = gold
    lbd.charm = charm
    lbd.success = is_success
    lbd.err_code = 0 if is_success else 201
    return lbd.SerializeToString()


def format_game_snapshot(game_id, req_id, game_type, st_id, st_cost, second, user_bet, slot_bet, t, game_result=None):
    ds = DataShell()
    ds.data = {
        JsonRespStr.Type: t,
        JsonRespStr.RequestId: req_id,
        JsonRespStr.Data: {
            "code": 200,
            "gType": game_type,
            "gId": game_id,
            "st": st_id,
            "dt": st_cost,
            "sec": second,
            "uBet": user_bet,
            "sBet": slot_bet,
            "attach": game_result
        }
    }
    return ds.SerializeToString()


def format_heartbeat_response(success, t):
    lbd = LiveBizData()
    lbd.success = success
    lbd.err_code = 0 if success else 501
    lbd.data_type = t
    return lbd.SerializeToString()


def format_close_live_response(success, t):
    lbd = LiveBizData()
    lbd.success = success
    lbd.err_code = 0 if success else 501
    lbd.data_type = t
    return lbd.SerializeToString()


def format_start_game_response(req_id, t, game_id):
    ds = DataShell()
    ds.data = {
        JsonRespStr.RequestId: req_id,
        JsonRespStr.Type: t,
        JsonRespStr.Data: {
            "code": 200,
            "gId": game_id,
            "gType": 0,
            "st": 0,
            "sec": 0,
            "uBet": [],
            "sBet": [],
            "attach": None
        }
    }
    return ds.SerializeToString()


def format_simple_response(req_id, response_type, err_code=None):
    ds = DataShell()
    if err_code:
        ds.success = False
        ds.errCode = err_code
    ds.data = {
        JsonRespStr.RequestId: req_id,
        JsonRespStr.Type: response_type,
        JsonRespStr.Data: {
            "code": 200,
            "gId": '',
            "gType": 0,
            "st": 0,
            "sec": 0,
            "uBet": [],
            "sBet": [],
            "attach": None
        }
    }
    return ds.SerializeToString()


'''Below is function for broadcasting msg to chatroom'''
GameMsgKeyStr = 't'
GameMsgValueStr = 'V'
GameUserStr = 'U'
GameUserFortuneStr = 'UF'
GameStFromStr = 'F'
GameStToStr = 'T'
GameStNowStr = 'N'
GameStProgressStr = 'P'
GameStDurationStr = 'DT'
GameStAttachStr = 'AT'
GameWinnerStr = 'WN'
GameWinnerRateStr = 'RT'
GameResultDetailStr = 'RE'
GameBetListStr = 'BL'
GameRawStr = "RS"
GameTypeStr = "T"
UserBetInfoStr = 'UB'
TotalBetInfoStr = 'TB'


def parse_game_result_to_dict(game_type, game_result, pumping_out):
    '''
    :param game_result: card_game_base.CommonGameResult
    :return: dict of this game result
    '''
    if not game_result:
        return None
    # 解析游戏结果
    return {
        GameWinnerStr: game_result.winner_index,
        GameWinnerRateStr: pumping_out,
        GameResultDetailStr: {
            GameRawStr: json.dumps(game_result.detail),
            GameTypeStr: game_type
        }
    }


def format_broadcast_msg():
    raise DeprecationWarning('This method is not used anymore.')


def format_game_status_trans(pre_st, cur_st, duration, game_result=None):
    return _format_game_broadcast_msg_item(msg_GameStatusTrans, {
        GameStFromStr: pre_st,  # from
        GameStToStr: cur_st,  # to
        GameStDurationStr: duration,  # duration
        GameStAttachStr: game_result  # attach
    })


def format_game_bet_info(tag, duration, progress, bet_list):
    '''
    :param bet_list:[slot0_bet_num, slot1_bet_num, ...]
    '''
    return _format_game_broadcast_msg_item(msg_GameBetStatusTick, {
        GameBetListStr: bet_list,
        GameStProgressStr: progress,
        GameStDurationStr: duration,
        GameStNowStr: tag

    })


def format_game_status_info(st_tag, duration, progress):
    return _format_game_broadcast_msg_item(msg_GameCommonStatusTick, {
        GameStProgressStr: progress,
        GameStDurationStr: duration,
        GameStNowStr: st_tag
    })


def format_game_result_info(tag, duration, progress, result):
    return _format_game_broadcast_msg_item(msg_GameResultStatusTick, {
        GameStProgressStr: progress,
        GameStDurationStr: duration,
        GameStNowStr: tag,
        GameStAttachStr: result
    })


def make_snapshot_data(game_type, st_id, st_cost, second, user_bet, slot_bet, game_result=None):
    return {
        GameTypeStr: game_type,
        GameStNowStr: st_id,
        GameStDurationStr: st_cost,
        GameStProgressStr: second,
        UserBetInfoStr: user_bet,
        TotalBetInfoStr: slot_bet,
        GameStAttachStr: game_result
    }


def format_snapshot(game_type, st_id, st_cost, second, user_bet, slot_bet, game_result=None, err_code=0):
    return _format_game_broadcast_msg_item(msg_GameSnapshot, {
        GameTypeStr: game_type,
        GameStNowStr: st_id,
        GameStDurationStr: st_cost,
        GameStProgressStr: second,
        UserBetInfoStr: user_bet,
        TotalBetInfoStr: slot_bet,
        GameStAttachStr: game_result
    }, err_code)


def format_err_response(msg_type, err_code):
    return json.dumps({
        "t": msg_type,
        "data": None,
        "code": err_code
    }, separators=json_separators)


def _format_game_broadcast_msg_item(msg_type, msg_data, err_code=0):
    return json.dumps({
        "t": msg_type,
        "data": msg_data,
        "code": err_code
    }, separators=json_separators)
