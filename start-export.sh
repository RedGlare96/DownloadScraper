#!/usr/bin/env bash
Xvfb :1 -screen 0 1920x1080x16 &
export DISPLAY=:1
cd "$1" || exit
"$1/$2/bin/python" "$1/historic_scraper.py"
sudo rm -rf /tmp/.X1-lock