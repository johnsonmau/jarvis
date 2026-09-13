import shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
old = """        clearTimeout(guard); retry = 0;
        ws.send(JSON.stringify({ id: msgId++, type: "get_states" }));"""
new = """        clearTimeout(guard); retry = 0;
        if (!DEBUG) status.classList.remove("show");   // hide the "cannot reach" note once we are back
        ws.send(JSON.stringify({ id: msgId++, type: "get_states" }));"""
if new in s: print("already patched"); raise SystemExit
assert old in s
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1)); print("face.html patched (status)")
