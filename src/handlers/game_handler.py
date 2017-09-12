# coding: utf-8

from handlers.base_handler import KVBaseHandler
from model.cache import LiveCache
from model.response.coredata import DataShell
from model.response.livedata import LiveGames
from utils.common_define import ErrorCode
from utils.common_define import HttpErrorStatus
from utils.repoze.lru import LRUCache


class GameCtrlHandler(KVBaseHandler):
    # 由于游戏进程是单进程, 因此直接把缓存放在本地, 不使用redis
    cache = LRUCache(500)

    def post(self):
        if not self.check_request():
            return
        op = self.get_argument('op')
        live_id = int(self.get_argument('lid'))
        # todo: remove req_id in message, this req_id is not necessary.
        req_id = '0'
        game_manager = self.application.game_manager
        if op == 'S':
            # 开启游戏, todo: 非主播不可以开启游戏
            game_type = int(self.get_argument('gType'))
            chat_room = int(self.get_argument('room'))
            if game_manager.validate_game(game_type):
                resp = game_manager.start_game(live_id, chat_room, game_type, req_id, 'S')
            else:
                ds = DataShell()
                ds.success = False
                ds.code = ErrorCode.GameFrozen
                resp = ds.SerializeToString()
        elif op == 'B':
            resp = self.ensure_live(live_id)
            if not resp:
                # 下注
                uid = int(self.get_argument('uid'))
                bet_detail = self.get_argument('bet')
                resp = game_manager.add_bet(live_id, uid, bet_detail, req_id, 'B')
        elif op == 'P':
            resp = self.ensure_live(live_id)
            if not resp:
                uid = int(self.get_argument('uid'))
                # 直播间快照
                resp = game_manager.get_game_snapshot(live_id, uid, req_id, 'P')
        else:
            self.set_status(*HttpErrorStatus.WrongParams)
            resp = '{}'
        self.write(resp)

    def ensure_live(self, live_id):
        if not self.application.get_cache(LiveCache.cache_name).is_user_living(live_id):
            ds = DataShell()
            ds.success = False
            ds.errCode = ErrorCode.LiveAlreadyClosed
            return ds.SerializeToString()
        return None


class GetGameListHandler(KVBaseHandler):
    LastInfo = [None, None]  # [版本号, 缓存回复串]

    def do_post(self, *args):
        ver = int(self.get_argument('ver'))
        game_cfg = self.application.game_conf
        cur_ver = game_cfg.version
        if ver == cur_ver:
            lg = LiveGames()
            lg.ver = ver
            self.write(lg.SerializeToString())
        elif self.LastInfo[0] == cur_ver:
            self.write(self.LastInfo[1])
        else:
            lg = LiveGames()
            lg.ver = cur_ver
            lg.games = [g.type for g in game_cfg.game_list if g and not g.frozen]
            body = lg.SerializeToString()
            self.LastInfo[0] = cur_ver
            self.LastInfo[1] = body
            self.write(body)
        self.finish()
