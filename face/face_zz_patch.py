import os, shutil, sys, time
p = sys.argv[1] if len(sys.argv) > 1 else "/home/mj/face.html"
s = open(p, encoding="utf-8").read()
if 'class="zz"' in s:
    print("already patched"); raise SystemExit
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
def rep(old, new):
    global s
    assert old in s, "anchor not found: " + old[:80]
    s = s.replace(old, new, 1)

# CSS: three little z's drift up and away from the right eye while asleep
rep("""  .face[data-skin="iris"][data-state="sleeping"] .body { filter: brightness(.6) saturate(.5); }""",
"""  .face[data-skin="iris"][data-state="sleeping"] .body { filter: brightness(.6) saturate(.5); }
  .face .eyes { position: relative; }
  .face .zz { position: absolute; right: calc(var(--s) * -.06); top: calc(var(--s) * .12); width: 0; height: 0; display: none; pointer-events: none; z-index: 4; }
  .face[data-state="sleeping"] .zz { display: block; }
  .face .zz span { position: absolute; left: 0; bottom: 0; font: 700 calc(var(--s) * .2) / 1 ui-monospace, "DejaVu Sans Mono", monospace;
                   color: var(--c); text-shadow: 0 0 calc(var(--s) * .04) rgba(var(--g), .8); opacity: 0;
                   animation: faceZ 3.9s ease-out infinite; }
  .face .zz span:nth-child(2) { animation-delay: 1.3s; font-size: calc(var(--s) * .26); }
  .face .zz span:nth-child(3) { animation-delay: 2.6s; font-size: calc(var(--s) * .32); }
  @keyframes faceZ {
    0%   { opacity: 0;  transform: translate(0, 0) scale(.5) rotate(-10deg); }
    12%  { opacity: .85; }
    70%  { opacity: .6; }
    100% { opacity: 0;  transform: translate(calc(var(--s) * .55), calc(var(--s) * -1.05)) scale(1.3) rotate(14deg); }
  }""")
# DOM: the z's live inside the eyes block so they follow the eye size and skin
rep("""    root.innerHTML = `<div class="eyes">${eyeHTML("L")}${eyeHTML("R")}</div>`;""",
    """    root.innerHTML = `<div class="eyes">${eyeHTML("L")}${eyeHTML("R")}<div class="zz"><span>z</span><span>z</span><span>z</span></div></div>`;""")
open(p, "w", encoding="utf-8").write(s)
print("face.html patched (zz):", len(s), "bytes")
