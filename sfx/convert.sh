#!/bin/bash
set -e
cd ~/voice/sfx
mkdir -p out
# normalize to speech-ish loudness, mono 22050 16-bit, trim silence at the edges
conv() { # name [extra -af filters] [-t seconds]
  ffmpeg -nostdin -y -loglevel error -i raw/$1.mp3 ${3:+-t $3} -af "${2:+$2,}silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse,loudnorm=I=-16:TP=-1.5:LRA=7" -ar 22050 -ac 1 -sample_fmt s16 out/$1.wav
}
conv yawn; conv yawn_short; conv burp1; conv burp2; conv sigh1; conv sigh2; conv chuckle; conv chuckle2; conv laugh; conv sneeze
conv snore "afade=t=out:st=3.4:d=0.6" 4.0
conv whistle "afade=t=out:st=1.7:d=0.3" 2.0
# hiccups: three hiccups with short gaps
ffmpeg -nostdin -y -loglevel error -i raw/hiccup1.mp3 -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,loudnorm=I=-16:TP=-1.5" -ar 22050 -ac 1 -sample_fmt s16 out/_h.wav
ffmpeg -nostdin -y -loglevel error -i out/_h.wav -i out/_h.wav -i out/_h.wav -filter_complex "[0]apad=pad_dur=0.9[a];[1]apad=pad_dur=1.1[b];[a][b][2]concat=n=3:v=0:a=1" -ar 22050 -ac 1 -sample_fmt s16 out/hiccup.wav
rm -f out/_h.wav
for f in out/*.wav; do printf "%-12s %5.2fs\n" "$(basename $f .wav)" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f)"; done
docker cp out/. homeassistant:/config/www/jarvis/
docker exec homeassistant ls /config/www/jarvis | tr '\n' ' '; echo
curl -s -o /dev/null -w "www url http %{http_code}\n" http://192.168.0.229:8123/local/jarvis/burp1.wav
