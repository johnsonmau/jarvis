"""Add Assist aliases so spoken names match (run with Home Assistant STOPPED)."""
import json, shutil, time
p = "/config/.storage/core.entity_registry"
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
d = json.load(open(p))
ALIASES = {
    "light.office":                 ["Office Light", "Office Lights", "Office Overhead Light", "Overhead Light"],
    "light.office_lamp":            ["Lamp", "Desk Lamp", "Office Desk Lamp"],
    "light.living_room":            ["Living Room Light", "Living Room Lights", "Living Room Overhead Light"],
    "media_player.bedroom_tv":      ["Bedroom TV", "Bedroom T V", "Bedroom Television", "TV in the bedroom"],
    "media_player.living_room_tv":  ["Living Room TV", "Living Room T V", "Living Room Television", "TV in the living room", "the TV"],
    "media_player.music_player_daemon": ["Office Speaker", "Speaker", "Music"],
    "light.outside_lights":         ["Outside Lights", "Outdoor Lights", "Porch Lights"],
}
n = 0
for e in d["data"]["entities"]:
    if e["entity_id"] in ALIASES:
        cur = list(e.get("aliases") or [])
        for a in ALIASES[e["entity_id"]]:
            if a not in cur: cur.append(a); n += 1
        e["aliases"] = cur
json.dump(d, open(p, "w"), indent=2)
print("aliases added:", n)
