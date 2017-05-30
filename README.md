# zayats-tv

## Features

  * Plays series and clips
  * Keeps track of watched episodes 
  * Change schedule when seasons are finished
  * Waits NAS to become available

## Requirements

* mpv
* python

## Installation

* Download zayats-tv
* Place a config file named config into ~/.zayats-tv

Example:
```
[CONFIG]
path_to_serials = /mnt/mediaplayer/serials
path_to_adv = /mnt/mediaplayer/adv
max_active_serials = 4
adv_per_pause = 3
```

path_to_serials - path to series. Each show should live in a separate folder. Folders can containt subfolders with seasons, when a  season is watched zayats-tv switchs to a next random show.<br>
path_to_adv - path to clips. <br>
max_active_serials - a number of simultaniously watched serials (default -4). <br>
adv_per_pause - how many clips to show between episodes (default -3). <br>

* Change a mount-script mount.sh if necessery.

## Run

* Launch zayats_tv.sh
<br>
MPV parameters can be changed in that shell-script.
You can control mpv from a keyboard. Press q - to exit. 

