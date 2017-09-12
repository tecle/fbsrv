# coding: utf-8


import time
import unittest
from games.horserace import HorseRace


class HorseRaceTest(unittest.TestCase):
    def test_play(self):
        hr = HorseRace()
        result = hr.play_game()
        print ''
        data = HorseRace.convert_result(result.result_list)
        for i in range(len(data[0])):
            m = 0
            cur = [sum(ary[:i + 1]) for ary in data]
            for j, sm in enumerate(cur):
                if sm > cur[m]:
                    m = j
            # print cur, m
            for count in cur:
                print '.'*count
            print ''
        print data
        print result.winner_index
