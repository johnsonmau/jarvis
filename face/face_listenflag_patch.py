import shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'jarvis_listening' in s: print("already patched"); raise SystemExit
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:70]
    s = s.replace(old, new, 1)
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
rep("""  const HEARD = "input_text.jarvis_last_heard", SAID = "input_text.jarvis_last_said";""",
"""  const HEARD = "input_text.jarvis_last_heard", SAID = "input_text.jarvis_last_said";
  // The satellite reports its own listening state here (via jarvis-micwatch). Home Assistant's
  // assist_satellite state drops back to idle ~2 s into a follow-up window (a TTS safety timer),
  // so while this flag is on, an "idle" from HA is shown as listening.
  const LISTENING = "input_boolean.jarvis_listening";
  let satListening = false, lastHaState = "idle";""")
rep("""  function applyState(s) {
    const key = face.resolve(s);""",
"""  function applyState(s) {
    lastHaState = face.resolve(s);
    if (lastHaState === "idle" && satListening) s = "listening";
    const key = face.resolve(s);""")
rep("""  function applyGesture(name) {""",
"""  function applyListening(on) {
    satListening = on;
    if (on && lastHaState === "idle") applyState("idle");            // becomes listening via the flag
    else if (!on && face.state === "listening" && lastHaState === "idle") applyState("idle");
  }
  function applyGesture(name) {""")
# initial state dump + live events
rep("""const g = m.result.find(s => s.entity_id === GESTURE); applyGesture(g ? g.state : "");""",
"""const li = m.result.find(s => s.entity_id === LISTENING); satListening = !!li && li.state === "on"; const g = m.result.find(s => s.entity_id === GESTURE); applyGesture(g ? g.state : "");""")
rep("""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === HEARD) showCaption("heard", m.event.data.new_state?.state);""",
"""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === LISTENING) applyListening(m.event.data.new_state?.state === "on");
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === HEARD) showCaption("heard", m.event.data.new_state?.state);""")
open(p, "w", encoding="utf-8").write(s); print("face.html patched (listening flag):", len(s), "bytes")
