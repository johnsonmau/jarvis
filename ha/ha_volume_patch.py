"""Replace the Jarvis volume intent handlers (speech now reads input_text.jarvis_volume) and add that helper."""
import re, shutil, time, yaml
class L(yaml.SafeLoader): pass
L.add_multi_constructor("!", lambda l, s, n: None)
TS = time.strftime("%Y%m%d-%H%M%S")
new = open("/tmp/jarvis_extras/jarvis_extras_intents.yaml").read()
def block(src, name):
    m = re.search(rf"(?ms)^{name}:\n.*?(?=^\S|\Z)", src); return m.group(0)
p = "/config/intent_scripts.yaml"; s = open(p).read(); shutil.copy(p, p + ".bak-" + TS)
for name in ("JarvisVolumeUp", "JarvisVolumeDown", "JarvisVolumeSet", "JarvisVolumeGet"):
    s = s.replace(block(s, name), block(new, name), 1)
yaml.load(s, Loader=L); open(p, "w").write(s); print("intent_scripts: volume handlers replaced")
p = "/config/configuration.yaml"; s = open(p).read()
if "jarvis_volume:" not in s.split("input_text:")[-1]:
    shutil.copy(p, p + ".bak-" + TS)
    s = s.rstrip("\n") + "\n  jarvis_volume:\n    name: Jarvis volume reply\n    max: 32\n    icon: mdi:volume-high\n"
    yaml.load(s, Loader=L); open(p, "w").write(s); print("configuration: input_text.jarvis_volume added")
