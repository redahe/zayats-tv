#!/usr/bin/python

import sys
import unittest2 as unittest

sys.path.append('../')
import zayats_tv as zay  #NOQA


class TestZayats(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestZayats, self).__init__(*args, **kwargs)
        zay.CONFIG_FILE = 'conf_dir/config'
        zay.WATCHED_FILE = 'conf_dir/watched'
        zay.PLAYLIST_FILE = 'conf_dir/last.m3u'
        zay.read_config()

    def test1_config_rel_paths(self):
        self.assertEquals('serials', zay.path_to_serials)
        self.assertEquals('adv', zay.path_to_adv)

    def test2_make_play_list(self):
        lst = zay.make_play_list()
        self.assertTrue('serials/Bserial/s1/ep2' in lst)


if __name__ == '__main__':
    unittest.main()
