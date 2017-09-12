# coding: utf-8

CHANNEL_GAME_MSG = 'GAME_CHANNEL'


GAME_NOTIFY_MSG_ROUTING_KEY = "Notify"
GAME_OVER_MSG_ROUTING_KEY = "GameOver"
ROOM_CLOSE_MSG_ROUTING_KEY = "RoomClose"
STOP_GAME_MSG_ROUTING_KEY = "GameClose"
START_GAME_MSG_ROUTING_KEY = "GameStart"
START_LIVE_MSG_ROUTING_KEY = "StartLive"
STOP_LIVE_MSG_ROUTING_KEY = "StopLive"

MSG_ROOM_ID_KEY = 'id'
MSG_ROOM_DATA_KEY = 'msg'

REQ_FOR_BET = 1
REQ_FOR_SEND_GIFT = 2


def make_publish_data(routing_key, msg_body):
    return {
        'key': routing_key,
        'data': msg_body
    }


