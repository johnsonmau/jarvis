#!/usr/bin/env python3
"""Applied after patch_followup.py: cap how many times the follow-up window can
re-open after one wake word (FOLLOW_UP_MAX_ROUNDS, default 2). Without this,
any speech-like noise inside the window keeps the conversation going forever."""
import sys
root = sys.argv[1] if len(sys.argv) > 1 else "/app"
p = f"{root}/wyoming_satellite/satellite.py"
s = open(p).read()
def rep(old, new, count=1):
    global s
    assert old in s, "anchor not found: " + old[:60]
    s = s.replace(old, new, count)
if "import os" not in s.split("\n\n")[0] + s[:2000]:
    rep("import asyncio\n", "import asyncio\nimport os\n")
rep("        self._reply_pending_at = 0.0\n",
    "        self._reply_pending_at = 0.0\n"
    "        self._follow_up_rounds = 0\n"
    "        self._follow_up_max = int(os.environ.get(\"FOLLOW_UP_MAX_ROUNDS\", \"2\"))\n")
rep("        self._reply_pending = False\n        await self._start_follow_up(seconds)\n",
    "        self._reply_pending = False\n"
    "        if self._follow_up_rounds >= self._follow_up_max:\n"
    "            _LOGGER.debug(\"Follow-up: max rounds reached, back to wake word\")\n"
    "            return\n"
    "        self._follow_up_rounds += 1\n"
    "        await self._start_follow_up(seconds)\n")
# a real wake word starts a fresh budget
rep("        if Detection.is_type(event.type):\n",
    "        if Detection.is_type(event.type):\n            self._follow_up_rounds = 0\n")
open(p, "w").write(s)
print("follow-up limit patch applied")
