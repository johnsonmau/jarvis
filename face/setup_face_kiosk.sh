#!/bin/bash
# Run this ON THE PI (192.168.0.226), as the pi's normal login user.
# It installs face.html as a fullscreen Chromium kiosk that starts on boot and
# shows the voice-assistant face driven by Home Assistant.
#
#   1) copy face.html to this Pi first (see the steps the assistant gave you)
#   2) bash setup_face_kiosk.sh
set -e

FACE="$HOME/face.html"
TOKEN=""                                # leave blank: face.html already carries the token. Set only to override it.
HA="192.168.0.229"
ENTITY="assist_satellite.usb_mic"          # the USB-mic satellite from docker-compose.yml
SKIN="iris"                             # beam / ring / iris / capsule  (preview: face.html?demo)
BG="dusk"                               # void / slate / dusk
NIGHT="21-8"                            # dim the face between these hours (24h), blank to disable
NIGHTDIM=".4"                           # brightness during the night window, 0.1 - 1
SIZE="46"                               # eye size, percent of the short screen edge

[ -f "$FACE" ] || { echo "face.html not found at $FACE - copy it here first."; exit 1; }

# pick whichever chromium this Pi OS has
BROWSER="$(command -v chromium-browser || command -v chromium)"
[ -n "$BROWSER" ] || { echo "Chromium not found. Run: sudo apt install -y chromium-browser"; exit 1; }

URL="file://$FACE?ha=$HA&entity=$ENTITY&skin=$SKIN&bg=$BG&night=$NIGHT&nightdim=$NIGHTDIM&size=$SIZE"
[ -n "$TOKEN" ] && URL="$URL&token=$TOKEN"

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/face.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Homelab Face
Exec=$BROWSER --kiosk --noerrdialogs --disable-infobars --incognito --disable-session-crashed-bubble --check-for-update-interval=31536000 "$URL"
X-GNOME-Autostart-enabled=true
EOF

# stop the screen from blanking (best-effort across X and Wayland Pi OS)
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/noblank.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=No Blank
Exec=sh -c "xset s off; xset -dpms; xset s noblank"
EOF

echo "Installed. Test it now without rebooting:"
echo "  $BROWSER --kiosk \"$URL\""
echo "Then reboot to confirm it starts on boot:  sudo reboot"
echo "Exit kiosk with Ctrl+W or Alt+F4; edit settings in ~/.config/autostart/face.desktop"
