# !../python
# coding:utf-8
import os
import re
import types
import sys

CUR_PATH = os.path.split(os.path.realpath(__file__))[0]
PARENT_PATH = os.path.join(CUR_PATH, "../src")
sys.path.append(PARENT_PATH)
sys.path.append(os.path.join(CUR_PATH, '../libs'))

import unittest
from unittest import runner


class UnitTestResult(runner.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super(UnitTestResult, self).__init__(stream, descriptions, verbosity)
        self.pass_num = 0
        self.err_num = 0
        self.fail_num = 0

    def addSuccess(self, test):
        super(UnitTestResult, self).addSuccess(test)
        self.pass_num += 1

    def addError(self, test, err):
        super(UnitTestResult, self).addError(test, err)
        self.err_num += 1

    def addFailure(self, test, err):
        super(UnitTestResult, self).addFailure(test, err)
        self.fail_num += 1


class TestResultWriter(object):
    @staticmethod
    def write(info):
        sys.stdout.write('\033[1;31m%s\033[0m' % info)

    @staticmethod
    def flush():
        sys.stdout.flush()


def add_test(test_suite, module_name):
    if module_name.startswith('.'):
        module_name = module_name[1:]
    mod = __import__(module_name)
    components = module_name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, types.TypeType) and issubclass(obj, unittest.TestCase):
            test_suite.addTest(unittest.makeSuite(obj, 'test'))


def get_case_from_dir(package, path, test_list):
    for case in os.listdir(path):
        case_path = os.path.join(path, case)
        if os.path.isdir(case_path) and case.endswith('_test'):
            get_case_from_dir('.'.join([package, case]), case_path, test_list)
            continue
        if case.startswith('.'):
            continue
        m = re.match(r"(.*?)_test.py$", case)
        if m is None:
            continue
        case_name = m.group(1) + "_test"
        test_list.append('.'.join([package, case_name]))


def run_test(case_list=None):
    test_list = []
    get_case_from_dir('', CUR_PATH, test_list)
    if case_list:
        for i, item in enumerate(test_list):
            if item not in case_list:
                test_list[i] = None
    ret = True
    pass_num = fail_num = err_num = 0
    for test_case in test_list:
        if not test_case:
            continue
        sys.stdout.write('\033[1;35mRun case:\033[0m\033[1;33m%s\033[0m\n' % test_case)
        runner = unittest.TextTestRunner(stream=TestResultWriter, resultclass=UnitTestResult)
        test_suite = unittest.TestSuite()
        add_test(test_suite, test_case)
        res = runner.run(test_suite)
        pass_num += res.pass_num
        fail_num += res.fail_num
        err_num += res.err_num
    print '\033[1;35m-' * 70
    print 'Summary:'
    print '-' * 70
    s_ = ('Success', 'Failed', 'Errors')
    tips_len = 8
    sys.stdout.write(
        '\033[0m\033[1;33m%s:%d\n%s:%d\n%s:%d\033[0m\n' %
        (s_[0].ljust(tips_len), pass_num, s_[1].ljust(tips_len), fail_num, s_[2].ljust(tips_len), err_num))
    return ret


if __name__ == "__main__":
    # 没有参数时跑所有case
    # 有参数时，根据参数指定的case名称跑，比如games_test下面的zhajinhua_test.py可以写成： games_test.zhajinhua_test
    # 需要使用 pip install mock 库
    if len(sys.argv) == 1:
        run_test()
    else:
        case_names = set(['.%s' % case for case in sys.argv[1:]])
        run_test(case_names)
