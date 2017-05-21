#!/bin/bash
rm playlist.m3u
python zayats_tv.py > playlist.m3u
DISPLAY=:0 script -f -c 'mpv --fs --playlist playlist.m3u 2>/dev/null' /dev/null | tee watch.log
cat watch.log | python zayats_tv.py -watch
rm watch.log

