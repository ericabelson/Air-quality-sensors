# BirdNET-Pi Investigation Results
**Date:** 2026-02-11
**System:** Raspberry Pi 4 at 192.168.68.109 (user: demeter)

---

## Executive Summary

**Finding:** BirdNET-Pi is **NOT installed** on the Raspberry Pi.

**Root Cause:** The installation script (`scripts/install_birdnet.sh`) was created in the repository but never executed on the actual Raspberry Pi.

**Audio Limitation:** The current iPhone 7 + Periscope HD setup streams audio at 8kHz (G.711 codec), limiting frequency range to 4kHz maximum. Most bird songs are 2-10kHz, so BirdNET detection will be significantly limited.

---

## Investigation Results

### Services Checked
```bash
❌ birdnet_recording service - Not found
❌ birdnet_analysis service - Not found
❌ birdnet service - Not found
❌ No BirdNET processes running
```

### Directories Checked
```bash
❌ /home/demeter/BirdNET-Pi/ - Does not exist
❌ /home/demeter/BirdSongs/ - Does not exist
❌ /usr/local/birdnet/ - Does not exist
❌ No BirdNET Python modules installed
```

### What EXISTS in Repository
```bash
✅ scripts/install_birdnet.sh - Installation script (never run)
✅ homeassistant/packages/audio_detection.yaml - HA config (ready)
✅ docs/DOG_BARK_BIRD_DETECTION_GUIDE.md - Documentation
✅ tasks/active/08-investigate-bird-detection.md - Task notes
```

---

## Audio Bandwidth Limitation

### Current Setup
- **Device:** iPhone 7 running Periscope HD
- **Codec:** G.711 PCMU
- **Sample Rate:** 8000 Hz
- **Maximum Frequency:** 4000 Hz (Nyquist limit)

### Bird Song Frequencies
- **Most birds:** 2000-10000 Hz
- **Many songbirds:** Primarily above 4000 Hz
- **Result:** Majority of birds will NOT be detected

### Birds That WILL Be Detected
✅ Crows, ravens (low frequency calls)
✅ Pigeons, doves (cooing sounds)
✅ Owls (hooting)
✅ Some large waterfowl

### Birds That WON'T Be Detected
❌ Warblers, sparrows, finches (high-pitched songs)
❌ Most songbirds
❌ Any birds vocalizing above 4kHz

---

## Options for Moving Forward

### Option 1: Install with Current iPhone Setup (Limited)

**Command to run on Pi:**
```bash
cd /home/demeter/Air-quality-sensors/scripts
chmod +x install_birdnet.sh
./install_birdnet.sh
```

**Expected time:** 30-60 minutes

**Post-install configuration:**
```bash
nano ~/BirdNET-Pi/birdnet.conf

# Recommended settings for limited audio:
CONFIDENCE=0.80          # Higher threshold (reduce false positives)
SENSITIVITY=1.50         # Higher sensitivity (compensate for poor audio)
CHANNELS=1               # Mono
MQTT_ENABLED=1
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=birdnet
```

**Pros:**
- No additional hardware
- Will detect some birds
- Test the concept

**Cons:**
- Limited bird detection
- Lower accuracy
- Frequent false positives

---

### Option 2: USB Microphone (RECOMMENDED)

**Hardware needed:**
- USB microphone with 44.1kHz+ sample rate
- Cost: $15-30

**Recommended models:**
- Blue Snowball Ice (~$45, excellent)
- Generic USB conference mic (~$20)
- Any USB mic with 44.1kHz support

**Pros:**
- Full audio bandwidth (22kHz+)
- Detects ALL bird species
- Better accuracy
- Improves dog bark detection too

**Cons:**
- Requires hardware purchase
- Audio setup reconfiguration needed

**Architecture:**
```
USB Mic → ALSA device → dsnoop (sharing) → BirdNET + Dog Bark Detector
iPhone → Retired or backup
```

---

### Option 3: Try Different iPhone App

Some RTSP streaming apps may support AAC codec at 44.1kHz instead of G.711 at 8kHz.

**Apps to investigate:**
- IPCamera
- Larix Broadcaster
- Periscope HD Pro (if it has better codec options)

---

## Verification Commands (After Installation)

### Check Services
```bash
sudo systemctl status birdnet_recording
sudo systemctl status birdnet_analysis
```

### Check Web Interface
```
http://192.168.68.109
```

### Monitor MQTT Messages
```bash
mosquitto_sub -h localhost -t "birdnet/#" -v
```

### View Logs
```bash
sudo journalctl -u birdnet_analysis -f
tail -f ~/BirdNET-Pi/birdnet.log
```

### Test Detection
1. Play bird call on YouTube (e.g., "robin bird call")
2. Hold iPhone near speaker
3. Wait 10-20 seconds
4. Check web interface for detection

---

## Current System Status

### Working Components ✅
- iPhone audio streaming (RTSP via Periscope HD)
- ALSA loopback device configured
- Dog bark detector functional (proves audio input works)
- MQTT broker running (Mosquitto in Home Assistant)
- Home Assistant ready to receive bird data

### Not Working Components ❌
- BirdNET-Pi (not installed)
- Bird detection (no software to perform it)
- Bird MQTT topics (no publisher)
- BirdNET web interface (doesn't exist yet)

---

## Recommended Action Plan

### Immediate Term (Test Concept)
1. Run installation script on Pi
2. Configure for 8kHz audio limitation
3. Test for 1 week
4. See what birds (if any) are detected

### Long Term (Full Capability)
1. Purchase USB microphone ($20-30)
2. Reconfigure audio input
3. Reinstall/reconfigure BirdNET
4. Enjoy full bird detection capability

### Hybrid Approach
1. Install BirdNET now with current setup
2. If you like it, upgrade to USB mic later
3. Keep iPhone as backup microphone

---

## Why Dog Bark Detector Works But Bird Detection Won't

**Dog Bark Detector:**
- Dog barks are broadband (wide frequency range)
- Significant energy below 4kHz
- YAMNet model trained on varied audio quality
- ✅ Works fine with 8kHz audio

**Bird Detection:**
- Bird songs are narrowband (specific frequencies)
- Most energy above 4kHz
- BirdNET relies on high-frequency harmonics
- ❌ Severely limited by 8kHz audio

---

## References

- **Installation script:** `scripts/install_birdnet.sh`
- **Task documentation:** `tasks/active/08-investigate-bird-detection.md`
- **HA configuration:** `homeassistant/packages/audio_detection.yaml`
- **Setup guide:** `docs/DOG_BARK_BIRD_DETECTION_GUIDE.md`
- **BirdNET-Pi GitHub:** https://github.com/mcguirepr89/BirdNET-Pi

---

## Questions?

Contact information or create an issue in the repository.

**Investigation completed:** 2026-02-11
**Investigator:** Claude Code
