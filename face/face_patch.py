import re, os, shutil, time
p = "/home/mj/face.html"
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
s = open(p, encoding="utf-8").read()
if "GESTURES = {" in s:
    print("already patched"); raise SystemExit
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:70]
    s = s.replace(old, new, 1)

# ---- CSS: gesture animations, appended to the face stylesheet
rep("\n</style>\n<style>\n", r'''
  /* ---- gestures (driven by Home Assistant input_text.jarvis_gesture) -------- */
  @keyframes faceJolt   { 0% { transform: translateY(0); } 20% { transform: translateY(calc(var(--s) * -.12)) scale(1.04); } 45% { transform: translateY(calc(var(--s) * .05)); } 100% { transform: translateY(0); } }
  @keyframes faceBounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(calc(var(--s) * -.07)); } }
  @keyframes faceSway   { 0%, 100% { transform: rotate(-3deg) translateX(calc(var(--s) * -.03)); } 50% { transform: rotate(3deg) translateX(calc(var(--s) * .03)); } }
  @keyframes faceSnore  { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.07); } }
  .face[data-gesture="burp"][data-state]   .eyes { animation: faceJolt .6s ease-out; }
  .face[data-gesture="sneeze"][data-state] .eyes { animation: faceJolt .5s ease-out .45s; }
  .face[data-gesture="laugh"][data-state]  .eyes { animation: faceBounce .34s ease-in-out infinite; }
  .face[data-gesture="hum"][data-state]    .eyes { animation: faceSway 1.3s ease-in-out infinite; }
  .face[data-gesture="snore"][data-state]  .body { animation: faceSnore 2.4s ease-in-out infinite; }
  .face[data-gesture="sleepy"][data-state] .body, .face[data-gesture="snore"][data-state] .body { filter: brightness(.85); }
</style>
<style>
''')

# ---- engine: gestures
rep("    const LOOPS = { idle, listening, thinking, speaking, offline };", r'''    // ---- gestures: one-shot or sustained overlays on top of the state loop ---
    // Names come from Home Assistant (input_text.jarvis_gesture). Timed ones clear
    // themselves; "sleepy" stays until the entity is cleared.
    let gesture = "", ggen = 0;
    const SLEEPY = { top: 46, bot: 12, topOther: null, tilt: 0 };
    const baseRest = () => (gesture === "sleepy" || gesture === "snore") ? { ...SLEEPY } : { top: 0, bot: 0, topOther: null, tilt: 0 };
    const endGesture = (g) => { if (ggen !== g) return; delete root.dataset.gesture; rest = baseRest(); restLids(500); look(0, 0, 500); };
    const GESTURES = {
      async yawn(g)    { look(0, .15, 800); lids(70, 25, 800); await sleep(1000); if (ggen !== g) return; lids(96, 42, 500); await sleep(650); endGesture(g); },
      async burp(g)    { await sleep(150); await blink(); await sleep(450); endGesture(g); },
      async sigh(g)    { look(0, .45, 500); lids(38, 10, 600); await sleep(1300); if (ggen !== g) return; await blink(); endGesture(g); },
      async laugh(g)   { lids(48, 42, 200); await sleep(2400); endGesture(g); },
      async eyeroll(g) { lids(30, 0, 200, 30, 0); await eyeRoll(gen); if (ggen !== g) return; await sleep(400); endGesture(g); },
      async sneeze(g)  { look(0, -.6, 200); lids(55, 15, 250); await sleep(450); if (ggen !== g) return; lids(100, 62, 80); await sleep(420); endGesture(g); },
      async hum(g)     { lids(14, 16, 500); await sleep(5500); endGesture(g); },
      async look(g)    { look(-.9, -.2, 220); await sleep(900); if (ggen !== g) return; look(.7, -.1, 300); await sleep(800); endGesture(g); },
      async morning(g) { await blink(true); look(-.8, -.3, 250); await sleep(500); look(.8, -.3, 300); await sleep(500); look(0, 0, 300); await sleep(300); endGesture(g); },
      async sleepy(g)  { rest = { ...SLEEPY }; restLids(900); look(0, .2, 900);
                         while (ggen === g) { await sleep(rnd(6000, 10000)); if (ggen !== g) break; lids(100, 46, 420); await sleep(380); if (ggen !== g) break; rest = { ...SLEEPY }; restLids(800); } },
      async snore(g)   { rest = { ...SLEEPY }; restLids(700); look(0, .25, 700); await sleep(5000); endGesture(g); },
    };
    function setGesture(name) {
      name = String(name || "").trim().toLowerCase();
      if (name === gesture) return;
      gesture = name; ggen++;
      if (GESTURES[name]) { root.dataset.gesture = name; GESTURES[name](ggen); }
      else { gesture = ""; delete root.dataset.gesture; rest = baseRest(); restLids(500); }
    }
    const LOOPS = { idle, listening, thinking, speaking, offline };''')
# idle loop keeps the sleepy lids while a sustained gesture is active
rep("""      rest = { top: 0, bot: 0, topOther: null, tilt: 0 }; restLids(); look(0, 0, 400);
      while (gen === g) {""", """      rest = baseRest(); restLids(); look(0, 0, 400);
      while (gen === g) {""")
rep("""          rest = { top: 0, bot: 0, topOther: null, tilt: 0 }; restLids(); look(0, 0, 220);
        }""", """          rest = baseRest(); restLids(); look(0, 0, 220);
        }""")
rep("""      root, setState,
      get state() { return state; },""", """      root, setState, setGesture,
      get state() { return state; },
      get gesture() { return gesture; },""")

# ---- app: gesture entity, sounds param, quiet indicator
rep("""  //   &demo (no HA, cycles states; tap top half = next skin, bottom half = next background)  &state=idle  &debug""",
    """  //   &gesture=input_text.jarvis_gesture (entity the face gestures follow)  &sounds=on|off (sets input_boolean.jarvis_cheeky on connect)
  //   &demo (no HA, cycles states; tap top half = next skin, bottom half = next background; keys y/u/g/l/r/z/x/n/h/k/m = gestures, c = clear)  &state=idle  &debug""")
rep("""  const ENTITY  = q.get("entity") || "assist_satellite.usb_mic";""",
    """  const ENTITY  = q.get("entity") || "assist_satellite.usb_mic";
  const GESTURE = q.get("gesture") || "input_text.jarvis_gesture";
  const CHEEKY  = "input_boolean.jarvis_cheeky";
  const SOUNDS  = (q.get("sounds") || "").toLowerCase();""")
rep("""  const face = Face.build(document.getElementById("face"), { skin: q.get("skin") || "beam", bg: q.get("bg") || "void", size: q.get("size") });""",
    """  const face = Face.build(document.getElementById("face"), { skin: q.get("skin") || "beam", bg: q.get("bg") || "void", size: q.get("size") });
  const showQuiet = (off) => { hint.textContent = off ? "quiet mode" : ""; hint.style.display = off ? "block" : ""; hint.style.opacity = off ? ".45" : ""; };""")
rep("""      if (e.key === " ") { face.setState(next(cycle, face.state)); }""",
    """      if (e.key === " ") { face.setState(next(cycle, face.state)); }
      const gk = { y: "yawn", u: "burp", g: "sigh", l: "laugh", r: "eyeroll", z: "sleepy", x: "snore", n: "sneeze", h: "hum", k: "look", m: "morning", c: "" };
      if (e.key in gk) face.setGesture(gk[e.key]);""")
rep("""        ws.send(JSON.stringify({ id: msgId++, type: "subscribe_events", event_type: "state_changed" }));""",
    """        ws.send(JSON.stringify({ id: msgId++, type: "subscribe_events", event_type: "state_changed" }));
        if (SOUNDS === "on" || SOUNDS === "off") ws.send(JSON.stringify({ id: msgId++, type: "call_service", domain: "input_boolean", service: "turn_" + SOUNDS, target: { entity_id: CHEEKY } }));""")
rep("""      else if (m.type === "result" && Array.isArray(m.result)) { const e = m.result.find(s => s.entity_id === ENTITY);""",
    """      else if (m.type === "result" && Array.isArray(m.result)) { const g = m.result.find(s => s.entity_id === GESTURE); face.setGesture(g ? g.state : ""); const c = m.result.find(s => s.entity_id === CHEEKY); showQuiet(!!c && c.state === "off"); const e = m.result.find(s => s.entity_id === ENTITY);""")
rep("""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === ENTITY)""",
    """      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === GESTURE) face.setGesture(m.event.data.new_state?.state || "");
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === CHEEKY) showQuiet(m.event.data.new_state?.state === "off");
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === ENTITY)""")
open(p, "w", encoding="utf-8").write(s)
print("face.html patched:", len(s), "bytes")
# token-free copy for testing in a browser (demo mode needs no token)
t = re.sub(r"eyJ[A-Za-z0-9_.-]{20,}", "PASTE_TOKEN", s)
os.makedirs("/tmp/facetest", exist_ok=True)
open("/tmp/facetest/face.html", "w", encoding="utf-8").write(t)
print("test copy written, token stripped:", "eyJ" not in t)
