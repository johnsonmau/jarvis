#!/usr/bin/env python3
"""Follow-up listening for wyoming-satellite v1.4.1 (applied at image build).

After Jarvis finishes a spoken reply, keep the pipeline open for a few seconds
so the next sentence works without the wake word. While that window is open
the microphone is also still fed to the wake-word service, so "hey Jarvis"
keeps working. If nobody speaks, the window closes and the satellite goes back
to waiting for the wake word. Enabled with --follow-up-seconds N (0 = off).
"""
import sys, re
root = sys.argv[1] if len(sys.argv) > 1 else "/app"

def patch(path, pairs):
    s = open(path).read()
    for old, new in pairs:
        assert old in s, f"{path}: anchor not found: {old[:60]!r}"
        s = s.replace(old, new, 1)
    open(path, "w").write(s)
    print("patched", path)

# ---- settings: WakeSettings.follow_up_seconds --------------------------------
patch(f"{root}/wyoming_satellite/settings.py", [(
'''    refractory_seconds: Optional[float] = 5.0
    """Seconds after a wake word detection before another detection is handled."""
''',
'''    refractory_seconds: Optional[float] = 5.0
    """Seconds after a wake word detection before another detection is handled."""

    follow_up_seconds: Optional[float] = None
    """After a spoken reply, keep listening this many seconds without the wake word."""
''')])

# ---- CLI: --follow-up-seconds -------------------------------------------------
patch(f"{root}/wyoming_satellite/__main__.py", [(
'''    parser.add_argument(
        "--wake-refractory-seconds",
        type=float,
        default=5.0,
        help="Seconds after a wake word detection before another detection is handled (default: 5)",
    )
''',
'''    parser.add_argument(
        "--wake-refractory-seconds",
        type=float,
        default=5.0,
        help="Seconds after a wake word detection before another detection is handled (default: 5)",
    )
    parser.add_argument(
        "--follow-up-seconds",
        type=float,
        default=0.0,
        help="After a spoken reply, keep listening this many seconds without the wake word (default: 0 = off)",
    )
'''), (
'''            refractory_seconds=(
                args.wake_refractory_seconds
                if args.wake_refractory_seconds > 0
                else None
            ),
        ),
''',
'''            refractory_seconds=(
                args.wake_refractory_seconds
                if args.wake_refractory_seconds > 0
                else None
            ),
            follow_up_seconds=(
                args.follow_up_seconds if args.follow_up_seconds > 0 else None
            ),
        ),
''')])

# ---- satellite: WakeStreamingSatellite ----------------------------------------
patch(f"{root}/wyoming_satellite/satellite.py", [
# state
('''        super().__init__(settings)
        self.is_streaming = False

        # Timestamp in the future when the refractory period is over (set with
        # time.monotonic()).
        # wake word id -> seconds
        self.refractory_timestamp: Dict[Optional[str], float] = {}
''',
'''        super().__init__(settings)
        self.is_streaming = False

        # Timestamp in the future when the refractory period is over (set with
        # time.monotonic()).
        # wake word id -> seconds
        self.refractory_timestamp: Dict[Optional[str], float] = {}

        # Follow-up: after a reply, listen again without the wake word
        self._follow_up = False
        self._follow_up_task: Optional[asyncio.Task] = None
        self._reply_pending = False  # a transcript was handled; next TTS "played" ends a reply
        self._reply_pending_at = 0.0
'''),
# server events: track reply state, cancel the window when speech is found
('''        if RunSatellite.is_type(event.type):
            is_run_satellite = True
            self._is_paused = False

        elif PauseSatellite.is_type(event.type):
            is_pause_satellite = True
        elif Transcript.is_type(event.type):
            is_transcript = True
        elif Error.is_type(event.type):
            is_error = True

        if is_transcript or is_pause_satellite:
''',
'''        if RunSatellite.is_type(event.type):
            is_run_satellite = True
            self._is_paused = False

        elif PauseSatellite.is_type(event.type):
            is_pause_satellite = True
        elif Transcript.is_type(event.type):
            is_transcript = True
            self._reply_pending = True
            self._reply_pending_at = time.monotonic()
        elif Error.is_type(event.type):
            is_error = True
            self._reply_pending = False
        elif VoiceStarted.is_type(event.type) and self._follow_up:
            # Someone is talking inside the follow-up window: let the pipeline finish
            self._cancel_follow_up_timer()
            _LOGGER.debug("Follow-up: speech detected")

        if is_transcript or is_error or is_run_satellite or is_pause_satellite:
            self._cancel_follow_up_timer()
            self._follow_up = False

        if is_transcript or is_pause_satellite:
'''),
# mic: during follow-up also feed the wake word service
('''        if self.is_streaming:
            # Forward to server
            await self.event_to_server(event)
        else:
            # Forward to wake word service
            await self.event_to_wake(event)

    async def event_from_wake(self, event: Event) -> None:
        if Info.is_type(event.type):
            self._wake_info = Info.from_event(event)
            self._wake_info_ready.set()
            return

        if self.is_streaming or (self.server_id is None):
            # Not detecting or no server connected
            return
''',
'''        if self.is_streaming:
            # Forward to server
            await self.event_to_server(event)
            if self._follow_up:
                # ...and keep the wake word service listening during the follow-up window
                await self.event_to_wake(event)
        else:
            # Forward to wake word service
            await self.event_to_wake(event)

    # ---- follow-up window ----------------------------------------------------
    def _cancel_follow_up_timer(self) -> None:
        if self._follow_up_task is not None:
            self._follow_up_task.cancel()
            self._follow_up_task = None

    async def _start_follow_up(self, seconds: float) -> None:
        self._follow_up = True
        self.is_streaming = True
        _LOGGER.info("Follow-up: listening %.1f s without wake word", seconds)
        await self._send_run_pipeline()
        await self.trigger_streaming_start()
        self._cancel_follow_up_timer()
        self._follow_up_task = asyncio.create_task(self._follow_up_timeout(seconds))

    async def _follow_up_timeout(self, seconds: float) -> None:
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return
        if not (self._follow_up and self.is_streaming):
            return
        _LOGGER.info("Follow-up: no speech, back to wake word")
        await self._end_follow_up()

    async def _end_follow_up(self) -> None:
        """Close the follow-up window: tell the server to stop STT, resume wake detection."""
        self._follow_up = False
        self.is_streaming = False
        self._reply_pending = False
        await self.event_to_server(AudioStop().event())
        await self.trigger_streaming_stop()
        if not self._is_paused:
            await self._send_wake_detect()
            _LOGGER.info("Waiting for wake word")

    async def trigger_played(self) -> None:
        await super().trigger_played()
        seconds = self.settings.wake.follow_up_seconds
        if (not seconds) or (not self._reply_pending) or self._is_paused or (self.server_id is None):
            return
        if self.is_streaming:
            return
        if time.monotonic() - self._reply_pending_at > 60:
            self._reply_pending = False
            return
        self._reply_pending = False
        await self._start_follow_up(seconds)

    async def event_from_wake(self, event: Event) -> None:
        if Info.is_type(event.type):
            self._wake_info = Info.from_event(event)
            self._wake_info_ready.set()
            return

        if self.server_id is None:
            return

        if self.is_streaming and self._follow_up and Detection.is_type(event.type):
            # Wake word inside the follow-up window: start a fresh request
            _LOGGER.debug("Follow-up: wake word heard, restarting pipeline")
            self._cancel_follow_up_timer()
            await self._end_follow_up()
        elif self.is_streaming:
            # Not detecting
            return
'''),
])
print("follow-up patch applied")
