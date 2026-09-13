"""Restore the owner's original alias lists (registry backup 20260913-115556), fixing the one real
problem: 'office light' was an alias on BOTH office lights, so Assist reported duplicates. Each list
gets a leading null (= the entity's own name) so renaming never breaks matching. Run with HA STOPPED."""
import json, shutil, time
p = "/config/.storage/core.entity_registry"
shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
d = json.load(open(p))
FINAL = {
    "light.office": ("Office Overhead", ['office overhead', 'office overhead light', 'office main light', 'office ceiling light', 'office ceiling', 'big office light', 'office light', 'overhead light']),
    "light.office_lamp": ("Office Lamp", ['office lamp', 'desk lamp', 'office desk lamp', 'lamp in the office', 'office table lamp', 'small office light']),
    "light.living_room": ("Living Room Overhead", ['living room overhead', 'living room overhead light', 'living room main light', 'living room ceiling light', 'living room ceiling', 'living room light', 'front room light', 'family room light', 'living room lights']),
    "media_player.bedroom_tv": (None, ['bedroom tv', 'bedroom television', 'tv in the bedroom']),
    "media_player.living_room_tv": (None, ['living room tv', 'living room television', 'tv in the living room', 'big tv', 'main tv', 'tv']),
    "media_player.music_player_daemon": ("Office Speaker", ['office speaker', 'jarvis speaker', 'speaker', 'music player', 'office music', 'mpd']),
    "light.outside_lights": (None, ['outside lights', 'outdoor lights', 'porch lights', 'exterior lights', 'outside light', 'yard lights', 'front and back lights']),
}
for e in d["data"]["entities"]:
    if e["entity_id"] in FINAL:
        name, aliases = FINAL[e["entity_id"]]
        if name is not None or e.get("name"): e["name"] = name
        e["aliases"] = list(aliases)
        e["aliases_v2"] = [None, *aliases]
        print(e["entity_id"], "name=", e.get("name"), "aliases:", len(aliases))
json.dump(d, open(p, "w"), indent=2)
