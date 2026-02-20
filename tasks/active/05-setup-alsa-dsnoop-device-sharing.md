# Task 05: Setup ALSA dsnoop for Shared Audio Device Access

**Priority:** MEDIUM
**Estimated effort:** Medium (new script + code change)
**Type:** Feature - enable both detectors to run simultaneously

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
iPhone 7 (Periscope HD) → RTSP → FFmpeg → ALSA loopback hw:X,0
                                                         ↓
                                          ALSA loopback hw:X,1 (capture)
                                                         ↓
                                               ┌─────────┴─────────┐
                                               ↓                   ↓
                                    Dog Bark Detector       BirdNET-Pi
                                      (PyAudio)           (PulseAudio)
```

### The Problem
The ALSA loopback capture device `hw:X,1` can only be opened by ONE application
at a time in exclusive mode. Currently:
- Dog bark detector uses PyAudio with direct ALSA `hw:X,1` access
- BirdNET uses PulseAudio which also tries to claim `hw:X,1`
- Only one can run at a time - BirdNET is currently STOPPED

### The Solution: ALSA dsnoop
`dsnoop` is an ALSA plugin that allows multiple applications to read from the
same capture device simultaneously (like `dmix` does for playback).

### Key Files
- `scripts/dog_bark_detector.py` - Needs to use dsnoop device instead of hw:X,1
- `scripts/setup_iphone_audio.sh` - May need to create dsnoop config
- New: `scripts/setup_audio_sharing.sh` - Script to configure dsnoop

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to deploy

---

## Implementation Plan

### Step 1: Create setup script `scripts/setup_audio_sharing.sh`

This script should:

1. Detect the ALSA loopback card number (parse `arecord -l` output)
2. Create `/etc/asound.conf` with a dsnoop device definition
3. Configure PulseAudio to use the dsnoop device as its source
4. Test that dsnoop works

The ALSA config (`/etc/asound.conf`) should contain:

```
# dsnoop device for shared access to loopback capture
pcm.dsnoop_loopback {
    type dsnoop
    ipc_key 82854
    ipc_perm 0666
    slave {
        pcm "hw:CARD_NUMBER,1"
        rate 16000
        channels 1
        format S16_LE
        period_size 1024
        buffer_size 8192
    }
}

pcm.loopback {
    type plug
    slave.pcm "dsnoop_loopback"
}
```

Replace CARD_NUMBER with the detected loopback card number.

The script must be run with `sudo` on the Pi. Make it idempotent (safe to run multiple times).
Back up any existing `/etc/asound.conf` before overwriting.

### Step 2: Update dog bark detector to use dsnoop

In `scripts/dog_bark_detector.py`, update `_find_audio_device()` to also look for
dsnoop devices in the PyAudio device list. The dsnoop device will appear as a named
device like "dsnoop_loopback" or "plug:loopback".

Add an environment variable override so the user can specify a device name:
```python
# At the top with other config
AUDIO_DEVICE_NAME = os.environ.get('AUDIO_DEVICE_NAME', None)
```

In `_find_audio_device()`, if `AUDIO_DEVICE_NAME` is set, search for a device
whose name contains that string. Otherwise, fall back to the existing loopback
auto-detection logic.

### Step 3: Configure PulseAudio for BirdNET

The setup script should also create a PulseAudio config that uses dsnoop_loopback
as its source. Create `~/.config/pulse/default.pa` for the Pi user with:

```
.include /etc/pulse/default.pa
load-module module-alsa-source device=dsnoop_loopback source_name=iphone_audio source_properties=device.description="iPhone_Microphone"
set-default-source iphone_audio
```

### Step 4: Update systemd service for dog bark detector

The dog bark detector service should set the environment variable:
```ini
Environment="PYTHONUNBUFFERED=1"
Environment="AUDIO_DEVICE_NAME=dsnoop_loopback"
```

---

## Verification

After deploying, give the user this command to test:

```bash
cd ~/Air-quality-sensors && git pull && \
sudo bash scripts/setup_audio_sharing.sh && \
sudo systemctl restart dog_bark_detector && \
sudo systemctl restart birdnet_recording && \
echo "Waiting 10s for services to start..." && sleep 10 && \
echo "=== Dog bark detector ===" && \
sudo journalctl -u dog_bark_detector -n 10 --no-pager && \
echo "" && \
echo "=== BirdNET recording ===" && \
sudo journalctl -u birdnet_recording -n 10 --no-pager && \
echo "" && \
echo "=== Both should be running ===" && \
systemctl is-active dog_bark_detector birdnet_recording
```

Both services should be "active" and both should show audio being processed
in their logs (not silence/errors).

---

## Important Notes

- The loopback card number can change across reboots. The setup script should
  detect it dynamically, not hardcode it.
- If `/etc/asound.conf` already exists, back it up before replacing.
- BirdNET's effectiveness is limited by the iPhone's 4kHz audio bandwidth
  (G.711 codec at 8kHz sample rate). Bird songs need 8-10kHz+. See task 08
  for alternatives. But getting dsnoop working is still valuable for when
  a USB microphone is added later.

---

## When This Task Is Complete

```bash
git mv tasks/active/05-setup-alsa-dsnoop-device-sharing.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 05: ALSA dsnoop device sharing configured"
git push
```
