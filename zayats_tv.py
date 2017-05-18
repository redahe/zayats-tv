#!/usr/bin/python

import os
import time
import random
import ConfigParser
import logging


WORK_DIR = os.path.join(os.path.expanduser('~'), '.zayats-tv')

CONFIG_FILE = os.path.join(WORK_DIR, 'config')
WATCHED_FILE = os.path.join(WORK_DIR, 'watched')
PLAYLIST_FILE = os.path.join(WORK_DIR, 'last.m3u')

WAIT_AFTER_MOUNT_SECS = 5
ITERATIONS = 3


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

playlist_serials = []

# ----- init module-----
random.seed()
LOG_FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


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


def mount_if_neccessery(path):
    logging.info('Checking serials path: ' + path)
    while not os.path.exists(path):
        logging.warn("Path doesn't exist:" + path)
        logging.info("Trying to mount external storage..")
        # TODO: MOUNT
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
            yield lst[random.randint(len(lst))]


def episodes_in_season_gener(serial):
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


def make_play_list():
    playlist_serials = list(active_serials)
    serials = set(os.listdir(path_to_serials))
    target = list(serials - set(playlist_serials))
    random.shuffle(target)
    need_serials = int(config.get(SECTION, MAX_ACTIVE_SERIALS)) - len(playlist_serials)
    playlist_serials.extend(target[:min(need_serials, len(target))])

    result = []
    adv_gen = adv_gener()
    gens = [episodes_in_season_gener(serial) for serial in playlist_serials]
    for gen in gens:
            try:
                result.append(next(gen))
            except StopIteration:
                continue
            for _ in range(int(config.get(SECTION, ADV_PER_PAUSE))):
                try:
                    result.append(next(adv_gen))
                except StopIteration:
                    pass      # NO ADV
    return result


def show():
    pl = make_play_list()
    with open(PLAYLIST_FILE, 'w') as f:
        f.writelines(pl)


def main():
    read_config()
    if not path_to_serials:
        logging.error('path_to_serials is not specified')
    mount_if_neccessery(path_to_serials)
    if path_to_adv:
        mount_if_neccessery(path_to_adv)
    else:
        logging.warn('path_to_adv is not specified')

if __name__ == '__main__':
    main()
