#!/usr/bin/env python3
"""Runs for every spoken reply (wyoming-satellite --synthesize-command).
The satellite pipes the reply text to stdin (an argument also works). Post it to
the Home Assistant webhook that speaks it on MPD (see ha_reply_automation.yaml)."""
import json, os, sys, urllib.request
text = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
url = os.environ.get("REPLY_WEBHOOK", "http://192.168.0.229:8123/api/webhook/t5ai_reply")
if text:
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:  # never crash the satellite over a missed reply
        print("reply webhook failed:", e, file=sys.stderr)
