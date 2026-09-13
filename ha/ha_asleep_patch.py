import re, shutil, time, yaml
p = "/config/automations.yaml"
s = open(p, encoding="utf-8").read()
if "jarvis_asleep" in s:
    print("already patched"); raise SystemExit
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))

blocks = re.split(r"(?m)^(?=- id: )", s)
GATE = ("  - condition: template\n"
        "    value_template: '{{ not is_state(''input_boolean.jarvis_asleep'',''on'') }}'\n")
out = []
for b in blocks:
    m = re.match(r"- id: (\S+)", b)
    bid = m.group(1) if m else ""
    if bid in ("jarvis_burp", "jarvis_sneeze", "jarvis_hiccups", "jarvis_hum", "jarvis_sigh", "jarvis_evening_yawn"):
        assert "  conditions:\n" in b, bid
        b = b.replace("  conditions:\n", "  conditions:\n" + GATE, 1)
    elif bid == "jarvis_snore":
        b = """- id: jarvis_snore
  alias: Jarvis - snore
  description: Part of Jarvis's cheeky behaviours. At most one quiet snore per nap,
    at night, once the face has been asleep a while (input_boolean.jarvis_asleep is
    set by face.html on the Pi). Gated by input_boolean.jarvis_cheeky and script.jarvis_sfx.
  triggers:
  - trigger: state
    entity_id: input_boolean.jarvis_asleep
    to: 'on'
    for:
      minutes: 25
  conditions:
  - condition: time
    after: '21:00:00'
    before: 00:30:00
  - condition: state
    entity_id: input_boolean.jarvis_cheeky
    state: 'on'
  - condition: template
    value_template: '{{ range(2) | random == 0 }}'
  actions:
  - action: script.jarvis_sfx
    data:
      sound: snore
      gesture: snore
      gesture_seconds: 5
  mode: single
"""
    elif bid == "jarvis_sleepy_clear":
        b = b.replace("  triggers:\n", "  triggers:\n  - trigger: state\n    entity_id: input_boolean.jarvis_asleep\n    to: 'off'\n", 1)
    out.append(b)
s2 = "".join(out)
yaml.safe_load(s2)  # must still parse
open(p, "w", encoding="utf-8").write(s2)
ids = [b[:40].split("\n")[0] for b in out if "jarvis_asleep" in b]
print("automations patched:", len(ids), ids)
