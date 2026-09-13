#!/bin/bash
# (Re)build and (re)start the USB-mic satellite container.
# docker-compose 1.29 on this box cannot recreate containers on the current
# Docker engine (KeyError: 'ContainerConfig'), so the satellite is managed with
# plain docker. Everything here mirrors the satellite service in
# ../docker-compose.yml; keep the two in sync.
set -e
cd "$(dirname "$0")"
docker build -t voice_satellite .
docker rm -f wyoming-satellite >/dev/null 2>&1 || true
docker run -d --name wyoming-satellite --restart unless-stopped --network voice_default \
  --device /dev/snd:/dev/snd --group-add 29 -p 10700:10700 \
  voice_satellite \
  --name usb-mic \
  --mic-command "arecord -D ${MIC_DEVICE:-plughw:CARD=Microphone,DEV=0} -r 16000 -c 1 -f S16_LE -t raw" \
  --mic-auto-gain 5 --mic-noise-suppression 2 \
  --wake-uri tcp://openwakeword:10400 --wake-word-name hey_jarvis \
  --snd-command "paplay --server=tcp:192.168.0.229:4713 --raw --rate=22050 --format=s16le --channels=1" \
  --done-wav /app/sounds/done.wav --timer-finished-wav /app/sounds/timer_finished.wav --timer-finished-wav-repeat 3 2 --snd-volume-multiplier 0.2 \
  --debug
docker logs --tail 3 wyoming-satellite
