#!/usr/bin/env bash

cd $1 || exit 2
for logfile in *.log; do
    i=$(echo $logfile | awk -F_ '{print $1};' -)
    new_logfile="$(echo $logfile | sed 's/^[0-9]\+_//g' -).${i}"
    echo "renaming $logfile -> $new_logfile"
    mv $logfile $new_logfile
done
