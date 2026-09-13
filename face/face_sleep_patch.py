import re, os, shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'async function sleeping(' in s:
    print("already patched"); raise SystemExit
if os.path.exists(p):
    shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:80]
    s = s.replace(old, new, 1)

# ---- CSS: a sleeping state (lids nearly shut, slow breathing, dimmed) ------------------------
rep("""  .face[data-state="offline"]   { --c: #98a3a9; --c2: #4a545a; --g: 110,120,130; }""",
"""  .face[data-state="offline"]   { --c: #98a3a9; --c2: #4a545a; --g: 110,120,130; }
  .face[data-state="sleeping"]  { --c: #a9bcc6; --c2: #4f6572; --g: 100,130,150; }""")
rep("""  .face[data-gesture="sleepy"][data-state] .body, .face[data-gesture="snore"][data-state] .body { filter: brightness(.85); }""",
"""  .face[data-gesture="sleepy"][data-state] .body, .face[data-gesture="snore"][data-state] .body { filter: brightness(.85); }
  /* ---- asleep: after a quiet spell (see &sleep= in the app script) ----------- */
  @keyframes faceBreathSlow { 0%, 100% { transform: scale(1) translateY(0); } 50% { transform: scale(1.03) translateY(calc(var(--s) * .015)); } }
  .face[data-state="sleeping"] .body { animation: faceBreathSlow 4.2s ease-in-out infinite; filter: brightness(.72) saturate(.7); }
  .face[data-state="sleeping"] .eyes { transform: translateY(calc(var(--s) * .04)); }
  .face[data-state="sleeping"] .halo { border-color: rgba(var(--g), .22); animation: none; }
  .face[data-state="sleeping"] .spec { opacity: .35; }
  .face[data-skin="iris"][data-state="sleeping"] .body { filter: brightness(.6) saturate(.5); }""")

# ---- engine: sleeping behaviour loop ---------------------------------------------------------
rep("""  const STATES = ["idle", "listening", "thinking", "speaking", "offline"];""",
    """  const STATES = ["idle", "listening", "thinking", "speaking", "offline", "sleeping"];""")
rep("""    function offline() { rest = { top: 42, bot: 8, topOther: null, tilt: 0 }; restLids(600); look(0, .25, 600); }""",
"""    function offline() { rest = { top: 42, bot: 8, topOther: null, tilt: 0 }; restLids(600); look(0, .25, 600); }
    // asleep: lids drift almost shut, gaze sinks, the odd slow twitch / fully-shut moment
    async function sleeping(g) {
      look(0, .3, 1600);
      rest = { top: 62, bot: 22, topOther: null, tilt: 0 }; restLids(1200); await sleep(1300); if (gen !== g) return;
      rest = { top: 74, bot: 18, topOther: null, tilt: 0 }; restLids(1800);          // a thin slit stays open
      while (gen === g) {
        await sleep(rnd(9000, 18000)); if (gen !== g) break;
        if (chance(.3)) { lids(100, 40, 1200); await sleep(rnd(1200, 2500)); if (gen !== g) break; restLids(1400); }
        else { look(rnd(-.2, .2), rnd(.2, .4), 1800); }
      }
    }""")
rep("""    const LOOPS = { idle, listening, thinking, speaking, offline };""",
    """    const LOOPS = { idle, listening, thinking, speaking, offline, sleeping };""")
rep("""      root, setState, setGesture,
      get state() { return state; },""",
"""      root, setState, setGesture,
      resolve(s) { return LOOPS[s] ? s : (LOOPS[ALIAS[s]] ? ALIAS[s] : "idle"); },
      get state() { return state; },""")

# ---- app: fall asleep after a quiet spell, wake on the next interaction ----------------------
rep("""  //   &demo (no HA, cycles states; tap top half = next skin, bottom half = next background; keys y/u/g/l/r/z/x/n/h/k/m = gestures, c = clear)  &state=idle  &debug""",
"""  //   &sleep=15 (minutes of quiet before the face falls asleep; 0 = never)  &sleepnight=5 (shorter wait inside the night window)
  //   &demo (no HA, cycles states; tap top half = next skin, bottom half = next background; keys y/u/g/l/r/z/x/n/h/k/m = gestures, c = clear, s = sleep/wake)  &state=idle  &debug""")
rep("""  const DEBUG   = q.has("debug"), DEMO = q.has("demo");""",
"""  const DEBUG   = q.has("debug"), DEMO = q.has("demo");
  const SLEEP_MIN = q.has("sleep") ? +q.get("sleep") : 15;            // quiet minutes before sleeping (0 = never)
  const SLEEP_NIGHT_MIN = q.has("sleepnight") ? +q.get("sleepnight") : SLEEP_MIN;""")
rep("""  const DIM = +q.get("dim") || 1, NIGHT = q.get("night"), NIGHTDIM = +q.get("nightdim") || .5;
  function applyDim() {
    let d = DIM;
    const m = NIGHT && NIGHT.match(/^(\\d{1,2})-(\\d{1,2})$/);
    if (m) { const h = new Date().getHours(), a = +m[1], b = +m[2]; if (a < b ? (h >= a && h < b) : (h >= a || h < b)) d = Math.min(d, NIGHTDIM); }
    face.setDim(d);
  }
  applyDim(); setInterval(applyDim, 60000);""",
"""  const DIM = +q.get("dim") || 1, NIGHT = q.get("night"), NIGHTDIM = +q.get("nightdim") || .5;
  function isNight() {
    const m = NIGHT && NIGHT.match(/^(\\d{1,2})-(\\d{1,2})$/);
    if (!m) return false;
    const h = new Date().getHours(), a = +m[1], b = +m[2];
    return a < b ? (h >= a && h < b) : (h >= a || h < b);
  }
  function applyDim() { face.setDim(isNight() ? Math.min(DIM, NIGHTDIM) : DIM); }
  applyDim(); setInterval(applyDim, 60000);

  // ---- sleep: idle for a while -> "sleeping"; any listening/thinking/speaking wakes it --------
  // Home Assistant keeps reporting idle while asleep, so idle never wakes the face; only a real
  // interaction (or a gesture from HA) does. Offline always shows as offline.
  let sleepTimer = null, asleep = false;
  const sleepDelay = () => Math.max(0, (isNight() ? SLEEP_NIGHT_MIN : SLEEP_MIN) * 60000);
  function armSleep() {
    clearTimeout(sleepTimer);
    const ms = sleepDelay(); if (!ms) return;
    sleepTimer = setTimeout(() => { if (face.state === "idle") { asleep = true; face.setState("sleeping"); status.textContent = "sleeping"; } }, ms);
  }
  function wakeUp() { const was = asleep; asleep = false; clearTimeout(sleepTimer); return was; }
  function applyState(s) {
    const key = face.resolve(s);
    if (key === "idle") { if (asleep) return; face.setState("idle"); armSleep(); return; }
    if (key === "offline") { wakeUp(); face.setState("offline"); return; }
    const was = wakeUp(); face.setState(key); if (was) face.setGesture("morning");   // active: wake with a double blink + look around
  }
  function applyGesture(name) {
    const n = String(name || "").trim().toLowerCase();
    if (asleep && n && n !== "sleepy" && n !== "snore") { wakeUp(); face.setState("idle"); armSleep(); }
    face.setGesture(n);
  }""")
# demo mode: "s" toggles sleep, and the auto-cycle respects it
rep("""      if (e.key === " ") { face.setState(next(cycle, face.state)); }""",
"""      if (e.key === " ") { face.setState(next(cycle, face.state)); }
      if (e.key === "s") { face.setState(face.state === "sleeping" ? "idle" : "sleeping"); if (face.state !== "sleeping") face.setGesture("morning"); }""")
rep("""    const step = () => { face.setState(lock || cycle[i++ % cycle.length]); show(); };""",
    """    const step = () => { if (face.state === "sleeping" && !lock) return; face.setState(lock || cycle[i++ % cycle.length]); show(); };""")
# HA wiring goes through applyState / applyGesture
rep("""      else if (m.type === "result" && Array.isArray(m.result)) { const g = m.result.find(s => s.entity_id === GESTURE); face.setGesture(g ? g.state : ""); const c = m.result.find(s => s.entity_id === CHEEKY); showQuiet(!!c && c.state === "off"); const e = m.result.find(s => s.entity_id === ENTITY); face.setState(e ? e.state : "idle"); status.textContent = e ? e.state : "idle"; }
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === GESTURE) face.setGesture(m.event.data.new_state?.state || "");""",
"""      else if (m.type === "result" && Array.isArray(m.result)) { const g = m.result.find(s => s.entity_id === GESTURE); applyGesture(g ? g.state : ""); const c = m.result.find(s => s.entity_id === CHEEKY); showQuiet(!!c && c.state === "off"); const e = m.result.find(s => s.entity_id === ENTITY); applyState(e ? e.state : "idle"); status.textContent = asleep ? "sleeping" : (e ? e.state : "idle"); }
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === GESTURE) applyGesture(m.event.data.new_state?.state || "");""")
rep("""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === ENTITY) { const s = m.event.data.new_state.state; face.setState(s); status.textContent = s; }""",
"""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === ENTITY) { const s = m.event.data.new_state.state; applyState(s); status.textContent = asleep ? "sleeping" : s; }""")
rep("""  const setOffline = () => { face.setState("offline"); status.textContent = "offline"; };""",
    """  const setOffline = () => { wakeUp(); face.setState("offline"); status.textContent = "offline"; };""")
open(p, "w", encoding="utf-8").write(s)
print("face.html patched:", len(s), "bytes")
