#!/bin/sh
if ps -ef | grep -v grep | grep prefix_checker.py ; then
        exit 0
else
        python3 /home/iptpnocpe/traffmon/prefix_checker.py >> /home/iptpnocpe/traffmon/prefix_checker.log &
        exit 0
fi

