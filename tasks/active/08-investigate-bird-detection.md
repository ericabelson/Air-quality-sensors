# Task 08: Investigate and Fix Bird Detection

**Priority:** LOW
**Estimated effort:** Research + recommendation (mostly investigation)
**Type:** Research and planning

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
iPhone 7 (Periscope HD) → RTSP (G.711 PCMU codec) → FFmpeg → ALSA loopback → BirdNET-Pi
```

### The Fundamental Problem
The iPhone 7 running Periscope HD streams audio using the **G.711 PCMU codec at 8000 Hz**.
This means the maximum audio frequency that can be captured is **4000 Hz** (Nyquist limit).

Most bird songs and calls are in the **2000-10000 Hz range**, with many species singing
primarily above 4000 Hz. This means:
- BirdNET can only detect birds that vocalize below 4kHz
- Many common songbirds (warblers, sparrows, finches) will be missed entirely
- Even detectable species will have degraded accuracy due to missing harmonics

### BirdNET-Pi Setup
- BirdNET-Pi is installed at `/home/demeter/BirdNET-Pi/` on the Pi
- Config file: `/home/demeter/BirdNET-Pi/birdnet.conf`
- Uses PulseAudio for audio input
- Currently STOPPED (to free the ALSA device for dog bark detector)
- Was producing only low-confidence detections ("Brahminy Kite 0.015", "Human 0.0")

### Key Files in Repo
- `homeassistant/packages/audio_detection.yaml` - HA sensor definitions for bird detection
- `homeassistant/automations/audio_alerts.yaml` - Bird alert automations

### User Preferences
- The user was very frustrated that this limitation wasn't mentioned earlier
- Be upfront about what will and won't work
- **Combine as many commands as possible** into single copy-paste blocks

---

## Research Tasks

### Task A: Verify Current BirdNET Status

First, gather diagnostic information. Give the user this command:

```bash
echo "=== BirdNET service status ===" && \
systemctl is-active birdnet_recording birdnet_analysis 2>&1 && \
echo "" && \
echo "=== BirdNET config ===" && \
cat ~/BirdNET-Pi/birdnet.conf 2>&1 && \
echo "" && \
echo "=== Recent BirdNET detections ===" && \
ls -la ~/BirdNET-Pi/BirdSongs/ 2>/dev/null | tail -5 && \
echo "" && \
echo "=== BirdNET analysis log (last 20 lines) ===" && \
sudo journalctl -u birdnet_analysis -n 20 --no-pager 2>&1 && \
echo "" && \
echo "=== Audio frequency test ===" && \
echo "Recording 3 seconds of audio for frequency analysis..." && \
CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p') && \
if [ -n "$CARD" ]; then \
  timeout 5 arecord -D "hw:$CARD,1" -f S16_LE -r 16000 -c 1 -d 3 /tmp/freq_test.wav 2>/dev/null && \
  python3 -c "
import numpy as np
from scipy.io import wavfile
rate, data = wavfile.read('/tmp/freq_test.wav')
fft = np.fft.rfft(data.astype(float))
freqs = np.fft.rfftfreq(len(data), 1/rate)
magnitudes = np.abs(fft)
# Find the highest frequency with significant energy
threshold = np.max(magnitudes) * 0.01
max_freq = freqs[magnitudes > threshold][-1] if any(magnitudes > threshold) else 0
print(f'Sample rate: {rate} Hz')
print(f'Max frequency with energy: {max_freq:.0f} Hz')
print(f'Nyquist limit: {rate/2:.0f} Hz')
if max_freq < 4500:
    print('CONFIRMED: Audio bandwidth limited to ~4kHz (G.711 codec)')
    print('This is insufficient for most bird song detection')
else:
    print(f'Audio bandwidth appears to extend to {max_freq:.0f} Hz')
" 2>&1 && rm -f /tmp/freq_test.wav; \
else echo "No loopback device found"; fi
```

### Task B: Research Alternatives

Based on the diagnostic results, evaluate these options:

#### Option 1: USB Microphone (Recommended)
- A USB microphone connected directly to the Pi would capture full audio bandwidth
- Typical USB mics support 44.1kHz or 48kHz sample rate (22kHz+ frequency range)
- BirdNET would work properly with a USB mic
- The dog bark detector could also benefit from higher quality audio
- Cost: $10-30 for a basic USB microphone
- **Recommendation for user:** Search for "USB microphone Raspberry Pi" - even
  a cheap USB conference microphone would be a massive improvement

The setup would be:
```
USB Mic → ALSA USB device → PulseAudio → BirdNET-Pi
iPhone (keep for dog bark) → RTSP → ALSA loopback → Dog Bark Detector
```

Or if the USB mic is good enough for both:
```
USB Mic → dsnoop/PulseAudio → Both BirdNET + Dog Bark Detector
iPhone → retired or backup
```

#### Option 2: Different iPhone Streaming App
- Some RTSP streaming apps may support higher-quality codecs (AAC, PCM)
- If an app can stream at 44.1kHz AAC, bird detection would work
- Research: Does Periscope HD support AAC or higher sample rates?
- Alternative apps: IPCamera, LarixBroadcaster, etc.

#### Option 3: Accept the Limitation
- Some birds vocalize below 4kHz (crows, ravens, pigeons, doves, owls)
- BirdNET might still detect these low-frequency birds
- Accuracy will be lower but not zero
- Configure BirdNET with higher confidence threshold to reduce false positives

### Task C: If Keeping BirdNET with Current Setup

Update BirdNET config for the best possible results with limited audio:

```bash
# In ~/BirdNET-Pi/birdnet.conf, recommend:
CONFIDENCE=0.80    # Higher threshold to reduce false positives
SENSITIVITY=1.50   # Higher sensitivity to compensate for poor audio
CHANNELS=1         # Mono (loopback is mono)
```

Also ensure BirdNET MQTT publishing is configured (check if there's a custom
script or if BirdNET-Pi has built-in MQTT support).

---

## Deliverable

After researching, provide the user with:

1. **A clear honest summary** of what will and won't work with the current setup
2. **A recommendation** (likely: get a USB microphone for bird detection)
3. **If USB mic recommended:** A short list of compatible affordable options
4. **Immediate steps** to make the best of the current setup (BirdNET config tweaks)

Be direct and honest about limitations. The user was previously frustrated by
not being told about this limitation upfront.

---

## When This Task Is Complete

```bash
git mv tasks/active/08-investigate-bird-detection.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 08: bird detection investigation complete"
git push
```
