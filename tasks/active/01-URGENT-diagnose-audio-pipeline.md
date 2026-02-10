# Task 01: URGENT - Diagnose Audio Pipeline Status

**Priority:** CRITICAL
**Estimated effort:** Small (diagnostic only, no code changes)
**Type:** Diagnostic - gather information and report findings

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
iPhone 7 (Periscope HD RTSP) → FFmpeg → ALSA loopback (snd-aloop) → PyAudio → Dog Bark Detector → MQTT → Home Assistant
```

### Key Details
- ALSA loopback kernel module `snd-aloop` creates virtual audio device pairs
- FFmpeg writes RTSP audio to `hw:X,0` (playback side)
- Dog bark detector reads from `hw:X,1` (capture side) via PyAudio
- MQTT broker (Mosquitto) runs on localhost port 1883
- When audio pipeline is broken, detector reads silence = constant 30 dB
- The loopback card number can change across reboots (was card 3 previously)

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible - minimize the number of steps
- The user is not a Linux expert - explain what things mean
- Be concise

---

## Problem

The dog bark detector is showing a constant 30 dB reading with no real detections.
This suggests the audio pipeline may be broken (no real audio reaching the detector).
We need to diagnose the full pipeline to find where audio is being lost.

## Your Task

**This is a diagnostic task. Do NOT make code changes.**

Create a SINGLE combined diagnostic command for the user to run on their Pi via SSH.
This command should check ALL of the following at once:

1. Is `snd-aloop` kernel module loaded?
2. What ALSA capture devices exist? (`arecord -l`)
3. Is the `iphone-audio-stream` service running?
4. Is the `dog_bark_detector` service running?
5. What are the last 20 log lines from each service?
6. Is FFmpeg actually writing audio to the loopback? (quick 2-second capture test)
7. Is Mosquitto running?
8. What's the current value on the MQTT decibels topic?

### Diagnostic Command Template

Give the user ONE command block like this:

```bash
echo "=== 1. KERNEL MODULE ===" && \
lsmod | grep snd_aloop && echo "snd-aloop: LOADED" || echo "snd-aloop: NOT LOADED" && \
echo "" && \
echo "=== 2. ALSA DEVICES ===" && \
arecord -l 2>&1 && \
echo "" && \
echo "=== 3. SERVICES ===" && \
systemctl is-active iphone-audio-stream dog_bark_detector mosquitto 2>&1 && \
echo "" && \
echo "=== 4. IPHONE STREAM LOGS ===" && \
sudo journalctl -u iphone-audio-stream -n 10 --no-pager 2>&1 && \
echo "" && \
echo "=== 5. DETECTOR LOGS ===" && \
sudo journalctl -u dog_bark_detector -n 20 --no-pager 2>&1 && \
echo "" && \
echo "=== 6. AUDIO TEST (2 sec) ===" && \
CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p') && \
if [ -n "$CARD" ]; then \
  timeout 4 arecord -D "hw:$CARD,1" -f S16_LE -r 16000 -c 1 -d 2 /tmp/diag_test.wav 2>&1 && \
  python3 -c "
import wave, struct
w = wave.open('/tmp/diag_test.wav','r')
frames = w.readframes(w.getnframes())
samples = [abs(struct.unpack('<h',frames[i:i+2])[0]) for i in range(0,min(len(frames),64000),2)]
peak = max(samples) if samples else 0
rms = (sum(s*s for s in samples)/len(samples))**0.5 if samples else 0
print(f'Peak: {peak}, RMS: {rms:.0f}')
if peak < 10: print('RESULT: SILENCE - no audio flowing')
else: print('RESULT: AUDIO IS FLOWING')
" 2>&1 && rm -f /tmp/diag_test.wav; \
else echo "No loopback device found - cannot test"; fi && \
echo "" && \
echo "=== 7. MQTT CHECK ===" && \
timeout 3 mosquitto_sub -t "audio/decibels" -C 1 2>&1 || echo "No MQTT message received in 3s"
```

## After Getting Results

Analyze the output and report:
1. Which parts of the pipeline are working and which are broken
2. What specific fix is needed (but don't implement it - just describe it)
3. Whether other task documents in `tasks/active/` are relevant

## When This Task Is Complete

Once you have diagnosed the issue and reported findings to the user, run:

```bash
git mv tasks/active/01-URGENT-diagnose-audio-pipeline.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 01: audio pipeline diagnosis complete"
git push
```

Then tell the user which task document to tackle next based on your findings.
