# Task 02: URGENT - Fix Binary Sensor Stuck Permanently ON

**Priority:** CRITICAL
**Estimated effort:** Small (two targeted changes)
**Type:** Bug fix - code change + HA config change

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
```
Dog Bark Detector (Python) → MQTT topics → Home Assistant sensors/binary_sensors
```

### Key Files in This Repo
- `scripts/dog_bark_detector.py` - Main detection script (lines 838-846 are the bark detection publish)
- `homeassistant/packages/audio_detection.yaml` - HA sensor definitions (lines 131-140 are the binary sensor)

### MQTT Topics
- `audio/dog_bark` - Bark detection events. Payload: `{"timestamp": "...", "detected": true/false, "confidence": 0.87, "decibels": 72.5, "class": "Bark"}`

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to pull and restart

---

## The Bug

The HA binary sensor `binary_sensor.dog_barking` is **stuck permanently ON** after the
first bark detection. The 72-hour barking timeline shows dogs "detected currently and
unceasingly" even though the sound level is at 30 dB (silence).

### Root Cause

In `scripts/dog_bark_detector.py`, the `audio/dog_bark` topic is ONLY published when
a bark IS detected (line 846):

```python
if is_bark:
    # ... creates event ...
    self.mqtt.publish_bark_event(event, True, class_name)  # Always True!
```

The code NEVER publishes `detected: false`. So once the HA binary sensor receives
`detected: true`, it stays ON forever because no OFF message ever arrives.

The HA binary sensor config (audio_detection.yaml line 131-140):
```yaml
binary_sensor:
  - name: "Dog Barking"
    state_topic: "audio/dog_bark"
    value_template: "{{ value_json.detected }}"
    payload_on: true
    payload_off: false
    device_class: sound
```

No `off_delay` is configured, so it waits for an explicit `detected: false` that never comes.

---

## Fix Required (Two Changes)

### Change 1: Add `off_delay` to HA binary sensor config

**File:** `homeassistant/packages/audio_detection.yaml`

Find the binary_sensor definition (around line 131-140) and add `off_delay: 30`:

```yaml
  binary_sensor:
    # Dog Barking Status (Binary)
    - name: "Dog Barking"
      unique_id: dog_barking
      state_topic: "audio/dog_bark"
      value_template: "{{ value_json.detected }}"
      payload_on: true
      payload_off: false
      device_class: sound
      icon: mdi:dog
      off_delay: 30
```

This makes the binary sensor automatically turn OFF 30 seconds after the last
`detected: true` message, even without an explicit `detected: false`.

### Change 2: Add bark cooldown to publish `detected: false` in Python

**File:** `scripts/dog_bark_detector.py`

This ensures the MQTT topic itself shows the correct state for any consumers.

**Step 2a:** Add a cooldown constant near line 68 (after DOG_BARK_CONFIDENCE_THRESHOLD):

```python
DOG_BARK_CONFIDENCE_THRESHOLD = 0.25  # Lowered from 0.70 for debugging - raise after testing
BARK_COOLDOWN_SECONDS = 30  # Publish "not barking" after this many seconds of no bark
```

**Step 2b:** Add tracking flag in `__init__` (around line 632, after `self.last_bark_decibels = 0`):

```python
        self.last_bark_decibels = 0
        self.bark_active = False  # True when actively barking, False after cooldown
```

**Step 2c:** In the `_detection_loop` method, AFTER the bark check block (after the
`if is_bark:` block ends, around line 857), add the cooldown logic:

```python
                if is_bark:
                    self.bark_active = True
                    # ... existing bark handling code ...

                # Bark cooldown - publish "not barking" when barking stops
                elif self.bark_active and self.last_bark_time:
                    time_since_bark = (datetime.now() - self.last_bark_time).total_seconds()
                    if time_since_bark > BARK_COOLDOWN_SECONDS:
                        self.bark_active = False
                        self.mqtt.publish(MQTT_TOPIC_BARK, {
                            'timestamp': datetime.now().isoformat(),
                            'detected': False,
                            'confidence': 0.0,
                            'decibels': float(decibels),
                            'class': ''
                        })
                        logger.info("Bark cooldown: published 'not barking' state")
```

Make sure the `elif` replaces the bare continuation after the `if is_bark:` block.
The key is: `if is_bark: [handle bark] elif self.bark_active: [check cooldown]`

Also set `self.bark_active = True` at the START of the `if is_bark:` block (before existing code).

---

## Verification

After committing and pushing, give the user this single command:

```bash
cd ~/Air-quality-sensors && git pull && sudo systemctl restart dog_bark_detector && echo "Restarted. Waiting 10s..." && sleep 10 && sudo journalctl -u dog_bark_detector -n 15 --no-pager && echo "" && echo "=== MQTT bark topic (wait 35s for cooldown test) ===" && timeout 40 mosquitto_sub -t "audio/dog_bark" -v
```

This will show:
1. The detector restarting with new code
2. After ~35 seconds with no bark, a `detected: false` message should appear on MQTT
3. The HA binary sensor should turn OFF within 30 seconds of no barking

The user should also check their HA dashboard to confirm `binary_sensor.dog_barking`
shows OFF/quiet after the fix.

**Note:** The HA YAML change requires reloading HA's MQTT integration. Tell the user:
```
In Home Assistant: Settings → Devices & Services → MQTT → Reload
Or restart Home Assistant entirely.
```

---

## When This Task Is Complete

```bash
git mv tasks/active/02-URGENT-fix-binary-sensor-stuck-on.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 02: fixed binary sensor stuck ON"
git push
```
