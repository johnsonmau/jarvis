import re, shutil, time, yaml
class L(yaml.SafeLoader): pass
L.add_multi_constructor("!", lambda l, s, n: None)
new = open("/tmp/jarvis_extras/jarvis_extras_intents.yaml").read()
m = re.search(r"(?ms)^JarvisTv:\n.*?(?=^\S|\Z)", new)
p = "/config/intent_scripts.yaml"; s = open(p).read()
if "JarvisTv:" not in s:
    shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    s = s.rstrip("\n") + "\n" + m.group(0); yaml.load(s, Loader=L); open(p, "w").write(s); print("JarvisTv handler added")
else: print("JarvisTv already present")
