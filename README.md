# Local voice services

![The Jarvis face on the office display: iris skin, dusk background, idle](docs/face-iris.png)

*Jarvis on the 7" display (iris skin, dusk background). Face source: `face/`.*

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

Voice: "tell me a joke" asks the LLM for a one-liner, speaks it, and laughs
after it (`script.jarvis_laugh_later`). Insults ("shut up", "you're useless")
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
(6 in docker-compose.yml). After Jarvis finishes a spoken reply he keeps the
pipeline open for N seconds; say the next thing without "hey Jarvis". The mic
also still feeds the wake-word service during that window, so "hey Jarvis"
keeps working. Silence for N seconds -> back to wake word (the log says
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
