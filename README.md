# Local voice services

Part A of the satellite build. Start these, add them to Home Assistant, then
point Home Assistant at the board.

```
docker compose up -d
docker compose logs -f        # watch the models download
```

Then in Home Assistant:

1. **Settings > Devices & services > Add Integration > Wyoming Protocol**, three
   times, using this machine's IP with ports 10300, 10200 and 10400.
2. **Settings > Voice assistants > Add assistant** - conversation agent Home
   Assistant, speech-to-text Whisper, text-to-speech Piper, wake word
   openWakeWord with `hey_jarvis`.
3. **Settings > Voice assistants > Expose** - Assist can only touch what is
   exposed. Garage door, lights, alarm, whatever you want to say out loud.
4. Checkpoint with no hardware at all: open Assist in the web UI, press the mic
   button, say "is the garage door closed".
5. Then add the board: **Add Integration > Wyoming Protocol**, host
   `192.168.0.140`, port `10700`. It appears as a satellite device. Open it and
   set its pipeline to the assistant from step 2, and its area.

## Retiring the board: the USB mic on this box

The T5AI board kept hanging mid-reply, so the microphone is now a USB condenser
mic on this server, run as a Wyoming satellite container (`satellite/`). Once,
as root:

```
sudo usermod -aG docker,audio $USER      # then open a new shell, or prefix docker with: sg docker -c "..."
sudo apt install -y alsa-utils           # arecord/aplay on the host, for testing only
```

Then `docker compose up -d --build satellite`, and in Home Assistant add
**Wyoming Protocol** with this machine's IP and port 10700. It appears as
`assist_satellite.usb_mic`; set its pipeline and area, then remove the old
t5ai entry. The face follows `assist_satellite.usb_mic` by default.

## Assist setup (12 Sep 2026)

What Jarvis can do now, and where it lives. All Home Assistant files are under
`/home/mjpi/HomeAssistant` (root-owned; edit with `docker exec -i homeassistant`
or `docker cp`). Working copies of everything below are kept in `~/voice/ha/`.

**Pipeline "Local"** (Settings > Voice assistants): whisper small-int8 ->
Home Assistant intents first (`prefer_local_intents`) -> Ollama `llama3.2`
("Jarvis" conversation agent, Settings > Devices > Ollama) for anything the
intents don't understand -> piper `en_US-joe-medium`. The Ollama agent has no
access to devices on purpose: on this CPU a tool-enabled prompt would take
30 s+ per reply. Device questions are all handled by intents.

**Exposed to Assist** (Settings > Voice assistants > Expose): all lights, the four
smart outlets, both air purifiers, the TVs and the MPD "Office Speaker", the
alarm, weather, shopping list, door/window contacts, motion sensors, the
door-sensor temperatures ("Garage Temperature" etc.) and `cover.garage_door`.
Every exposed entity has an area; the areas Outside and Upstairs Hallway were
added. Default assistant area is Office (the satellite's area).

**Garage door** is a template cover (`templates.yaml`): state from the overhead
Aqara contact, open/close call `script.garage_script` (one press of the opener)
only when the door is in the other state. The walk-in door is "Garage Side Door".

**Custom sentences** (`custom_sentences/en/`), handlers in `intent_scripts.yaml`:
- `garage.yaml`  "is the garage [door] open/closed", "is the garage side door open"
  (needed because "garage door" parses as area + device class otherwise)
- `climate.yaml` "what's the temperature in the garage", "how warm is the living room"
- `weather.yaml` "what's the weather tomorrow", "will it rain tomorrow", "what's the forecast"
- `alarm.yaml`   "turn on the alarm" (home), "arm away", "disarm the alarm", "is the alarm armed". Needs
  `alarm_code` in `secrets.yaml` (Alarmo requires a code). Disarm by voice was added
  at the owner's request: anyone within earshot of the mic can disarm.
- `responses.yaml` says "closed" instead of "off" for doors (pre-existing)

Reload after editing, no restart needed:
Developer tools > YAML > "Conversation" (sentences), "Intent scripts", "Template entities".

Test any sentence without the mic: Settings > Voice assistants > Local > three
dots > Debug, or the Assist dialog in the top bar.

Caveat: the plain "Home Assistant" agent has fuzzy matching, so a question like
"is the office ceiling light on" can be read as "turn on the office lights". The
Local pipeline avoids this because unmatched sentences go to Jarvis (Ollama)
instead. Keep the pipeline's agent set to Jarvis.

Known unrelated issues seen in the log: VeSync (air purifiers) fails to
authenticate and needs re-login in Settings > Integrations; the Frigate and Ring
integrations log API errors; "Pi hole - ad block" automation references a
deleted device; the `snmp` binary_sensor platform no longer exists in HA.

### Names that work by voice

Home Assistant's parser reads "<area> <thing>" as an area plus a device type,
so an entity whose name starts with its own area name can only be reached
through an alias. Names were chosen to avoid that:

| Say | Entity |
|---|---|
| office overhead light / office main light / office ceiling light | light.office (named "Office Overhead") |
| office lamp; office lights (both) | light.office_lamp; area Office |
| living room overhead light, left lamp, right lamp; living room lights (all) | light.living_room, table lamps |
| front porch light / front door light, back porch light / back door light | the two outdoor lights |
| outside lights | light.outside_lights (group of both) |
| hallway light / upstairs hallway light | light.upstairs_hallway_light |
| kitchen / garage / office / living room outlet | the four outlets (device class outlet) |
| living room air purifier, bedroom air purifier | the two VeSync fans |
| office speaker / jarvis speaker | media_player.music_player_daemon |
| garage door, overhead door; garage side door | cover.garage_door; walk-in door contact |
| front door, laundry room door, laundry room window | contact sensors |
| garage / living room / front door / laundry room temperature; temperature outside | door-sensor temperatures; weather |

`sensor.daily_forecast` (templates.yaml) caches the Met.no daily forecast every
30 min for the forecast intent; fire the `refresh_forecast` event to refresh it.

**Renaming rule:** an entity name changed from the UI or API is not picked up
by the sentence matcher (only its aliases are, even after a restart), so every
exposed entity also carries its own name as an alias. When you rename something
for Jarvis, add the new name under Settings > Voice assistants > Expose >
(entity) > Aliases as well.

## Replies play from the satellite now (12 Sep 2026, later)

The satellite plays the pipeline's TTS itself through the host's system
PulseAudio (`paplay` over TCP to 192.168.0.229:4713, the sink MPD also uses),
with a chime when it stops listening. So the voice you pick in
Settings > Voice assistants > Local is the voice you hear, and there is no
second synthesis. The "T5AI reply -> MPD" automation is turned off (not
deleted); `satellite/reply.py` is still in the image if you want that path back.

`docker-compose` 1.29 on this box can no longer recreate containers
("KeyError: 'ContainerConfig'"), so use `satellite/run.sh` to rebuild/restart the
satellite. Installing the compose v2 plugin (`sudo apt install docker-compose-v2`)
would make `docker compose up -d` work again for everything.

Latency notes: whisper small-int8 takes about 2 s after you stop talking; the
satellite's "Finished speaking detection" is set to aggressive (Settings >
Devices > usb-mic). Anything the intents can't answer goes to llama3.2 on this
CPU, which takes several seconds; history is capped at 2 messages and replies at
25 words to keep that short.

**Stuck listening:** saying "hey jarvis" again before the previous reply has
finished makes wyoming-satellite 1.4.1 start a second stream that Home
Assistant never answers, and the satellite then sits in "listening" forever.
The automation "Jarvis satellite watchdog" reloads the satellite's Wyoming
entry (Settings > Devices > Wyoming Protocol > usb-mic) when it has been
listening for 25 s, processing for 60 s, or responding for 90 s; that resets
both sides in about 8 s. The same reload is the manual fix. Wait for the reply
(or the done chime) before waking it again.

**Volume:** Jarvis's own audio (TTS and the done chime) is scaled by
`--snd-volume-multiplier` in the satellite command (0.2 now; 1.0 is full).
That is the only knob to touch: the alarm sounds go through MPD, a separate
PulseAudio stream, so they stay at whatever MPD is set to.

## Cheeky Jarvis (12 Sep 2026, night)

Sounds and remarks are pushed to the satellite with `assist_satellite.announce`
(same speakers, Jarvis volume). Everything goes through `script.jarvis_sfx`,
which refuses unless: `input_boolean.jarvis_cheeky` is on, the satellite is
idle, the alarm is disarmed or armed home, the last sound was 45+ min ago, and
someone seems home (living-room motion, front door, a recent command, or the
living-room TV playing). Say "be quiet" for an hour of silence, "cheeky mode on"
to end it early; the face shows "quiet mode" while it is off.

Sound files: `/config/www/jarvis/*.wav` (CC0 from freesound, normalized;
sources in `~/voice/sfx/raw`, converter `~/voice/sfx/convert.sh`).

| Automation | When | Sound / remark |
|---|---|---|
| Jarvis - morning yawn and brief | first reply or disarm 07:00-11:00, once | yawn_short, then weather + anything left open |
| Jarvis - burp | 11:00-22:30, random, max 2/day | burp1/burp2, sometimes "Excuse me." |
| Jarvis - sigh | idle 2 h, 11:00-22:30, max 3/day | sigh1/sigh2 |
| Jarvis - sneeze | 11:00-22:30, rare, 1/day | sneeze |
| Jarvis - hiccups | 11:00-22:30, rare, 1/day | hiccup (x3) |
| Jarvis - evening yawn | idle 90 min, 21:00-00:30, max 2 | yawn, then the sleepy face |
| Jarvis - snore | idle 150 min while sleepy, 21:00-00:30 | snore |
| Jarvis - bedtime | alarm armed home after 20:00 | yawn + "Goodnight." + sleepy face |
| Jarvis - wake from sleepy | first command, 07:00, or disarm | clears the sleepy face |
| Jarvis - front door | door opens, disarmed, 11:00-22:30, 1 in 2, 30 min apart | whistle and/or "Welcome back." |
| Jarvis - late garage | garage opens 22:00-00:30 | "Late night?" |
| Jarvis - laundry window and rain | 09:30 and 17:00 if window open and rain forecast | reminder (not gated by cheeky mode) |
| Jarvis - hum | off: no usable humming sample found | |
| Jarvis - reset daily counters | 03:00 | |

Voice: "tell me a joke" asks the LLM for a one-liner and speaks it (the laugh
after it was removed on request). Insults ("shut up", "you're useless")
get a one-word reply and an eye roll.

Face (`face.html` on the Pi) follows `input_text.jarvis_gesture`: yawn, burp,
sigh, laugh, eyeroll, sneeze, hum, look, morning, sleepy (stays until cleared),
snore. URL params: `&gesture=<entity>` to follow a different entity,
`&sounds=on|off` sets cheeky mode when the face connects. In `?demo` mode the
keys y u g l r z x n h k m trigger gestures and c clears.

## Mic watchdog + face sleep (13 Sep 2026)

**Why Jarvis went deaf on 13 Sep:** the USB condenser mic dropped off the bus at
07:09 (kernel: `usb 1-4: USB disconnect` then re-enumerated 3 s later). The
satellite's `arecord` reattached, but no wake words were detected afterwards
until the container was restarted. The mic itself was fine (host `arecord`
test showed normal room levels).

**Fix:** `jarvis-micwatch` (service `micwatch` in docker-compose.yml,
script `satellite/micwatch.sh`) tails the satellite log; when it sees
`Mic service disconnected` / `audio open error` it waits for the card named
`Microphone` to be back in `/proc/asound/cards`, then `docker restart
wyoming-satellite`. Cooldown 90 s. Watch it: `docker logs -f jarvis-micwatch`.

**Face sleep** (`face.html` on the OG Pi, 192.168.0.226): after `&sleep=`
minutes of idle (default 15; `&sleepnight=` for a shorter wait inside the
`&night=` window; 0 disables) the eyes drift almost shut, breathe slowly and
dim. Any listening/thinking/speaking from `assist_satellite.usb_mic` wakes it
with a double blink and a look around; a gesture from HA wakes it too. Idle
alone never wakes it. Demo: `face.html?demo`, key `s` toggles sleep.
Relaunch the kiosk after editing: `~/face-kiosk.sh` on the Pi.

## Sleep is now shared with Home Assistant (13 Sep 2026)

`face.html` flips `input_boolean.jarvis_asleep` (it creates the helper on
first connect if missing) when the eyes doze off / wake. Automations changed
(`ha/ha_asleep_patch.py` is the script that was applied; backup of
automations.yaml is next to it in /config):

- burp, sneeze, hiccups, hum, sigh, evening yawn: extra condition, skipped
  while `jarvis_asleep` is on. Event remarks (front door, late garage,
  laundry/rain, bedtime, morning brief) are NOT gated - they wake him.
- snore: now triggers on `jarvis_asleep` being on for 25 min, 21:00-00:30,
  cheeky on, 50 % chance - at most one snore per nap. The old 150-min-idle
  trigger is gone.
- wake from sleepy: also clears the sleepy gesture when `jarvis_asleep` goes off.

Before dozing the face does a local yawn (no sound). Kiosk launcher
`~/face-kiosk.sh` on the Pi now exports the desktop session bus and passes
`--password-store=basic`, otherwise a relaunch over ssh pops a "new keyring"
dialog and the page never connects.

## Extras added 13 Sep 2026

- **"What did you hear" / "what did you say"**: `jarvis-micwatch` relays every
  transcript and reply from the satellite log to the `jarvis-transcript`
  webhook, which fills `input_text.jarvis_last_heard`, `jarvis_prev_heard`
  and `jarvis_last_said` (defined in configuration.yaml). Intents
  `JarvisWhatHeard` / `JarvisWhatSaid` read them. The face shows the same text
  as a caption for a few seconds (`&captions=off` to hide).
- **Volume by voice**: "louder", "quieter", "set your volume to 40 percent",
  "what's your volume". `jarvis-ctl` (:10710, `satellite/jarvisctl.py`) stores
  the level in `satellite/data/`; `satellite/snd.sh` passes it to paplay for
  every reply and chime. Only Jarvis's own audio changes; MPD/alarms do not.
  `rest_command.jarvis_volume` / `jarvis_volume_get` in configuration.yaml.
- **Reminders**: "remind me to move the laundry in 20 minutes" / "in 2 hours".
  `JarvisRemind` -> `script.jarvis_reminder` (parallel, up to 10) -> announce.
  Timers were already built in ("set a timer for 10 minutes", "cancel the
  timer"); the satellite plays `timer_finished.wav`.
- **Music**: "what's playing", "play some music" (MPD queue), plus the built-in
  "pause", "resume", "next track", "set volume to 50 percent" for the office
  speaker (area Office). MPD has no saved playlists, so "play jazz" is not a
  thing yet.
- **Morning brief** now also needs recent living-room motion (30 min) or the
  alarm being disarmed, so it does not fire on a half-asleep mumble.
- **Follow-up questions**: Home Assistant 2026.4 continues the conversation
  (no wake word needed) when the Ollama agent's reply asks a question. Intent
  replies never ask, so device commands still need "hey Jarvis" each time.

Sentences: `custom_sentences/en/jarvis_extras.yaml`. Handlers: `Jarvis*` in
`intent_scripts.yaml`. Working copies of all of it live in `ha/` here; the
patch that installed them is `ha/ha_extras_patch.py`.

## Git

This directory is a git repo (init 13 Sep 2026). Ignored: `.env`, models
(`whisper/`, `piper/`), `satellite/data/` (volume state), `satellite/debug/`,
`face/face.html` (has the HA token; `face/face.template.html` is the committed
copy). To push to Gitea: create an empty repo there, then
`git remote add origin http://192.168.0.229:4000/<user>/jarvis.git && git push -u origin main`.

## Follow-up listening, aliases (13 Sep 2026, afternoon)

**Follow-up without the wake word.** Home Assistant only continues a
conversation when an LLM reply ends with a question, never after an intent, so
the satellite does it itself: `satellite/patch_followup.py` is applied to
wyoming-satellite at image build (Dockerfile) and adds `--follow-up-seconds N`
(8 in docker-compose.yml). After Jarvis finishes a spoken reply he keeps the
pipeline open for N seconds; say the next thing without "hey Jarvis". Saying
"hey Jarvis ..." inside the window is fine too: the phrase lands in the
transcript and skip_words in custom_sentences/en/jarvis_extras.yaml drop it
before intent matching (an earlier version restarted the pipeline on the wake
word instead, which raced Home Assistant and left him listening in silence).
Silence for N seconds -> back to wake word (the log says
"Follow-up: no speech, back to wake word"). Announcements (reminders, burps)
do not open a window; only real replies do. Set to 0 to disable. Rebuild after
changing the patch: `docker compose build satellite && docker compose up -d satellite`.

**Aliases** (`ha/ha_aliases.py`, applied to core.entity_registry with HA
stopped): "office light(s)", "overhead light", "lamp"/"desk lamp", "bedroom
TV" / "bedroom T V" (how Parakeet spells it) / "bedroom television", same for
the living room TV, "speaker", "outside/outdoor/porch lights". Add more in
Settings > Voice assistants > Expose > entity > Aliases.

**Volume phrases** now also match "lower/raise your volume", "turn your voice
down", "you're too loud", "speak louder", etc.

**Follow-up cue (13 Sep, evening):** when the window opens the speaker plays a
soft two-note tick (`satellite/sounds/followup.wav`, `--follow-up-wav`, mic
stays open) and the face shows a pulsing "LISTENING" pill at the top for as
long as the satellite is listening (`face_listen_patch.py`). Volume phrases
accept "value"/"bound", which is what Parakeet usually hears for "volume".

## Names, aliases and the intent test hook (13 Sep, late)

- **Aliases live in `aliases_v2`** in `.storage/core.entity_registry` on this
  HA version (registry 1.22); the `aliases` key is legacy and ignored by
  Assist. A `null` entry in `aliases_v2` stands for the entity's own name;
  drop it and the name stops matching. `ha/ha_aliases3.py` is the script that
  writes them (HA must be stopped while the file is edited).
- **"multiple devices called office light"** came from "office light" being an
  alias on BOTH office lights. `ha/ha_aliases_final.py` restores the original
  alias lists with that one collision removed ("small office light" still
  reaches the lamp).
- **"T V"**: Parakeet spells TV as "T V" and hassil will not match that
  against an alias, so `JarvisTv` in jarvis_extras.yaml handles
  "turn off [the] bedroom t v" directly.
- **Volume**: intent_script speech cannot see action variables, so the volume
  handlers stash the reply in `input_text.jarvis_volume` and speak from it.
- **Test any sentence without the mic**: POST to the local webhook
  `jarvis-intent-test` (automation "Jarvis - intent test hook"):
  `curl -X POST -H 'Content-Type: application/json' -d '{"text":"turn on the office light"}' http://192.168.0.229:8123/api/webhook/jarvis-intent-test`
  The intent agent's reply lands in `input_text.jarvis_last_said` as "TEST: ...".
  Add `"agent":"conversation.jarvis"` to the JSON to go through Ollama instead.

**Listening pill during follow-up (13 Sep, late):** Home Assistant arms a TTS
safety timer after every reply that forces `assist_satellite.usb_mic` back to
idle ~2 s later, even when a follow-up run has already started, so the face
cannot rely on that state. `jarvis-micwatch` now relays the satellites own

## Nest thermostat (13 Sep 2026)

Commissioned over Matter (python-matter-server container, see ~/matter) as
`climate.nest_thermostat` ("Thermostat"), with `sensor.nest_thermostat_temperature`.
Both exposed to Assist. Built-in: "set the thermostat to 70", "what's the inside
temperature". Added (`custom_sentences/en/thermostat.yaml`): "what's the
thermostat set to", "set the thermostat to cool/heat/auto/off", "turn on the
heat", "turn it up/down", "it's cold in here" (nudges the set point by 2).

## LLM router: workstation GPU first, this box as fallback (13 Sep 2026)

Home Assistant's Ollama integration now points at `http://127.0.0.1:11435`, a
small router container in `~/llm-router` (aiohttp, `docker compose up -d --build`).
Every request goes to the workstation SWISSARMYKNIFE (192.168.0.15:11434,
RX 9070 XT, model `gemma3:12b`, ~0.5 s per answer) when a 1 s probe succeeds,
otherwise to the local Ollama (`llama3.2:latest`, several seconds). It swaps the
model name per backend and drops tool schemas on the fallback, so HA keeps one
"Jarvis" agent and one pipeline. When the workstation is down it remembers that
for 30 s. `curl -s http://127.0.0.1:11435/status` shows which side is active;
`sensor.jarvis_brain` (rest sensor in configuration.yaml) mirrors it as GPU/CPU.

On the workstation: Ollama 0.34 for Windows, user env `OLLAMA_HOST=0.0.0.0:11434`
and `OLLAMA_KEEP_ALIVE=-1` (model stays in VRAM), started at login from the
Startup folder, inbound firewall rule "Ollama LAN (192.168.0.0/24)" on TCP 11434.
Sleep is set to never on AC, so it stays reachable.

## TARS (13 Sep 2026, late)

- **Voice:** piper `en_GB-alan-medium` in the Local pipeline, plus a "TARS"
  treatment applied to everything the satellite plays (`satellite/play.sh`:
  ffmpeg chain from `TARS_FILTER` in docker-compose.yml, slightly deeper,
  speaker-box EQ, tiny metallic slap, light compression). Set `TARS_FILTER: ""`
  for the plain voice. play.sh keeps the jarvis-ctl volume from /data/pa that
  snd.sh used, so that control still works. Applies on both GPU and CPU
  answers, since TTS always runs on this box.
- **Wake word:** "TARS", using the community openWakeWord model from
  fwartner/home-assistant-wakewords-collection (`./openwakeword/TARS.tflite`,
  mounted at /custom, `--custom-model-dir /custom`). "hey jarvis" is still
  loaded as a second wake word; drop `--wake-word-name hey_jarvis` from the
  satellite command to retire it. The Local pipeline's wake word is TARS.
- The LLM prompt now introduces the assistant as TARS (Jarvis still accepted).

## Alarm and door announcements are TARS now (14 Sep 2026)

The old alarm/door sounds were MP3s inside the HA container's /media, which
is not a mounted folder, so the HA image update (2026.4 -> 2026.9) wiped them
and MPD got 404s. They are gone for good; instead:

- Alarm disarm / armed home / armed away / arming, and the five door/window
  "open" automations, now call `assist_satellite.announce` (TARS speaks, normal
  Jarvis volume). Phone notifications and conditions were kept as they were.
- "Alarm - triggered" sets MPD to 100 %, speaks "Alarm triggered. Security
  breach detected." on MPD (loud, plain British voice, no TARS filter), then
  loops `/config/www/jarvis/siren.mp3` (CC0, ~7 s, loudness-normalized) via
  MPD until disarmed, with the critical phone push each loop. The siren lives
  in the web folder (`/local/jarvis/siren.mp3`, bind-mounted) so it survives
  HA updates, and MPD fetches it without auth.
- The hourly "new hour" gun-cock automation was left alone at the owner's
  request; it still references a missing MP3 and will 404 each hour until it is
  disabled or given a sound.
- Rule of thumb: never put sounds under /media in this HA install; use
  /config/www/jarvis (served at /local/jarvis/) or speak them via TARS.

## Natural phrasing, volume, custom wake word (14 Sep 2026)

- **Fuzzy requests** ("uhhh do you think you can turn off office light?") work
  because the GPU agent now has Home Assistant's Assist tools
  (`llm_hass_api: assist` on the Ollama "Jarvis" agent). Exact phrasings still
  hit the built-in/custom intents first (~0.2 s); anything they miss goes to the
  model, which calls the matching tool and answers in ~1 s. The workstation model
  is **qwen3:8b** (tool calling; qwen3:14b spilled past the 16 GB card and ran at
  4 tokens/s, gemma3 has no tool support). On the CPU fallback the router strips
  the tools, so with the workstation off Jarvis still answers questions but only
  exact commands control devices.
- **Volume:** Jarvis's own audio is set with jarvis-ctl (`POST :10710/volume?set=N`,
  0-100, now 12; voice: "set volume to N"). The play.sh filter no longer adds gain.
  The alarm siren/voice go through MPD at 100 % and are unaffected.
- **Custom wake words:** trained with openWakeWord on the workstation
  (C:/Users/mj/oww-train, Docker, ~25 min per run; the tflite goes in
  ~/voice/openwakeword/). Loaded now: `hey_tars` (best: recall 0.53, fires on 3 of
  5 synthetic voices at threshold 0.6 / trigger 2), `tars` (bare word, weaker:
  recall 0.36, 1 of 4 voices), and `hey_jarvis` as a backup. The pipeline's wake
  word is hey_tars. If real speech misses too often, lower `--threshold` to 0.5
  in the openwakeword command; if it false-triggers, raise it or drop the bare
  `tars` model. The community TARS model is in openwakeword/community_backup;
  older training outputs are in C:/Users/mj/oww-train/data/output_v1 and _v2.


## Tuning notes (14 Sep 2026, late)

- **Wake sensitivity:** openwakeword command is now `--threshold 0.4 --trigger-level 1`
  (was 0.6/2), because "hey tars" was missing too often. If it starts waking on
  random speech, raise threshold toward 0.55 or trigger-level back to 2, or drop the
  bare `tars` model. Raw `arecord` on the host captures the mic near silence (peak
  ~480/32767); the satellite's `--mic-auto-gain 5` is what makes it usable, so
  calibrate from the live pipeline (openwakeword `--debug-probability`), not raw WAVs.
- **Follow-up run-on:** after a reply the mic reopens for 5 s (was 8) and at most
  2 rounds per wake word (FOLLOW_UP_MAX_ROUNDS in the satellite env, patch
  satellite/patch_followup_limit.py), so background noise can't keep the
  conversation going indefinitely.
- **LLM sampling / parroting:** the router (llm_router.py) forces the model per
  backend and injects repeat_penalty 1.18 / temperature 0.6, which stops qwen3:8b
  echoing its previous reply. The agent prompt tells it to answer the current turn
  only, never reuse its last reply, and reply with just "." to chatter not aimed at it.
- **Swearing:** the agent prompt allows cursing on this private adult system;
  insult comebacks in intent_scripts.yaml (InsultResponse) include profane options.

## Live info: sports, odds, news (14 Sep 2026)

`infobot` container (~/infobot, host net, :8140) fetches keyless sources and
returns a spoken-ready line, or "I can't reach the internet for that right now"
on failure:
  /sports?team=&league=   ESPN scoreboard (scores + status), nickname map (niners->49ers)
  /odds?team=&league=     same, with spread + over/under for upcoming games
  /news?topic=            Google News RSS top headlines (3), source suffix stripped
Leagues: nfl (default), nba, mlb, nhl, college football, wnba, mls. Uses UA
"curl/8.5.0" (ESPN/Akamai 403s unknown or browser UAs).

Home Assistant wiring:
- rest_command tars_sports/tars_odds/tars_news in the package /config/packages/tars_info.yaml.
- Deterministic voice: custom_sentences/en/info.yaml -> intent_script GetSports/
  GetOdds/GetNews, which fetch, stash the text in input_text.tars_info (a 255-char
  helper, because an intent_script speech template cannot read a rest_command
  response_variable), then speak it verbatim. This is the accurate path.
- LLM tools: scripts get_sports_scores/get_betting_odds/get_news_headlines
  (in scripts.yaml, exposed to Assist) return {result: text}; the qwen3 agent
  calls them for phrasings the sentences miss. Caveat: the 8B sometimes
  paraphrases or invents news, so the deterministic sentences cover the common
  news phrasings; sports/odds relay fine via either path.
- Offline: every layer relays infobot's "can't reach the internet" line.
Broader betting markets (props, futures) would need a paid odds API key; only
per-game spread/total are available keyless from ESPN.

### Fixes (14 Sep 2026, later)
- Sports/odds are now speech-formatted: "Todays

### Fixes (14 Sep 2026, later)
- Sports/odds are now speech-formatted: "Today's NFL: Broncos at Chiefs at 8:15 PM.
  Seahawks beat Patriots 13 to 10." (natural times, "beat", max 4 games, period-joined).
- infobot team matching scans for a team name/nickname anywhere in the slot text
  (a rambling "odds on the bronco game tonight" still finds the Broncos) and
  ignores short abbreviations as substrings (CHI no longer matches "chiefs").
  Nicknames live in NICKS (niners->49ers, etc).
- Thermostat by voice: deterministic ThermostatSet intent (custom_sentences/en/
  thermostat.yaml + intent_scripts.yaml) catches "set the temperature to N",
  "turn the ac on to N", "set the heat to N" and targets climate.nest_thermostat
  directly with the right mode, so it is not routed to the air purifier by the LLM.

### Thermostat: single-setpoint only (14 Sep 2026)
"Turn the AC on 67" used to fall to the LLM, which turned the Nest on into
heat_cool (auto), showing both a heat and a cool setpoint. Fixed: ThermostatSet
now also catches "turn the ac on N" (no "to"), "set the cool/cooling/heat to N",
"I need the cool to be N", "make the cool N", and always forces cool or heat mode
with one temperature. The agent prompt also forbids auto/heat_cool and forbids
turning the thermostat on without a mode. If it ever shows dual setpoints again,
say "set the cool to 70" (or use the card) to put it back to a single mode.

### Fixes (14 Sep 2026, evening 2)
- "Games today" now shows only games whose LOCAL (America/New_York) date is today,
  not the whole NFL week (infobot _is_today filter; tzdata added to the image).
  A team query still shows that team's most recent/next game unfiltered.
- Thermostat robustness: STT writes "A C" and "sixty seven", which the exact
  sentences missed, sending it to the LLM which set heat_cool. Fixes: (a) sentences
  accept "a c"/"a.c."; (b) climate.nest_thermostat is UNEXPOSED from the conversation
  agent so the LLM's generic climate/turn-on tools can't touch it; the deterministic
  ThermostatSet/Mode/Status intents still control it directly by entity_id; (c) a
  safe script.set_thermostat tool (temperature + mode cool|heat, single setpoint,
  never auto) is exposed for the LLM, and the prompt says to use only that for
  climate. Net: spoken numbers and "A C" now work and can never produce a
  dual-setpoint/auto state again.
- Wake: bare "tars" threshold lowered 0.4 -> 0.35 (trigger-level still 1) for more
  reliable single-word wakes; raise back toward 0.45 if it starts false-triggering.
  "hey tars" remains the most reliable phrase.

### Fixes (14 Sep, night)
- Weather said "F" (piper reads "°F" as a letter). Added GetCurrentWeather intent
  ("what's the weather [right now/outside/like]", "weather report") that speaks
  "It's 69 degrees and sunny, high of 70." instead of the built-in "°F" answer.
- "vs" was the LLM paraphrasing tool output on team-less follow-ups ("odds on that
  game"). Added deterministic follow-up sentences (odds/line/score on that/the game,
  "and the odds") so they relay infobot's "at" text verbatim. infobot also has a
  _say() guard (vs->versus, @->at) for its own output.
- Added no-apostrophe variants (whats/hows) across weather/info/climate/thermostat
  sentences, since STT often drops the apostrophe.
- Bare "tars" wake stays weak (didn't fire in live reps, build won't emit scores to
  tune); one shared threshold means loosening it makes hey_tars/hey_jarvis false-fire.
  Recommendation: use "hey tars" (reliable). tars stays loaded as a bonus.

### CPU fallback fixed (14 Sep, night)
When the workstation (.15) is down, Jarvis used to listen then hang and idle: the
CPU model choked on Home Assistant's full device and tool context (thousands of
tokens at 8k context). The router (llm_router.py), on the fallback backend only,
now replaces HA's system prompt with a lean TARS persona (LEAN_PROMPT), strips
tools, and sets num_ctx 2048. With .15 down: device control, weather, and sports
still work via the sentence intents (they never touch the model), and general
questions answer on the CPU in about 2 to 10 seconds instead of hanging. The
GPU/primary path is unchanged (full context and tools). Verified by pointing
PRIMARY at a dead port and running the pipeline, then restoring .15.

## TARS's eyes: camera vision (14 Sep, night)
"What do you see", "is anyone in the office", "look in the garage", "who's in the
office", "describe the office" -> TARS grabs a still from the go2rtc camera and a
vision model describes it in one spoken sentence.
- vision service: ~/vision (host net, :8150). GET /look?src=office|garage&q=...
  grabs go2rtc /api/frame.jpeg, sends to the workstation gemma3:12b (vision), returns
  {text, online}. Warm answers ~2 s, cold ~13 s (first call loads the model).
- HA: rest_command tars_look (in the package /config/packages/tars_info.yaml, needs a
  restart to register), custom_sentences/en/vision.yaml -> intent_script GetVision
  (deterministic, stashes to input_text.tars_info, speaks verbatim), plus a
  script.look_at_camera tool exposed for the LLM on fuzzy phrasings.
- Rooms: office, garage (the two go2rtc streams). Add more by adding streams and the
  room list in vision.yaml.
- WORKSTATION OFF: there is NO usable offline vision. moondream on the .229 CPU took
  32 s and returned garbage, which just hangs the pipeline, so the service does a 1 s
  probe of the workstation and, if it's down, says "I can't see right now, my eyes
  need the workstation and it's offline." (moondream is pulled on .229 but deliberately
  not used in the live path.)

### Vision prompt fix (14 Sep, night)
TARS was denying it had eyes when sight was referenced as a statement ("you can see
me") rather than a question, because the qwen3 agent prompt didn't mention the
cameras. Prompt now states it has office+garage cameras and must use the
look-at-camera tool (never say it can't see). Verified: "do you have eyes",
"can you see me", "you can see me right now" all acknowledge/use vision. Edge: a
room-less "what am I wearing" is ambiguous and may not trigger; name a room or ask
"what do you see".

## New features (14 Sep, late night)
- **Alarm voices are LOUD.** disarm/armed home/armed away/arming now call
  script.tars_say_loud (MPD at volume 1.0, tts.speak), so alarm speech is loud even
  though regular TARS stays quiet on the satellite (volume 12). Fixes the inaudible
  "arming". Triggered already loops the siren loud.
- **"Daddy's home".** Say "daddy's home" (or "the king is home", "guess who's back")
  -> office overhead+lamp on, fanfare (/local/jarvis/daddyshome.mp3) on MPD at 0.6,
  and a cheeky greeting. GetDaddysHome intent; user-invoked, ignores DND.
- **Memory.** "remember that X", "make a note to Y", "where is Z", "what did I ask
  you to remember", "forget about Z". Notes persist in the memory service (~/memorysvc,
  :8160, /data/notes.json). Deterministic intents RememberNote/RecallNote/ForgetNote
  plus LLM tools remember_note/recall_note.
- **"What can you do".** WhatCanYouDo intent lists capabilities.
- **Doorbell.** binary_sensor.front_door_ding -> TARS announces a visitor (automation
  tars_doorbell), respects DND. (Front-door camera isn't a go2rtc stream, so "look at
  the front door" isn't wired; office/garage vision only.)
- **Do Not Disturb.** input_boolean.tars_dnd. When on, ALL proactive/cheeky sound is
  muted (the check is at the top of the jarvis_sfx gate, above the force bypass, so even
  forced announcements like the morning brief are silenced) and the doorbell is silent.
  The alarm is NOT gated by DND. NOTE: the helper's entity_id is input_boolean.tars_dnd
  (it was first created as tars_do_not_disturb and renamed; everything references tars_dnd).

### Spoken-text hygiene (14 Sep, late)
piper reads emoji aloud by name ("smiling face with smiling eyes") and says "vs"
as letters. The router (llm_router.py) now filters every /api/chat and /api/generate
response, streaming or not: strips emoji/pictographs and rewrites vs -> versus in the
message content before Home Assistant speaks it. Source-agnostic, so any model or
phrasing is covered. Deterministic intents never emit emoji anyway.

### "Unable to get response" + tuning (14 Sep, late)
Cause: HA's Ollama tool-calling loop sometimes ended without a final assistant
message ("Last content is not AssistantContent") on phrasings that fell to the LLM
with tools. Mitigations: max_history raised 2 -> 6 (short history was starving the
tool-call/result exchange); prompt now says "after a tool result you MUST reply once,
never chain tools for a simple request"; and the live-data hard-rule was scoped to
ONLY live/current things so general knowledge (moon distance, capitals) is answered
normally instead of refused. Also: "dad is home"/"dad's home" now trigger GetDaddysHome;
"can you see the front door" is a deterministic GetVision (src=front) and the vision
service returns "I don't have a camera on the front, just the office and garage" for
any camera that isn't office/garage. The emoji/vs response filter in the router was
verified NOT to break the stream (360-line stream ends clean). Residual: an 8B tool
loop can still rarely stall; the common commands are deterministic and never hit it.
