#!/usr/bin/env bash
cd "$1" || exit
"$1/$2/bin/python" "$1/historic_scraper.py"