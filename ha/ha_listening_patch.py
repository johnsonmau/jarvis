import shutil, time, yaml
class L(yaml.SafeLoader): pass
L.add_multi_constructor("!", lambda l, s, n: None)
TS = time.strftime("%Y%m%d-%H%M%S")
p = "/config/configuration.yaml"; s = open(p).read()
if "jarvis_listening" not in s:
    shutil.copy(p, p + ".bak-" + TS)
    s = s.rstrip("\n") + """

# Jarvis: the satellite is actively listening (wake word heard or follow-up window open).
# Set by the jarvis-transcript webhook; the face shows its "listening" pill from this.
input_boolean:
  jarvis_listening:
    name: Jarvis listening
    icon: mdi:ear-hearing
"""
    yaml.load(s, Loader=L); open(p, "w").write(s); print("configuration: input_boolean.jarvis_listening added")
p = "/config/automations.yaml"; s = open(p).read()
old = """    - conditions: '{{ trigger.json.kind == ''said'' }}'
      sequence:
      - action: input_text.set_value
        target:
          entity_id: input_text.jarvis_last_said
        data:
          value: '{{ trigger.json.text | truncate(250, true, '''') }}'
"""
new = old + """    - conditions: '{{ trigger.json.kind == ''listening'' }}'
      sequence:
      - action: 'input_boolean.turn_{{ ''on'' if trigger.json.text == ''on'' else ''off'' }}'
        target:
          entity_id: input_boolean.jarvis_listening
"""
if "kind == ''listening''" not in s:
    assert old in s, "webhook automation anchor missing"
    shutil.copy(p, p + ".bak-" + TS)
    s = s.replace(old, new, 1); yaml.load(s, Loader=L); open(p, "w").write(s); print("automations: listening branch added")
