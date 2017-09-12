# coding: utf-8

import unittest
import controller.live_msg_formater as live_message
import json


class LiveMessageTest(unittest.TestCase):
    def test_convert_snapshot_data_normal(self):
        row_data = [
            ['123', 'avatar028', 'x028'],
            [None, None, 'x027'],
            ['456', 'avatar025', 'x025'],
            ['999', '123141']
        ]
        s = live_message.convert_snapshot_data(row_data)
        self.assertContainDict({"Type": 8,
                                "hot": 999,
                                "charm": 123141,
                                "spe": [
                                    {"uid": "x028", "avatar": "avatar028", "level": 123},
                                    {"uid": "x027", "avatar": None, "level": 1},
                                    {"uid": "x025", "avatar": "avatar025", "level": 456}
                                ]}, json.loads(s))

        row_data = [
            [None, None, 'x027'],
            [None, None]
        ]
        s = live_message.convert_snapshot_data(row_data)
        self.assertContainDict({"Type": 8,
                                "hot": 0,
                                "charm": 0,
                                "spe": [
                                    {"uid": "x027", "avatar": None, "level": 1}
                                ]}, json.loads(s))

    def test_convert_snapshot_data_nodata(self):
        row_data = [
            ['999', '123141']
        ]
        s = live_message.convert_snapshot_data(row_data)
        self.assertContainDict({"Type": 8, "hot": 999, "charm": 123141, "spe": []}, json.loads(s))

    def test_make_io_notify_msg_user_in(self):
        data = ('uid', 'nick', 27)
        s = live_message.make_io_notify_msg(data, True)
        sobj = json.loads(s)
        self.assertContainDict({"nick": "nick", "Type": 1, "uid": "uid", "level": 27}, sobj)

    def test_make_io_notify_msg_user_out(self):
        data = 'uid'
        s = live_message.make_io_notify_msg(data, False)
        self.assertContainDict({"Type": 2, "uid": "uid"}, json.loads(s))

    def test_make_broadcast_msg(self):
        msg_list = ['{}', '{}']
        s = live_message.make_broadcast_msg(msg_list)
        print s
        self.assertContainDict({"Type": 7, "Data": [{}, {}]}, json.loads(s))

    def assertContainDict(self, left, right):
        if isinstance(left, list):
            for i, item in enumerate(left):
                self.assertContainDict(item, right[i])
        elif isinstance(left, dict):
            for key in left:
                self.assertContainDict(left[key], right[key])
        else:
            self.assertEqual(left, right)
