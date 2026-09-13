"""Apply the Jarvis extras to the Home Assistant config (run inside the container).
Backs up every file it touches. Idempotent."""
import shutil, time, yaml, os
class L(yaml.SafeLoader): pass
L.add_multi_constructor("!", lambda loader, suffix, node: None)   # tolerate !secret / !include tags
def check(text): yaml.load(text, Loader=L)
TS = time.strftime("%Y%m%d-%H%M%S")
SRC = "/tmp/jarvis_extras"
def backup(p): shutil.copy(p, p + ".bak-" + TS)

# 1) custom sentences
dst = "/config/custom_sentences/en/jarvis_extras.yaml"
shutil.copy(f"{SRC}/jarvis_extras.yaml", dst); check(open(dst).read()); print("sentences ok")

# 2) intent scripts
p = "/config/intent_scripts.yaml"; s = open(p).read()
if "JarvisWhatHeard:" not in s:
    backup(p); s = s.rstrip("\n") + "\n\n" + open(f"{SRC}/jarvis_extras_intents.yaml").read()
    check(s); open(p, "w").write(s); print("intent_scripts patched")
else: print("intent_scripts already patched")

# 3) scripts
p = "/config/scripts.yaml"; s = open(p).read()
if "jarvis_reminder:" not in s:
    backup(p); s = s.rstrip("\n") + "\n" + open(f"{SRC}/jarvis_extras_scripts.yaml").read()
    check(s); open(p, "w").write(s); print("scripts patched")
else: print("scripts already patched")

# 4) automations: webhook relay + presence gate on the morning brief
p = "/config/automations.yaml"; s = open(p).read()
changed = False
if "jarvis_transcript_webhook" not in s:
    s = s.rstrip("\n") + "\n" + open(f"{SRC}/jarvis_extras_automations.yaml").read(); changed = True
old = """  - condition: numeric_state
    entity_id: counter.jarvis_morning
    below: 1
  actions:
  - delay:
      seconds: 2
  - action: script.jarvis_sfx
    data:
      sound: yawn_short"""
new = """  - condition: numeric_state
    entity_id: counter.jarvis_morning
    below: 1
  - condition: template
    value_template: >-
      {{ trigger.entity_id == 'alarm_control_panel.alarmo'
         or is_state('binary_sensor.living_room_motion_occupancy', 'on')
         or (now() - states.binary_sensor.living_room_motion_occupancy.last_changed).total_seconds() < 1800 }}
  actions:
  - delay:
      seconds: 2
  - action: script.jarvis_sfx
    data:
      sound: yawn_short"""
if old in s and "living_room_motion_occupancy.last_changed).total_seconds() < 1800 }}\n  actions:\n  - delay:\n      seconds: 2" not in s:
    s = s.replace(old, new, 1); changed = True
if changed:
    backup(p); check(s); open(p, "w").write(s); print("automations patched")
else: print("automations already patched")

# 5) configuration.yaml: helpers + rest commands
p = "/config/configuration.yaml"; s = open(p).read()
if "jarvis_last_heard" not in s:
    backup(p)
    s = s.replace("rest_command:\n", """rest_command:
  # Jarvis's own output volume (jarvis-ctl container on the satellite host)
  jarvis_volume:
    url: 'http://192.168.0.229:10710/volume{{ query }}'
    method: POST
  jarvis_volume_get:
    url: 'http://192.168.0.229:10710/volume'
    method: GET
""", 1)
    s = s.rstrip("\n") + """

# Jarvis: what he last heard / said (filled by the jarvis-transcript webhook)
input_text:
  jarvis_last_heard:
    name: Jarvis last heard
    max: 255
    icon: mdi:ear-hearing
  jarvis_prev_heard:
    name: Jarvis previously heard
    max: 255
    icon: mdi:ear-hearing
  jarvis_last_said:
    name: Jarvis last said
    max: 255
    icon: mdi:account-voice
"""
    open(p, "w").write(s); print("configuration patched")
else: print("configuration already patched")
