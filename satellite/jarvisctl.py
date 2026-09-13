#!/usr/bin/env python3
"""jarvis-ctl: tiny LAN-only HTTP control for the Jarvis satellite.

  GET  /volume                 -> {"volume": 20}
  POST /volume?set=35          -> set Jarvis's own output volume (0-100)
  POST /volume?delta=-10       -> nudge it
  GET  /health

"volume" is a linear percent (20 = the old fixed multiplier). It is stored in
/data/volume and converted to a PulseAudio volume in /data/pa, which the
satellite's snd.sh passes to paplay for every reply. Nothing else on the shared
PulseAudio sink (MPD, alarms) is touched.
"""
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DATA = "/data"
DEFAULT = 20

def read_volume():
    try:
        return max(0, min(100, int(open(os.path.join(DATA, "volume")).read().strip())))
    except Exception:
        return DEFAULT

def write_volume(v):
    v = max(0, min(100, int(round(v))))
    pa = int(round(65536 * ((v / 100.0) ** (1 / 3)))) if v > 0 else 0
    os.makedirs(DATA, exist_ok=True)
    for name, val in (("volume", v), ("pa", pa)):
        tmp = os.path.join(DATA, name + ".tmp")
        with open(tmp, "w") as f:
            f.write(str(val))
        os.replace(tmp, os.path.join(DATA, name))
    return v

class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/volume":
            return self._json(200, {"volume": read_volume()})
        if u.path == "/health":
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "unknown path"})

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path != "/volume":
            return self._json(404, {"error": "unknown path"})
        try:
            if "set" in q:
                v = write_volume(float(q["set"][0]))
            elif "delta" in q:
                v = write_volume(read_volume() + float(q["delta"][0]))
            else:
                return self._json(400, {"error": "use ?set=N or ?delta=N"})
        except ValueError:
            return self._json(400, {"error": "not a number"})
        print(f"jarvis-ctl: volume -> {v}", flush=True)
        return self._json(200, {"volume": v})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    write_volume(read_volume())  # make sure /data/pa exists on first start
    print("jarvis-ctl listening on :10710, volume", read_volume(), flush=True)
    ThreadingHTTPServer(("0.0.0.0", 10710), H).serve_forever()
