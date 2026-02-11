# Dog Bark & Bird Detection - Troubleshooting Guide

This document contains solutions to common problems, historical issues that have been fixed, and maintenance procedures.

---

## Table of Contents

1. [Data Management & Storage](#data-management--storage)
2. [Service Issues](#service-issues)
3. [Audio Input Problems](#audio-input-problems)
4. [Home Assistant Dashboard Errors](#home-assistant-dashboard-errors)
5. [Database & History Management](#database--history-management)
6. [MQTT Issues](#mqtt-issues)
7. [Historical Problems (Fixed)](#historical-problems-fixed)
8. [Maintenance Procedures](#maintenance-procedures)

---

## Data Management & Storage

### Where is bark data stored?

The dog bark detector stores data in **4 locations**:

#### 1. CSV Event Logs (Complete History)
**Location:** `/home/demeter/audio_detection/data/`
- `bark_events_5min.csv` - Events grouped with 5-minute gaps
- `bark_events_10min.csv` - Events grouped with 10-minute gaps

**Format:**
```csv
date,start_time,end_time,duration_minutes,max_decibels,num_barks
2026-02-11,08:30:15,08:35:42,5.45,78.2,12
2026-02-11,09:15:20,09:22:10,6.83,82.1,18
```

**Growth Rate:** ~1-2 KB per day (negligible)

**Rotation:** Use `/home/demeter/Air-quality-sensors/scripts/rotate_csv_files.sh`

#### 2. Audio Recordings (MP3 Files)
**Location:**
- Primary: `/mnt/usb/bark_audio/recordings/YYYY/MM/DD/` (if USB mounted)
- Fallback: `/home/demeter/audio_detection/recordings/YYYY/MM/DD/`

**Format:** `bark_YYYY-MM-DD_HH-MM-SS.mp3` (32kbps, low quality)

**Growth Rate:** ~480 MB per day (assuming 4 hours of barking)

**Auto-Cleanup:** ✅ **Built-in!** Automatically deletes oldest files when storage exceeds 95%

#### 3. Log Files (Debugging)
**Location:** `/home/demeter/audio_detection/logs/`
- `dog_bark_detector_YYYYMMDD.log` - Daily log files

**Growth Rate:** ~5-10 MB per day

**Rotation:** Manually delete old logs or use logrotate

#### 4. Home Assistant Database (Dashboard Data)
**Location:** `/home/demeter/homeassistant/home-assistant_v2.db`

**Contains:** All sensor history, states, and statistics for dashboard

**Growth Rate:** Varies (HA has built-in purge settings)

**Management:** See [Database & History Management](#database--history-management)

---

### What happens when storage fills up?

#### Audio Recordings (Automatic ✅)
The dog bark detector has **built-in automatic cleanup**:

```python
# From dog_bark_detector.py lines 389-438
MAX_STORAGE_PERCENT = 95  # Trigger cleanup at 95% full
```

**How it works:**
1. Every 10 minutes, checks storage usage
2. If over 95%, deletes oldest MP3 files first
3. Continues until storage drops to 90%
4. Logs all deletions

**You don't need to do anything - this is automatic!**

#### CSV Files (Manual)
CSV files grow slowly (~1-2 KB/day) so they rarely cause problems, but you can rotate them:

```bash
# Keep last 90 days, archive the rest
~/Air-quality-sensors/scripts/rotate_csv_files.sh 90
```

#### Home Assistant Database
HA has built-in purge settings. To check:
```
Settings → System → Storage → Purge
```

Default: Keeps 10 days of history. You can extend this if desired.

---

### How to safely clear history

**IMPORTANT:** Never manually delete files without backing up first!

Use the safe script:
```bash
cd ~/Air-quality-sensors/scripts
bash safe_clear_history.sh
```

This script:
1. ✅ Creates automatic backups
2. ✅ Stops services safely
3. ✅ Clears CSV files
4. ✅ Clears HA database history
5. ✅ Optionally clears audio recordings
6. ✅ Restarts everything
7. ✅ Shows you how to restore

**Backup location:** `~/audio_detection/backups/backup_YYYYMMDD_HHMMSS/`

---

## Service Issues

### Dog bark detector not starting

**Check status:**
```bash
sudo systemctl status dog_bark_detector
```

#### Error: "Model not found"
**Symptom:** Service fails with error about missing model file

**Solution:**
```bash
# Check if model exists
ls -lh ~/audio_detection/models/

# Should show:
#   yamnet.tflite (4.1 MB)
#   yamnet_class_map.csv

# If missing, re-download:
cd ~/audio_detection/models
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/lite-model_yamnet_classification_tflite_1.tflite
mv lite-model_yamnet_classification_tflite_1.tflite yamnet.tflite
wget https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv

# Restart service
sudo systemctl restart dog_bark_detector
```

#### Error: "Cannot set tensor: Dimension mismatch"
**Symptom:**
```
Error: Dimension mismatch. Got 16000 but expected 15600
```

**Cause:** YAMNet TFLite model expects **exactly 15600 samples**, not 16000

**Solution:**
```bash
# Check CHUNK_SIZE in script
grep "CHUNK_SIZE = " ~/Air-quality-sensors/scripts/dog_bark_detector.py

# Should be:
CHUNK_SIZE = 15600  # NOT 16000!

# If wrong, edit the file and restart
sudo systemctl restart dog_bark_detector
```

#### Error: "Cannot open audio device"
**Symptom:** Service fails to open audio stream

**Solution:**
```bash
# List available audio devices
arecord -l

# Check if ALSA loopback is loaded
lsmod | grep snd_aloop

# If not loaded:
sudo modprobe snd-aloop
echo "snd-aloop" | sudo tee -a /etc/modules

# Restart service
sudo systemctl restart dog_bark_detector
```

#### Service keeps restarting
**Check logs:**
```bash
sudo journalctl -u dog_bark_detector -n 50 --no-pager
```

**Common causes:**
1. Audio device disconnected (iPhone stopped streaming)
2. MQTT broker not running
3. Python dependency missing
4. Permission error on recording directory

---

### BirdNET not detecting birds

**Check service:**
```bash
sudo systemctl status birdnet_recording
```

**Check configuration:**
1. Open BirdNET web interface: `http://192.168.68.109`
2. Settings → MQTT → Ensure enabled with broker `localhost:1883`
3. Settings → Audio → Verify audio source is correct

**Test MQTT publishing:**
```bash
mosquitto_sub -h localhost -t "birdnet/#" -v
```

If no messages appear when birds are chirping, BirdNET is not publishing to MQTT.

---

## Audio Input Problems

### Silence detection warnings

**Symptom:**
```
WARNING: SILENCE DETECTED: Audio stuck at 32 dB for 60s. No real audio is being captured!
```

**Meaning:** Microphone is "connected" but only receiving dead air/silence

**Common causes:**
1. iPhone Periscope HD app not running or stopped streaming
2. ALSA loopback loaded but no audio stream writing to it
3. `iphone-audio-stream.service` not running
4. Wrong audio device selected

**Solution:**
```bash
# Check if iPhone stream service is running
sudo systemctl status iphone-audio-stream

# If not running:
sudo systemctl start iphone-audio-stream

# Check iPhone Periscope HD app:
# - Open app on iPhone
# - Tap "Start" button
# - Verify "LIVE" indicator is red

# Check ALSA loopback:
sudo modprobe snd-aloop

# Test audio capture:
arecord -D hw:1,1 -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav  # Should hear audio from iPhone
```

### Microphone status shows "offline"

**Check in dashboard:** Sensor `binary_sensor.microphone_online`

**Debug:**
```bash
# Check detector logs for errors
sudo journalctl -u dog_bark_detector -f --no-pager

# Look for lines like:
#   "Microphone offline - no audio data for 30 seconds"

# Common causes:
# 1. Dog bark detector service not running
# 2. Audio device disconnected
# 3. iPhone stream stopped
```

---

## Home Assistant Dashboard Errors

### Orange warning triangles with "!"

**Symptom:** Dashboard cards show orange warning icon

**Common causes:**
1. Entity doesn't exist (sensor not created)
2. Syntax error in YAML
3. Custom card not installed (e.g., `custom:apexcharts-card`)

**Debug:**
```bash
# Check Home Assistant logs
docker logs homeassistant 2>&1 | grep -i "error\|warning" | tail -50

# Check configuration validity
docker exec homeassistant hass --script check_config

# Restart HA to reload config
docker restart homeassistant
```

### "Entity not found" or "unavailable"

**Symptom:** Dashboard shows "entity is currently unavailable"

**Debug:**
1. Check if entity exists:
   - HA Settings → Developer Tools → States
   - Search for the entity ID (e.g., `sensor.dog_bark_confidence`)

2. If entity doesn't exist:
```bash
# Check if MQTT topics are publishing
mosquitto_sub -h localhost -t "audio/#" -v

# If no messages, detector is not running:
sudo systemctl status dog_bark_detector

# If messages appear, MQTT sensor may not be configured:
# Edit ~/homeassistant/packages/audio_detection.yaml
# Restart HA: docker restart homeassistant
```

3. If entity exists but shows "unavailable":
   - MQTT topic stopped publishing
   - Service crashed or restarted
   - Check service logs

### ApexCharts cards not rendering

**Symptom:** Card shows `custom:apexcharts-card not found`

**Solution:**
1. Install ApexCharts frontend:
   - HA → Settings → Dashboards → Resources
   - Add new resource:
     - URL: `/hacsfiles/apexcharts-card/apexcharts-card.js`
     - Type: JavaScript Module

2. Or install via HACS:
   - HACS → Frontend → Search "ApexCharts" → Install

3. Restart Home Assistant:
```bash
docker restart homeassistant
```

---

## Database & History Management

### Clear sensor history in Home Assistant

**Why:** After fixing issues, you may have bad data in the dashboard

**Safe method (clears only bark sensors):**
```bash
# Clear states for bark sensors
docker exec homeassistant sqlite3 /config/home-assistant_v2.db \
  "DELETE FROM states WHERE entity_id LIKE 'sensor.%bark%' OR entity_id LIKE 'sensor.%decibel%';"

# Clear statistics
docker exec homeassistant sqlite3 /config/home-assistant_v2.db \
  "DELETE FROM statistics WHERE metadata_id IN (SELECT metadata_id FROM statistics_meta WHERE statistic_id LIKE '%bark%');"

# Restart HA
docker restart homeassistant
```

**SAFER method (use the script):**
```bash
cd ~/Air-quality-sensors/scripts
bash safe_clear_history.sh
```

### Reduce HA database size

**Check current size:**
```bash
du -h ~/homeassistant/home-assistant_v2.db
```

**Purge old data:**
1. HA → Settings → System → Storage
2. Change "Purge settings" to keep fewer days (default: 10 days)
3. Click "Purge database"

---

## MQTT Issues

### MQTT topics not receiving data

**Test MQTT broker:**
```bash
# Subscribe to all audio topics
mosquitto_sub -h localhost -t "audio/#" -v

# Should see messages like:
#   audio/decibels {"decibels": 45.2}
#   audio/dog_bark {"detected": true, "confidence": 0.87, ...}
```

**If no messages:**
1. Check detector is running: `sudo systemctl status dog_bark_detector`
2. Check MQTT broker is running in HA
3. Check detector logs: `sudo journalctl -u dog_bark_detector -n 20`

### MQTT integration not showing sensors

**Reload MQTT integration:**
1. HA → Settings → Devices & Services
2. Find "MQTT" integration
3. Click ⋮ (three dots) → Reload

---

## Historical Problems (Fixed)

This section documents issues that were encountered during setup and how they were resolved. These are **already fixed** in the current code.

### ✅ FIXED: Service hardcoded for wrong user
**Problem:** Service files had hardcoded `/home/pi/` paths but user is `demeter`

**Solution:** Updated `scripts/create_services.sh` to auto-detect username
```bash
# Now uses:
USER=$(whoami)
HOME_DIR=$(eval echo ~$USER)
```

**Files modified:** `scripts/create_services.sh`

**When fixed:** 2026-01-15

---

### ✅ FIXED: TensorFlow version incompatibility
**Problem:** TensorFlow 2.13.0 had `imp` module deprecation error

**Error:**
```
AttributeError: module 'imp' is deprecated
```

**Solution:** Upgraded to TensorFlow 2.20.0 and flatbuffers 24.3.25

**Files modified:** `requirements.txt`

**When fixed:** 2026-01-20

---

### ✅ FIXED: Model input shape mismatch
**Problem:** YAMNet TFLite expects 15600 samples, but code used 16000

**Error:**
```
Error: Dimension mismatch. Got 16000 but expected 15600
```

**Solution:** Changed `CHUNK_SIZE = 16000` to `CHUNK_SIZE = 15600`

**Files modified:** `scripts/dog_bark_detector.py` line 65

**When fixed:** 2026-01-22

---

### ✅ FIXED: USB mount permission errors
**Problem:** Service crashed if `/mnt/usb` didn't exist or wasn't writable

**Solution:** Added fallback logic to use local directory

```python
def get_recording_dir():
    if os.path.exists("/mnt/usb") and os.access("/mnt/usb", os.W_OK):
        return USB_MOUNT_PATH
    return LOCAL_RECORDING_PATH
```

**Files modified:** `scripts/dog_bark_detector.py` lines 117-126

**When fixed:** 2026-01-25

---

### ✅ FIXED: Deprecated Home Assistant template syntax
**Problem:** Used old `platform: template` syntax (deprecated in HA 2026.6+)

**Warning:**
```
Defining templates under `template:` is deprecated and will be removed in 2026.12
```

**Solution:** Converted all sensors to modern `template:` block format

**Files modified:** `homeassistant/packages/audio_detection.yaml`

**When fixed:** 2026-02-01

---

### ✅ FIXED: MQTT JSON serialization error for numpy types
**Problem:** MQTT publish failed when sending numpy.float32 values

**Error:**
```
TypeError: Object of type float32 is not JSON serializable
```

**Solution:** Added custom JSON encoder to handle numpy types

```python
@staticmethod
def _convert_numpy(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    # ... etc
```

**Files modified:** `scripts/dog_bark_detector.py` lines 532-541

**When fixed:** 2026-02-05

---

## Maintenance Procedures

### Daily Checks (Optional)

```bash
# Quick health check
sudo systemctl status dog_bark_detector birdnet_recording --no-pager

# Check if MQTT is flowing
timeout 5 mosquitto_sub -h localhost -t "audio/#" -v

# Check recent errors
sudo journalctl -u dog_bark_detector --since today | grep -i error
```

### Weekly Maintenance

```bash
# Rotate CSV files (keep last 90 days)
~/Air-quality-sensors/scripts/rotate_csv_files.sh 90

# Check storage usage
df -h /mnt/usb  # or wherever recordings are stored

# Check service logs for anomalies
sudo journalctl -u dog_bark_detector --since "7 days ago" | grep -i warning
```

### Monthly Maintenance

```bash
# Backup important data
cp -r ~/audio_detection/data ~/audio_detection/backups/data_$(date +%Y%m%d)

# Clean up old backups (keep last 3 months)
find ~/audio_detection/backups -type d -mtime +90 -exec rm -rf {} \;

# Check HA database size
du -h ~/homeassistant/home-assistant_v2.db

# Purge old HA data if needed (Settings → System → Storage)
```

### Before Making Changes

**Always:**
1. Create a backup first
2. Stop the service: `sudo systemctl stop dog_bark_detector`
3. Make changes
4. Test manually: `python3 ~/Air-quality-sensors/scripts/dog_bark_detector.py`
5. If works, restart service: `sudo systemctl start dog_bark_detector`
6. Check logs: `sudo journalctl -u dog_bark_detector -f`

---

## Getting Help

### Log Files to Check

```bash
# Dog bark detector logs
sudo journalctl -u dog_bark_detector -n 100 --no-pager

# Home Assistant logs
docker logs homeassistant 2>&1 | tail -100

# BirdNET logs
sudo journalctl -u birdnet_recording -n 100 --no-pager

# System logs
sudo journalctl -n 100 --no-pager
```

### Diagnostic Information to Collect

When asking for help, provide:

```bash
# System info
uname -a
df -h

# Service status
sudo systemctl status dog_bark_detector birdnet_recording --no-pager

# Recent errors
sudo journalctl -u dog_bark_detector --since "1 hour ago" | grep -i error

# MQTT test
timeout 5 mosquitto_sub -h localhost -t "audio/#" -v

# Audio devices
arecord -l

# Python version
python3 --version

# TensorFlow version
python3 -c "import tensorflow as tf; print(tf.__version__)"
```

---

## Quick Reference

### Important File Locations

```
/home/demeter/Air-quality-sensors/           # Git repo
├── scripts/dog_bark_detector.py             # Main service
├── scripts/safe_clear_history.sh            # Safe history clear
├── scripts/rotate_csv_files.sh              # CSV rotation
├── homeassistant/packages/                  # HA sensor configs
└── docs/TROUBLESHOOTING.md                  # This file

/home/demeter/audio_detection/               # Runtime data
├── models/                                  # TensorFlow models
├── data/bark_events_*.csv                   # CSV logs
├── logs/                                    # Debug logs
├── recordings/                              # Audio (local)
└── backups/                                 # Backups

/mnt/usb/bark_audio/recordings/              # Audio (USB)

/home/demeter/homeassistant/                 # Home Assistant
├── configuration.yaml                       # Main config
├── packages/audio_detection.yaml            # Audio sensors
├── dashboards/home-test.yaml                # Dashboard
└── home-assistant_v2.db                     # Database

/etc/systemd/system/
├── dog_bark_detector.service                # Systemd service
└── birdnet_recording.service                # BirdNET service
```

### Common Commands

```bash
# Service management
sudo systemctl status dog_bark_detector
sudo systemctl restart dog_bark_detector
sudo systemctl stop dog_bark_detector
sudo journalctl -u dog_bark_detector -f

# Home Assistant
docker restart homeassistant
docker logs homeassistant

# MQTT testing
mosquitto_sub -h localhost -t "audio/#" -v

# Audio testing
arecord -D hw:1,1 -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav

# Storage check
df -h /mnt/usb
du -sh ~/audio_detection/recordings
```

---

**Last Updated:** 2026-02-11
