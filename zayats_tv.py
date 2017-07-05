#!/usr/bin/python

import os
import ast
import sys
import time
import pprint
import random
import ConfigParser
import logging
from subprocess import call
from shutil import copyfile

WORK_DIR = os.path.join(os.path.expanduser('~'), '.zayats-tv')

CONFIG_FILE = os.path.join(WORK_DIR, 'config')
WATCHED_FILE = os.path.join(WORK_DIR, 'watched')

WAIT_AFTER_MOUNT_SECS = 5
PLAYLIST_ITERATIONS = 6

NONE_SHOW = 'NONE'

# ----cfg-----------
MAX_ACTIVE_SERIALS = 'max_active_serials'
ADV_PER_PAUSE = 'adv_per_pause'
PATH_TO_SERIALS = 'path_to_serials'
PATH_TO_ADV = 'path_to_adv'
SECTION = 'CONFIG'
config = ConfigParser.ConfigParser({MAX_ACTIVE_SERIALS: '4',
                                    ADV_PER_PAUSE: '3'})


# ----state-------
active_serials = []
last_watched = {}

# ----inner variables ----

path_to_serials = None
path_to_adv = None
max_active_serials = 0

# ----- init module-----
random.seed()
LOG_FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=LOG_FORMAT)


def readpath(path, base):
    if os.path.isabs(path):
        return path
    else:
        return os.path.normpath(os.path.join(base, path))


def read_config():
    logging.info('Reading config: ' + CONFIG_FILE)
    config.read(CONFIG_FILE)
    dirbase = os.path.dirname(CONFIG_FILE)
    global path_to_serials
    path_to_serials = readpath(config.get(SECTION, PATH_TO_SERIALS), dirbase)
    if config.has_option(SECTION, PATH_TO_ADV):
        global path_to_adv
        path_to_adv = readpath(config.get(SECTION, PATH_TO_ADV), dirbase)
    global max_active_serials
    max_active_serials = int(config.get(SECTION, MAX_ACTIVE_SERIALS))


def read_state():
    if not os.path.exists(WATCHED_FILE):
        logging.warn('NO WATCHED LIST: ' + WATCHED_FILE + ' USE EMPTY')
        return
    with open(WATCHED_FILE) as f:
        data = ast.literal_eval(f.read())
    global active_serials
    global last_watched
    global start_from
    active_serials = data[0]
    last_watched = data[1]


def save_state():
    data = ([active_serials, last_watched])
    with open(WATCHED_FILE, 'w') as f:
        pprint.pprint(data, f)


def mount_if_necessery(path):
    logging.info('Checking serials path: ' + path)
    while not os.path.exists(path):
        logging.warn("Path doesn't exist:" + path)
        logging.info("Trying to mount external storage..")
        call(["./mount.sh"], shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        time.sleep(WAIT_AFTER_MOUNT_SECS)


def list_files(path):
    res = []
    for e in os.walk(path):
        for f in e[2]:
            res.append(os.path.join(e[0], f))
    return res


def adv_gener():
    if path_to_adv is None:
        return
    lst = list_files(path_to_adv)
    if lst:
        while True:
            yield lst[random.randint(0, len(lst)-1)]


def episodes_in_season_gener(serial):
    if not serial:
        return
    sp = os.path.join(path_to_serials, serial)
    all_episodes = sorted(list_files(sp))
    cur_season = None
    for ep in all_episodes:
        if (serial not in last_watched) or (ep > last_watched[serial]):
            season = ep[:ep.rfind(os.sep)]
            if cur_season and cur_season != season:
                break
            yield ep
            cur_season = season


def choose_serials_in_playlist():
    global active_serials
    serials = set(os.listdir(path_to_serials))
    target = list(serials - set(active_serials))
    random.shuffle(target)
    if len(active_serials) > max_active_serials:
        active_serials = active_serials[:max_active_serials]
    else:
        active_serials.extend([None]*(max_active_serials-len(active_serials)))
    j = 0
    for i in range(len(active_serials)):
        if active_serials[i] == None:
            while j < len(target):
                serial = target[j]
                gen = episodes_in_season_gener(serial)
                try:
                    next(gen)
                    active_serials[i] = target[j]
                    j += 1
                    break
                except StopIteration:
                    j += 1    # That serial has ended, try next


def stop_if_season_ended():
    global active_serials
    for i in range(len(active_serials)):
        serial = active_serials[i]
        lw = last_watched.get(serial, None)
        if lw:
            gen = episodes_in_season_gener(serial)
            try:
                ep = next(gen)
                season1 = ep[:ep.rfind(os.sep)]
                season2 = lw[:lw.rfind(os.sep)]
                if season1 != season2:
                    active_serials[i] = None
            except StopIteration:
                active_serials[i] = None  # NO more episodes


def make_play_list():
    logging.info('ACTIVE SERIALS: ' + str(active_serials))
    stop_if_season_ended()
    logging.info('FILTER RECENTLY ENDED SEASONS: ' + str(active_serials))
    result = []
    adv_gen = adv_gener()
    gens = [None] * max_active_serials
    for epoch in range(PLAYLIST_ITERATIONS):
        oldlist = list(active_serials)
        choose_serials_in_playlist()
        for i in range(max_active_serials):
            if (gens[i] == None) or (i >= len(oldlist)) or (oldlist[i] != active_serials[i]):
                gens[i] = episodes_in_season_gener(active_serials[i])
        logging.info('PLAYLIST_SERIALS: ' + str(active_serials))
        for i in range(len(active_serials)):
                try:
                    ep = next(gens[i])
                    last_watched[active_serials[i]] = ep
                    result.append(ep)
                    logging.debug(ep)
                except StopIteration:
                    result.append(NONE_SHOW)  # NO SHOW. Empty Record
                    active_serials[i] = None
                    gens[i] = None
                    continue
                for _ in range(int(config.get(SECTION, ADV_PER_PAUSE))):
                    try:
                        result.append(next(adv_gen))
                    except StopIteration:
                        break      # NO ADV
    return result


def watch():
    global active_serials
    active_serials.extend([None] * (max_active_serials - len(active_serials)))
    pos = 0
    watching = None
    for line in sys.stdin.readlines():
        ind = line.find('Playing: ')
        if ind != -1:
            if watching:                                 # We have watched an episode
                last_watched[watching[0]] = watching[1]
                watching = None
            playing = line[ind+9:]
            playing = playing.strip()
            if playing == NONE_SHOW:
                active_serials[pos] = None
                pos = (pos + 1) % max_active_serials
            if playing.startswith(path_to_serials):
                start = len(path_to_serials)
                end = playing.find(os.sep, start+1)
                serial = playing[start:end]
                serial = serial.replace(os.sep, '')
                active_serials[pos] = serial
                watching = (serial, playing)
                pos = (pos + 1) % max_active_serials

    if watching:
        active_serials = active_serials[pos-1:]+active_serials[:pos-1]
    else:
        active_serials = active_serials[pos:]+active_serials[:pos]

    save_state()
    logging.info('STATE SAVED')


def main():
    read_config()
    read_state()
    if ('-watch' in sys.argv):
        print('zayats-tv watching')
        watch()
    else:
        if not path_to_serials:
            logging.error('path_to_serials is not specified')
        mount_if_necessery(path_to_serials)
        if path_to_adv:
            mount_if_necessery(path_to_adv)
        else:
            logging.warn('path_to_adv is not specified')

        copyfile(WATCHED_FILE, WATCHED_FILE+'_backup')  # backup
        for line in make_play_list():
            print(line)


if __name__ == '__main__':
    main()
