#!/bin/sh
# Plays the satellite's audio (TTS + chimes) through the host PulseAudio, at the
# volume jarvis-ctl last wrote to /data/pa (a PulseAudio volume, 65536 = 100 %).
# Default 38336 = the old --snd-volume-multiplier 0.2 in PulseAudio's cubic scale.
v=$(cat /data/pa 2>/dev/null)
case "$v" in ''|*[!0-9]*) v=38336 ;; esac
exec paplay --server=tcp:192.168.0.229:4713 --raw --rate=22050 --format=s16le --channels=1 --volume="$v"
