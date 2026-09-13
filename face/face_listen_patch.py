import shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'id="listen"' in s: print("already patched"); raise SystemExit
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:70]
    s = s.replace(old, new, 1)
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
rep("""  #caption.heard::before { content: "\\201C"; } #caption.heard::after { content: "\\201D"; }
</style>""",
"""  #caption.heard::before { content: "\\201C"; } #caption.heard::after { content: "\\201D"; }
  /* "listening" pill: visible whenever the satellite is listening (wake word or follow-up window) */
  #listen { position: fixed; top: 4vmin; left: 50%; transform: translateX(-50%) translateY(-1vmin); z-index: 9; pointer-events: none;
            display: flex; align-items: center; gap: 1.2vmin; padding: 1.1vmin 2.4vmin; border-radius: 99px;
            background: rgba(92,193,255,.12); border: 1px solid rgba(92,193,255,.45); color: #d4ecff;
            font-size: 2.4vmin; letter-spacing: .18em; text-transform: uppercase;
            opacity: 0; transition: opacity .25s ease, transform .25s ease; }
  #listen::before { content: ""; width: 1.6vmin; height: 1.6vmin; border-radius: 50%; background: #5cc1ff;
            box-shadow: 0 0 1.2vmin #5cc1ff; animation: listenDot 1.1s ease-in-out infinite; }
  @keyframes listenDot { 0%, 100% { transform: scale(.7); opacity: .6; } 50% { transform: scale(1.15); opacity: 1; } }
  #face[data-state="listening"] ~ #listen { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>""")
rep("""  <div id="caption"></div>""", """  <div id="caption"></div>
  <div id="listen">listening</div>""")
open(p, "w", encoding="utf-8").write(s); print("face.html patched (listen pill):", len(s), "bytes")
