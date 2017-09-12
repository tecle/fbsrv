# coding: utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import os
import signal
import logging

CUR_PATH = os.getcwd()
ROOT_PATH = CUR_PATH
sys.path.append(os.path.join(ROOT_PATH, 'src'))
sys.path.append(os.path.join(ROOT_PATH, 'libs'))

import servers

server_mapping = {
    'main': servers.LogicServer,
    'op': servers.OperationServer,
    'pay': servers.PayServer,
    'live': servers.LiveServer,
    'db': servers.DatabaseServer,
    'game': servers.GameLogicServer,
    'gate': servers.LiveServer
}


def make_server(bind_addr, port, mode, config_path):
    server_cls = server_mapping.get(mode, None)
    if server_cls:
        return server_cls(ROOT_PATH, bind_addr, port, config_path)
    logging.error("Invalid option for server mode[%s], quit." % mode)
    return None


if __name__ == "__main__":
    from tornado.options import define, options

    define("port", 5001, help="Server listen port", type=int)
    define("mode", 'logic', help="choose server mode:{}".format(','.join(server_mapping.keys())), type=str)
    define("config", '', help="Server config file. Default: ./server-config/server.cfg", type=str)
    define("bind", '127.0.0.1', help="bind address, default: 127.0.0.1, use 0.0.0.0 to indicate none", type=str)
    import sys
    import copy

    default_params = {
        '--log-to-stderr': 'false',
        '--log_file_prefix': os.path.join(CUR_PATH, 'logs/chat_server.log'),
        '--log_rotate_mode': 'time',
        '--logging': 'debug',
        '--log_file_num_backups': '2'
    }
    extra_params = copy.copy(default_params)
    for item in sys.argv:
        for p in default_params:
            if item.startswith(p):
                extra_params.pop(p)
    sys.argv += ['%s=%s' % (k, v) for k, v in extra_params.items()]
    options.parse_command_line()
    server = make_server(options.bind, options.port, options.mode, options.config)


    def stop_server(signum, frame):
        logging.info("receive signal %d. will stop now" % signum)
        server.stop_server()


    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)
    server.start_server()
