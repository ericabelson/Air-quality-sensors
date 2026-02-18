# Task 07: Add Boot Resilience for Audio Pipeline

**Priority:** LOW-MEDIUM
**Estimated effort:** Medium (new script + service adjustments)
**Type:** Reliability improvement

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
Boot sequence needed:
1. snd-aloop kernel module loads (from /etc/modules)
2. ALSA loopback device appears (hw:X,0 and hw:X,1)
3. iphone-audio-stream.service starts FFmpeg → writes to hw:X,0
4. dog_bark_detector.service starts → reads from hw:X,1
5. (Optional) BirdNET recording starts → reads from dsnoop or PulseAudio
```

### Key Problem
After a reboot:
- `snd-aloop` loads from `/etc/modules` but the card number may change
- The iphone-audio-stream service has a HARDCODED device `hw:3,0` but after
  reboot it might be `hw:1,0` or `hw:2,0`
- The dog bark detector auto-detects the loopback card, so it adapts
- But if FFmpeg is writing to the wrong device, there's no audio

### Key Files
- `scripts/create_services.sh` - Creates systemd service files
- `scripts/setup_iphone_audio.sh` - Sets up the audio stream
- `/etc/modules` on Pi - Contains `snd-aloop` for persistent loading

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to deploy

---

## Implementation Plan

### Step 1: Create a startup helper script `scripts/audio_startup.sh`

This script runs at boot (as a oneshot systemd service) BEFORE the other audio
services. It:

1. Verifies `snd-aloop` is loaded (loads it if not)
2. Detects the loopback card number
3. Writes the card number to a file: `/run/audio_loopback_card`
4. Optionally creates/updates the ALSA dsnoop config with correct card number

```bash
#!/bin/bash
# audio_startup.sh - Detect loopback device at boot and configure audio pipeline
set -e

# Ensure snd-aloop is loaded
if ! lsmod | grep -q snd_aloop; then
    modprobe snd-aloop
    sleep 2
fi

# Detect loopback card number
CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
if [ -z "$CARD" ]; then
    echo "ERROR: No loopback device found" >&2
    exit 1
fi

echo "$CARD" > /run/audio_loopback_card
echo "Loopback device detected as card $CARD"
```

### Step 2: Update iphone-audio-stream service to use dynamic card number

Instead of hardcoding `hw:3,0`, the service should read from `/run/audio_loopback_card`.

One approach: create a wrapper script `scripts/start_iphone_stream.sh` that reads the
card number and launches FFmpeg:

```bash
#!/bin/bash
# start_iphone_stream.sh - Launch FFmpeg with dynamically detected loopback device
CARD=$(cat /run/audio_loopback_card 2>/dev/null)
if [ -z "$CARD" ]; then
    echo "ERROR: /run/audio_loopback_card not found. Is audio_startup.service running?" >&2
    exit 1
fi

IPHONE_IP="${IPHONE_IP:-192.168.68.116}"
RTSP_PORT="${RTSP_PORT:-8554}"

exec /usr/bin/ffmpeg \
    -rtsp_transport udp \
    -i "rtsp://${IPHONE_IP}:${RTSP_PORT}/live.sdp" \
    -vn \
    -acodec pcm_s16le \
    -ar 16000 \
    -ac 1 \
    -f alsa \
    "hw:${CARD},0"
```

**Note about iPhone IP:** The script uses an environment variable `IPHONE_IP` with
a default. The user should verify their iPhone's IP address hasn't changed. On first
setup, ask the user:

```bash
echo "What is your iPhone's IP address? (Check iPhone > Settings > Wi-Fi > tap network)"
```

The service file should pass the IP as an environment variable:
```ini
Environment="IPHONE_IP=192.168.68.116"
```

### Step 3: Create audio_startup.service (oneshot, runs before others)

Update `scripts/create_services.sh` to create this service:

```ini
[Unit]
Description=Audio Pipeline Startup (detect loopback device)
After=sound.target
Before=iphone-audio-stream.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/path/to/scripts/audio_startup.sh

[Install]
WantedBy=multi-user.target
```

### Step 4: Update service dependencies

The iphone-audio-stream.service should depend on audio_startup.service:
```ini
[Unit]
After=network.target audio_startup.service
Requires=audio_startup.service
```

The dog_bark_detector.service already depends on iphone-audio-stream:
```ini
[Unit]
After=network.target mosquitto.service iphone-audio-stream.service
Wants=mosquitto.service iphone-audio-stream.service
```

---

## First: Gather Information

Before implementing, have the user run this on the Pi to understand the current state:

```bash
echo "=== Current services ===" && \
systemctl list-unit-files | grep -E "iphone|dog_bark|birdnet|audio" && \
echo "" && \
echo "=== Current iphone-audio-stream service ===" && \
sudo systemctl cat iphone-audio-stream 2>&1 && \
echo "" && \
echo "=== Current dog_bark_detector service ===" && \
sudo systemctl cat dog_bark_detector 2>&1 && \
echo "" && \
echo "=== /etc/modules ===" && \
cat /etc/modules && \
echo "" && \
echo "=== Current loopback card ===" && \
arecord -l 2>/dev/null | grep -i loopback
```

Use this output to inform the exact paths and configuration in your implementation.

---

## Verification

After deploying, simulate a reboot test:

```bash
cd ~/Air-quality-sensors && git pull && \
sudo bash scripts/audio_startup.sh && \
cat /run/audio_loopback_card && \
echo "Card number above should match 'arecord -l' output" && \
arecord -l | grep -i loopback
```

A full reboot test:
```bash
sudo reboot
# After reconnecting via SSH:
systemctl is-active audio_startup iphone-audio-stream dog_bark_detector && \
cat /run/audio_loopback_card && \
timeout 5 mosquitto_sub -t "audio/decibels" -C 2 -v
```

---

## When This Task Is Complete

```bash
git mv tasks/active/07-add-boot-resilience.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 07: boot resilience for audio pipeline"
git push
```
