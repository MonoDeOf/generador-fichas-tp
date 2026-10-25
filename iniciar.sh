#!/bin/sh
cd "$(dirname "$0")/backend"
python3 -m pip install -q -r requirements.txt || python3 -m pip install -q --user -r requirements.txt
python3 main.py
