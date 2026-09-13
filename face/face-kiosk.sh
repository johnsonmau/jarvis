#!/bin/bash
# Relaunch the face kiosk with the flags it was started with (captured 2026-09-12).
pkill -f "/usr/lib/chromiu[m]/chromium"; sleep 1
export DISPLAY=:0
# pick up the desktop session bus so Chromium does not ask to create a keyring when launched over ssh
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
cd ~
setsid nohup /usr/lib/chromium/chromium --force-renderer-accessibility --enable-remote-extensions --show-component-extension-options --enable-gpu-rasterization --no-default-browser-check --disable-pings --media-router=0 --disable-dev-shm-usage --enable-remote-extensions --load-extension --use-angle=gles --password-store=basic --noerrdialogs --disable-infobars --disable-session-crashed-bubble --kiosk file:///home/mj/face.html\?skin=iris\&bg=dusk\&size=46\&night=21-8\&nightdim=.4\&sleep=15\&sleepnight=5 > /dev/null 2>&1 < /dev/null &
