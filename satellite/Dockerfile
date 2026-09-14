# Wyoming satellite for the USB condenser mic. Replaces the T5AI board: same
# pipeline, no firmware to hang. Runs on 192.168.0.229. Plays TTS through the
# host's system PulseAudio (paplay over TCP), the same sink MPD uses.
FROM python:3.11-slim-bookworm
ENV LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends alsa-utils git \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN git clone --depth 1 --branch v1.4.1 https://github.com/rhasspy/wyoming-satellite.git . \
 && script/setup \
 && (.venv/bin/pip install -e ".[all]" || echo "optional VAD/noise extras skipped")
RUN apt-get update && apt-get install -y --no-install-recommends pulseaudio-utils \
 && rm -rf /var/lib/apt/lists/*
COPY reply.py /reply.py
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*
COPY play.sh /app/play.sh
# Follow-up listening after a reply (see patch_followup.py)
COPY patch_followup.py /tmp/patch_followup.py
RUN python3 /tmp/patch_followup.py /app
COPY patch_followup_limit.py /tmp/patch_followup_limit.py
RUN python3 /tmp/patch_followup_limit.py /app
EXPOSE 10700
ENTRYPOINT ["/app/script/run", "--uri", "tcp://0.0.0.0:10700", "--no-zeroconf"]
