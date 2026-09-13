# Face kiosk (OG Pi, 192.168.0.226)

`face.template.html` is `~/face.html` on the Pi with the Home Assistant token
replaced by `PASTE_TOKEN`. To deploy: copy it to `~/face.html` on the Pi, put a
long-lived token in place of `PASTE_TOKEN` (or pass `&token=` in the URL), then
run `~/face-kiosk.sh`. The real `face.html` is git-ignored so the token never
lands in the repo.

`face-kiosk.sh` is what launches Chromium (flags + URL params). The
`face_*_patch.py` scripts are the incremental patches that produced the current
file, kept for history; they are already applied to the template.

URL params: see the comment block at the top of the app script in the template
(`skin`, `bg`, `size`, `night`, `nightdim`, `sleep`, `sleepnight`, `captions`,
`gesture`, `sounds`, `demo`, `debug`).
