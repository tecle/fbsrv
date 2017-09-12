# coding: utf-8

import unittest

from utils.util_tools import get_age
from utils.util_tools import get_star


class UtilToolsTest(unittest.TestCase):
    def test_get_age(self):
        age = get_age(1990, 4, 26)
        self.assertEqual(26, age)
        age = get_age(1990, 1, 1)
        self.assertEqual(27, age)

    def test_get_star(self):
        self.assertEqual(12, get_star(12, 21))
        self.assertEqual(12, get_star(11, 23))
        self.assertEqual(12, get_star(11, 30))

        self.assertEqual(1, get_star(12, 22))
