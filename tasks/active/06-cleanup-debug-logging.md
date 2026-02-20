# Task 06: Cleanup Debug Logging

**Priority:** MEDIUM
**Estimated effort:** Small (remove/adjust a few lines)
**Type:** Code cleanup

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo.

### Key File
- `scripts/dog_bark_detector.py` - Main detection script

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to pull and restart

---

## The Problem

The detector has debug logging that was added during troubleshooting and is now
too verbose for production use. It logs every 5 seconds and fills up journal/log files.

---

## Changes Required

### Change 1: Remove periodic debug classification logging

In `scripts/dog_bark_detector.py`, find this block (around line 830-833):

```python
                # Log top predictions periodically for debugging
                if predictions and int(time.time()) % 5 == 0:
                    top3 = predictions[:3]
                    top_str = ", ".join(f"{p['class']}:{p['confidence']:.3f}" for p in top3)
                    logger.info(f"[DEBUG] dB={decibels:.1f} top3=[{top_str}]")
```

**Replace with:**
```python
                # Log top predictions periodically (every 60 seconds) for monitoring
                if predictions and int(time.time()) % 60 == 0:
                    top3 = predictions[:3]
                    top_str = ", ".join(f"{p['class']}:{p['confidence']:.3f}" for p in top3)
                    logger.debug(f"dB={decibels:.1f} top3=[{top_str}]")
```

Changes:
- Frequency: every 5 seconds → every 60 seconds
- Level: `logger.info` → `logger.debug` (only visible when DEBUG level is enabled)
- Removed `[DEBUG]` prefix (the log level already indicates this)

### Change 2: Reduce silence re-alert frequency

Find the silence re-alert line (around line 788):

```python
                        elif int(silence_duration) % 300 == 0:
```

This is fine (every 5 minutes). No change needed here.

### Change 3: Reduce startup verbosity (optional)

The model loading logs input/output shapes which is useful for debugging but
not for production. Consider changing these from `info` to `debug`:

Around line 228-230:
```python
            logger.info(f"Model loaded successfully")
            logger.info(f"Input shape: {self.input_details[0]['shape']}")
            logger.info(f"Output shape: {self.output_details[0]['shape']}")
```

Change to:
```python
            logger.info(f"Model loaded successfully")
            logger.debug(f"Input shape: {self.input_details[0]['shape']}")
            logger.debug(f"Output shape: {self.output_details[0]['shape']}")
```

### Change 4: Change the comment about PulseAudio

The comment at line 60-62 says:
```python
# Use PulseAudio (default device) so both this detector and BirdNET can share
# the same loopback source. PulseAudio handles resampling from 48kHz to 16kHz.
AUDIO_DEVICE_INDEX = None  # None = PulseAudio default source (shared with BirdNET)
```

This is misleading because the detector actually auto-detects the ALSA loopback
device in `_find_audio_device()`. Update the comment:
```python
# Audio device selection: None = auto-detect ALSA loopback capture device
# The _find_audio_device() method will scan for hw:X,1 loopback or dsnoop device
AUDIO_DEVICE_INDEX = None  # None = auto-detect (see _find_audio_device)
```

---

## Verification

After committing and pushing:

```bash
cd ~/Air-quality-sensors && git pull && sudo systemctl restart dog_bark_detector && sleep 5 && sudo journalctl -u dog_bark_detector -n 20 --no-pager
```

You should see:
- Startup messages (model loaded, device detected, stream opened)
- No `[DEBUG]` lines flooding the log
- Bark detections still logged normally when they occur
- Silence warnings still appear if audio pipeline is dead

---

## When This Task Is Complete

```bash
git mv tasks/active/06-cleanup-debug-logging.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 06: cleaned up debug logging"
git push
```
