#!/bin/sh
# Satellite log watcher, two jobs:
#  1) Mic watchdog. When the USB mic drops off the bus the satellite's arecord
#     reattaches but wake-word detection has been seen to stay dead. On a mic
#     disconnect, wait for the card to be back on the host, then restart the
#     satellite container.
#  2) Transcript relay. Every "transcript" (what Jarvis heard) and "synthesize"
#     (what he replied) event is POSTed to a Home Assistant webhook, which stores
#     them in input_text.jarvis_last_heard / jarvis_last_said. That feeds the
#     "what did you hear" intent and the caption on the face.
SAT=${SATELLITE:-wyoming-satellite}
CARD=${MIC_CARD:-Microphone}
COOLDOWN=${COOLDOWN:-90}
HOOK=${HA_WEBHOOK:-http://192.168.0.229:8123/api/webhook/jarvis-transcript}
last=0

post() {  # post <kind> <text>
  txt=$(printf '%s' "$2" | sed 's/\\/\\\\/g; s/"/\\"/g' | cut -c1-250)
  wget -q -O /dev/null -T 5 --header='Content-Type: application/json' \
       --post-data="{\"kind\":\"$1\",\"text\":\"$txt\"}" "$HOOK" 2>/dev/null \
    || echo "micwatch: webhook post failed ($1)"
}

echo "micwatch: watching $SAT (card '$CARD', webhook $HOOK)"
docker logs -f --since 5s "$SAT" 2>&1 | while IFS= read -r line; do
  case "$line" in
    *"type='transcript'"*)
      t=$(printf '%s' "$line" | sed -n "s/.*'text': [\"']\(.*\)[\"']}, payload.*/\1/p")
      [ -n "$t" ] && post heard "$t"
      continue ;;
    *"type='synthesize'"*)
      t=$(printf '%s' "$line" | sed -n "s/.*'text': [\"']\(.*\)[\"'], 'voice'.*/\1/p")
      [ -n "$t" ] && post said "$t"
      continue ;;
    *"Mic service disconnected"*|*"audio open error"*|*"read error: No such device"*) ;;
    *) continue ;;
  esac
  now=$(date +%s)
  [ $((now - last)) -lt "$COOLDOWN" ] && continue
  echo "micwatch: mic trouble seen: $line"
  sleep 8
  tries=0
  until grep -q "$CARD" /host_cards 2>/dev/null; do
    tries=$((tries + 1)); [ "$tries" -eq 1 ] && echo "micwatch: card '$CARD' not present, waiting for it"
    sleep 5
  done
  echo "micwatch: card present, restarting $SAT"
  docker restart "$SAT" >/dev/null 2>&1 && echo "micwatch: restarted $SAT" || echo "micwatch: restart failed"
  last=$(date +%s)
done
