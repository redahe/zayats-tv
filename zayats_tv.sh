#!/bin/bash

python zayats_tv.py > playlist.m3u
script -f -c 'mpv --playlist playlist.m3u 2>/dev/null' /dev/null | tee watch.log
cat watch.log | python zayats_tv.py -watch
#rm watch.log

