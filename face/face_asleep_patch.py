import os, shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'input_boolean.jarvis_asleep' in s:
    print("already patched"); raise SystemExit
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:80]
    s = s.replace(old, new, 1)

# yawn first, then doze; tell Home Assistant when asleep / awake
rep("""    sleepTimer = setTimeout(() => { if (face.state === "idle") { asleep = true; face.setState("sleeping"); status.textContent = "sleeping"; } }, ms);
  }
  function wakeUp() { const was = asleep; asleep = false; clearTimeout(sleepTimer); return was; }""",
"""    sleepTimer = setTimeout(() => {
      if (face.state !== "idle") return;
      face.setGesture("yawn");                                             // a yawn, then the lids drift shut
      sleepTimer = setTimeout(() => { if (face.state === "idle") { asleep = true; face.setState("sleeping"); status.textContent = "sleeping"; pushAsleep(true); } }, 2600);
    }, ms);
  }
  function wakeUp() { const was = asleep; asleep = false; clearTimeout(sleepTimer); if (was) pushAsleep(false); return was; }""")
rep("""  let ws, msgId = 1, retry = 0;""",
"""  let ws, msgId = 1, retry = 0;
  // ---- tell Home Assistant when the face is asleep, so the cheeky noises can hold off ---------
  // input_boolean.jarvis_asleep is created on first connect if it does not exist yet.
  const ASLEEP = "input_boolean.jarvis_asleep";
  let asleepSent = null;
  function pushAsleep(on) {
    if (DEMO || !ws || ws.readyState !== 1 || asleepSent === on) return;
    asleepSent = on;
    ws.send(JSON.stringify({ id: msgId++, type: "call_service", domain: "input_boolean", service: on ? "turn_on" : "turn_off", target: { entity_id: ASLEEP } }));
  }""")
rep("""      else if (m.type === "result" && Array.isArray(m.result)) { const g = m.result.find(s => s.entity_id === GESTURE); applyGesture(g ? g.state : "");""",
"""      else if (m.type === "result" && Array.isArray(m.result)) { if (!m.result.some(s => s.entity_id === ASLEEP)) ws.send(JSON.stringify({ id: msgId++, type: "input_boolean/create", name: "Jarvis asleep", icon: "mdi:sleep" })); asleepSent = null; setTimeout(() => pushAsleep(asleep), 1500); const g = m.result.find(s => s.entity_id === GESTURE); applyGesture(g ? g.state : "");""")
open(p, "w", encoding="utf-8").write(s)
print("face.html patched (asleep helper):", len(s), "bytes")
