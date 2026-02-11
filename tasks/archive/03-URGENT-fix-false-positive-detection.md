# Task 03: URGENT - Fix False Positive Bark Detection

**Priority:** CRITICAL
**Estimated effort:** Small (targeted code changes)
**Type:** Bug fix - adjust detection parameters

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
iPhone 7 (Periscope HD) → RTSP → FFmpeg → ALSA loopback → PyAudio → YAMNet TFLite model → MQTT → HA
```

### Key Details
- YAMNet is a general audio classifier with 521 classes (not dog-specific)
- Audio source is iPhone 7 using G.711 codec (8kHz sample rate, 4kHz max frequency)
- This limited audio quality means the model has degraded accuracy
- FFmpeg resamples from 8kHz to 16kHz for the detector
- When audio pipeline is silent, readings are constant 30 dB (MIN_DB floor)

### Key File
- `scripts/dog_bark_detector.py` - Lines 68-78 define detection thresholds and class names

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to pull and restart

---

## The Bug

The bark detector is producing false positive detections because:

1. **Confidence threshold is 0.25** (set for debugging, way too low for production)
2. **"Animal" is in the class list** - this is an extremely generic YAMNet class that
   matches all kinds of ambient audio, not just dogs
3. **No minimum dB filter** - the model classifies even silence (30 dB), and random
   noise patterns in silence can produce "Animal: 0.26" which exceeds the 0.25 threshold

A real bark was detected at confidence 0.26 for class "Animal" - this is indistinguishable
from a false positive.

---

## Fix Required (Three Changes)

All changes are in `scripts/dog_bark_detector.py`.

### Change 1: Remove overly generic classes from detection list

Find the `DOG_BARK_CLASS_NAMES` list (around line 69-78):

**Before:**
```python
DOG_BARK_CLASS_NAMES = [
    "Animal",
    "Domestic animals, pets",
    "Dog",
    "Bark",
    "Bow-wow",
    "Growling",
    "Whimper",
    "Howl"
]
```

**After:**
```python
DOG_BARK_CLASS_NAMES = [
    "Dog",
    "Bark",
    "Bow-wow",
    "Growling",
    "Whimper",
    "Howl",
    "Domestic animals, pets",
]
```

Remove "Animal" entirely. It's a parent category in YAMNet's ontology and matches
far too many non-dog sounds. Keep "Domestic animals, pets" but it will require the
higher threshold (see Change 2).

### Change 2: Raise confidence threshold

Find the threshold line (around line 68):

**Before:**
```python
DOG_BARK_CONFIDENCE_THRESHOLD = 0.25  # Lowered from 0.70 for debugging - raise after testing
```

**After:**
```python
DOG_BARK_CONFIDENCE_THRESHOLD = 0.40  # Balanced for iPhone audio quality (8kHz G.711)
```

Why 0.40: The iPhone's 8kHz G.711 codec degrades audio quality significantly, so
YAMNet confidence scores are lower than with a proper microphone. 0.70 (the original)
would miss most real barks. 0.40 balances sensitivity with false positive reduction.
The user can adjust this from the HA dashboard via `input_number.bark_sensitivity`.

### Change 3: Add minimum dB filter before classification

In the `_detection_loop` method, find the line that runs classification
(around line 827):

**Before:**
```python
                # Classify audio
                predictions = self.classifier.classify_audio(audio_data)
```

**After:**
```python
                # Skip classification if audio is too quiet (likely silence/no input)
                MIN_CLASSIFY_DB = 35
                if decibels <= MIN_CLASSIFY_DB:
                    predictions = []
                else:
                    # Classify audio
                    predictions = self.classifier.classify_audio(audio_data)
```

This prevents the model from classifying silence/near-silence, which eliminates
false positives when the audio pipeline is dead or the environment is very quiet.
35 dB is slightly above the 30 dB silence floor and 32 dB silence threshold.

---

## Verification

After committing and pushing, give the user this single command:

```bash
cd ~/Air-quality-sensors && git pull && sudo systemctl restart dog_bark_detector && echo "Restarted. Watching for 30 seconds..." && timeout 30 sudo journalctl -u dog_bark_detector -f --no-pager 2>&1 | head -50
```

What to look for:
- If audio is silent (30 dB), there should be NO "[DEBUG]" classification lines
  (because we skip classification below 35 dB)
- If audio is flowing, classifications should appear but "Animal" should NOT
  trigger bark detections
- Any bark detection that DOES appear should have confidence >= 0.40

If the user wants to test with actual dog barking, they can play dog bark sounds
near the iPhone and watch for detections.

---

## When This Task Is Complete

```bash
git mv tasks/active/03-URGENT-fix-false-positive-detection.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 03: fixed false positive bark detection"
git push
```
