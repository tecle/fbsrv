# coding: utf-8
from __future__ import absolute_import
import os
import sys
import traceback


cur = os.getcwd()
sys.path.append(os.path.join(cur, 'src'))
sys.path.append(os.path.join(cur, 'libs'))
sys.stderr = sys.stdout

if __name__ == "__main__":
    conf_file = 'helper/server.cfg'
    from .hplcore import HelperConf, test_redis, show_notice

    if len(sys.argv) > 1:
        conf_file = sys.argv[1]
    HelperConf().conf_file = conf_file
    test_redis()

    from .thirdctrl import import_info as third_import_info
    from .httpctrl import import_info as http_import_info
    from .redisctrl import import_info as redis_import_info
    from .appctrl import import_info as app_import_info

    module_inf = '\n'.join([third_import_info, http_import_info, redis_import_info, app_import_info])
    while 1:
        func_list = show_notice()
        if not func_list:
            continue
        try:
            func_id = int(raw_input('你的选择:'))
            func_list[func_id][1]()
        except Exception:
            traceback.print_exc()
