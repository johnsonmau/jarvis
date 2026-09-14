#!/bin/sh
# Plays the satellite's output (raw s16le 22050 Hz mono on stdin: TTS, chimes,
# announcements) through the host's system PulseAudio.
#  - volume: whatever jarvis-ctl last wrote to /data/pa (PulseAudio scale,
#    65536 = 100 %), default 38336 (same as the old snd.sh)
#  - "TARS" treatment: ffmpeg filter chain from TARS_FILTER (slightly deeper,
#    speaker-box EQ, tiny metallic slap, light compression). Empty = plain.
v=$(cat /data/pa 2>/dev/null)
case "$v" in ''|*[!0-9]*) v=38336 ;; esac
FILTER="${TARS_FILTER-asetrate=22050*0.95,aresample=22050,atempo=1.0526,highpass=f=120,lowpass=f=6500,equalizer=f=1700:t=q:w=1.4:g=3.5,aecho=0.9:0.32:10:0.22,acompressor=threshold=-18dB:ratio=3:attack=4:release=90,volume=1.0}"
PLAY="paplay --server=tcp:192.168.0.229:4713 --raw --rate=22050 --format=s16le --channels=1 --volume=$v"
if [ -n "$FILTER" ] && command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -nostdin -loglevel error -f s16le -ar 22050 -ac 1 -i pipe:0 -af "$FILTER" -f s16le -ar 22050 -ac 1 pipe:1 | $PLAY
else
  $PLAY
fi
