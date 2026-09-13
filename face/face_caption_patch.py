import os, shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'jarvis_last_heard' in s:
    print("already patched"); raise SystemExit
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:80]
    s = s.replace(old, new, 1)

# CSS + element for the caption
rep("""  body.demo #hint { display: block; }
</style>""",
"""  body.demo #hint { display: block; }
  /* caption: what Jarvis heard / said, a few seconds at the bottom */
  #caption { position: fixed; left: 50%; bottom: 4vmin; transform: translateX(-50%) translateY(1vmin); max-width: 86vw;
             font-size: 2.6vmin; line-height: 1.35; text-align: center; letter-spacing: .02em; z-index: 9;
             color: #8fa3ad; opacity: 0; transition: opacity .35s ease, transform .35s ease; pointer-events: none; }
  #caption.show { opacity: 1; transform: translateX(-50%) translateY(0); }
  #caption.said { color: #c8fff6; }
  #caption.heard::before { content: "\\201C"; } #caption.heard::after { content: "\\201D"; }
</style>""")
rep("""  <div id="hint"></div>""", """  <div id="hint"></div>
  <div id="caption"></div>""")
# config + helper
rep("""  const SLEEP_MIN = q.has("sleep") ? +q.get("sleep") : 15;            // quiet minutes before sleeping (0 = never)""",
"""  const SLEEP_MIN = q.has("sleep") ? +q.get("sleep") : 15;            // quiet minutes before sleeping (0 = never)
  const CAPTIONS = (q.get("captions") || "on").toLowerCase() !== "off";  // &captions=off hides the heard/said text
  const HEARD = "input_text.jarvis_last_heard", SAID = "input_text.jarvis_last_said";""")
rep("""  const showQuiet = (off) => { hint.textContent = off ? "quiet mode" : ""; hint.style.display = off ? "block" : ""; hint.style.opacity = off ? ".45" : ""; };""",
"""  const showQuiet = (off) => { hint.textContent = off ? "quiet mode" : ""; hint.style.display = off ? "block" : ""; hint.style.opacity = off ? ".45" : ""; };
  const caption = document.getElementById("caption"); let captionTimer = null;
  function showCaption(kind, text) {
    if (!CAPTIONS || !text || text === "unknown") return;
    clearTimeout(captionTimer);
    caption.className = kind; caption.textContent = text;
    requestAnimationFrame(() => caption.classList.add("show"));
    captionTimer = setTimeout(() => caption.classList.remove("show"), kind === "said" ? 7000 : 4500);
  }""")
# HA events -> caption (only on change, not on the initial state dump)
rep("""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === GESTURE) applyGesture(m.event.data.new_state?.state || "");""",
"""      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === HEARD) showCaption("heard", m.event.data.new_state?.state);
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === SAID) showCaption("said", m.event.data.new_state?.state);
      else if (m.type === "event" && m.event?.event_type === "state_changed" && m.event.data.entity_id === GESTURE) applyGesture(m.event.data.new_state?.state || "");""")
# demo: "t" shows a sample caption
rep("""      if (e.key === "s") { face.setState(face.state === "sleeping" ? "idle" : "sleeping"); if (face.state !== "sleeping") face.setGesture("morning"); }""",
"""      if (e.key === "s") { face.setState(face.state === "sleeping" ? "idle" : "sleeping"); if (face.state !== "sleeping") face.setGesture("morning"); }
      if (e.key === "t") { showCaption("heard", "turn the office light on"); setTimeout(() => showCaption("said", "Turned on the office light."), 2200); }""")
open(p, "w", encoding="utf-8").write(s)
print("face.html patched (captions):", len(s), "bytes")
