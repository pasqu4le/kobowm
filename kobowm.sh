#!/usr/bin/env bash
# set the working directory as the one this script is
cd $(dirname $(readlink -f $0))
# launch the window manager
python ./kobowm.py