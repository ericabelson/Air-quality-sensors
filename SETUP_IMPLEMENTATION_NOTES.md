# Dog Bark & Bird Detection Setup - Implementation Notes

## Overview
This document captures critical information about the dog bark and bird detection integration with Home Assistant on a Raspberry Pi. Use this when troubleshooting or continuing development.

---

## System Architecture

### Hardware
- **Raspberry Pi 4** (2GB+ RAM) running Raspberry Pi OS
- **Home Assistant** running in Docker
- **iPhone 7** with Periscope HD app streaming audio via RTSP
- **Audio Input**: ALSA loopback device (captures RTSP stream from iPhone)

### Software Components
1. **Dog Bark Detector** - Custom Python service using TensorFlow Lite + YAMNet model
2. **BirdNET-Pi** - Third-party bird detection system
3. **Home Assistant** - Automation platform with MQTT integration
4. **MQTT Broker** (Mosquitto) - Message broker for sensor data

---

## File Locations on Raspberry Pi

### Critical Paths
```
/home/demeter/homeassistant/              # Home Assistant Docker mount point
├── configuration.yaml                     # Main HA config
├── packages/
│   └── audio_detection.yaml              # Audio detection sensors & templates
├── dashboards/
│   └── audio_detection_dashboard.yaml    # Standalone audio dashboard (not used in current setup)
│   └── home-test.yaml                    # Main dashboard with dog/bird sections
└── automations/
    └── audio_alerts.yaml                 # HA automations (not yet implemented)

/home/demeter/Air-quality-sensors/        # Git repository (clone of ericabelson/Air-quality-sensors)
├── scripts/
│   ├── dog_bark_detector.py             # Main dog bark detection service
│   ├── install_birdnet.sh                # BirdNET-Pi installer (already run)
│   └── create_services.sh                # Systemd service file generator
├── homeassistant/
│   ├── packages/audio_detection.yaml     # Source of truth for sensor definitions
│   └── dashboards/audio_detection_dashboard.yaml
└── docs/
    └── DOG_BARK_BIRD_DETECTION_GUIDE.md # Implementation guide

/home/demeter/audio_detection/            # Dog bark detector storage
├── models/
│   ├── yamnet.tflite                     # TensorFlow Lite model (4.1 MB)
│   └── yamnet_class_map.csv              # Model class labels
├── logs/                                 # Debug logs for detector
├── data/                                 # CSV event logs
└── recordings/                           # Local fallback for bark audio clips

/home/demeter/BirdSongs/                  # BirdNET-Pi storage
└── StreamData/                           # Bird detection recordings

/etc/systemd/system/
├── dog_bark_detector.service             # Dog detector systemd service
├── birdnet_recording.service             # BirdNET recording systemd service
└── (other HA services)
```

---

## Key Configuration Details

### User & Permissions
- **SSH User**: `demeter`
- **Docker Container User**: `root` (inside container runs as root)
- **Service User**: `demeter`
- **Note**: Packages installed with `sudo pip3 install --break-system-packages` are visible to all users

### Network & MQTT
- **MQTT Broker**: `localhost:1883` (Mosquitto, part of HA installation)
- **MQTT Topics Published**:
  - `audio/dog_bark` - Real-time bark detections
  - `audio/decibels` - Current sound level (every ~1 second)
  - `audio/detector_status` - Detector online/offline status
  - `audio/bark_stats` - Daily statistics
  - `audio/last_detection` - Last bark time (updated every 60 seconds)
  - `audio/microphone_status` - Audio input health
  - `birdnet/detection` - Bird species detections (from BirdNET-Pi)
  - `birdnet/stats` - Bird daily statistics

### Audio Input
- **iPhone RTSP URL**: `rtsp://192.168.68.116:8554/live.sdp` (set in Periscope HD app)
- **Audio Device**: ALSA loopback (device index varies, usually `hw:1,0` or `hw:1,1`)
- **Streaming Service**: `iphone-audio-stream.service` (if using RTSP capture)
- **Note**: Current setup may use direct audio input from default device

### Storage
- **Dog Bark Recordings**:
  - Primary: `/mnt/usb/bark_audio/recordings/` (if USB mounted)
  - Fallback: `/home/demeter/audio_detection/recordings/` (if USB not available)
- **Recording Format**: MP3 (32kbps, ~480MB per day with 4 hours of barking)
- **Auto-cleanup**: Enabled if storage exceeds 95% capacity

---

## TensorFlow & YAMNet Model Details

### Critical: Input Shape Requirement
- **Model**: `lite-model_yamnet_classification_tflite_1.tflite`
- **Expected Input**: 1D audio tensor of **exactly 15600 samples**
- **Sample Rate**: 16000 Hz (mono)
- **Duration**: ~0.975 seconds per inference
- **Chunk Size Config**: `CHUNK_SIZE = 15600` (line 63 of dog_bark_detector.py)

### Common Input Shape Errors
```
Error: Dimension mismatch. Got 16000 but expected 15600
```
**Solution**: Ensure CHUNK_SIZE is set to 15600, not 16000

### Model Loading
```python
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
```
- Model must be loaded before starting detection loop
- If model not found, detector exits with error
- Models stored at: `/home/demeter/audio_detection/models/`

---

## Home Assistant Integration

### Sensor Types
The `audio_detection.yaml` package creates:
1. **MQTT Sensors** - Raw data from detector
   - `sensor.audio_decibels`
   - `sensor.dog_bark_confidence`
   - `sensor.dog_bark_class`
   - `sensor.total_barks_today`
   - `sensor.max_decibels_today`
   - `sensor.latest_bird_species`
   - `sensor.bird_confidence`
   - etc.

2. **MQTT Binary Sensors** - State indicators
   - `binary_sensor.dog_barking` (on/off)
   - `binary_sensor.microphone_online` (connectivity)

3. **Template Sensors** - Calculated/derived values
   - `sensor.bark_minutes_per_hour`
   - `sensor.decibel_status` (Quiet/Moderate/Loud/Very Loud)
   - `sensor.bark_event_status` (🔴 BARKING NOW / ✅ Quiet)
   - `sensor.quiet_streak` (time since last bark)

4. **History Stats Sensors** - Time-based aggregation
   - `sensor.barking_time_today`
   - `sensor.barking_time_last_hour`
   - `sensor.barking_percentage_today`

### Template Syntax Evolution
- **DEPRECATED** (pre-2026.6): `platform: template` with `sensors:` block
- **MODERN** (2026.6+): `template:` block with `- sensor:` list
- **Location**: `audio_detection.yaml` lines 156-222
- **If getting deprecation warnings**: Ensure using modern syntax with `unique_id`, `name`, `icon`, `state` keys

### Dashboard Integration
- **Type**: Lovelace YAML dashboard
- **Location**: `/home/demeter/homeassistant/dashboards/home-test.yaml`
- **Custom Cards Used**: `custom:apexcharts-card` (requires ApexCharts frontend)
- **Sections**:
  - Dog Barking Monitor (24-72 hour timeline with red bands)
  - Bird Detection (last 20 species, 7-day trends)

---

## Common Issues & Solutions

### Issue 1: Configuration Errors in Dashboard
**Symptom**: Orange warning triangles with ! in Home Assistant dashboard
**Likely Causes**:
1. Entity doesn't exist (sensor not created yet)
2. MQTT topics not receiving data
3. Deprecated YAML syntax
4. Typo in entity ID

**Debugging Steps**:
```bash
# 1. Check if entities exist in HA
# Settings → Developer Tools → States
# Search for entities starting with "sensor.dog_bark", "sensor.bird", etc.

# 2. Verify MQTT topics are receiving data
mosquitto_sub -h localhost -t "audio/#" -v
mosquitto_sub -h localhost -t "birdnet/#" -v

# 3. Check detector is running
sudo systemctl status dog_bark_detector

# 4. Check detector logs
sudo journalctl -u dog_bark_detector -n 50 --no-pager
```

### Issue 2: Entity Not Found Errors
**Symptom**: Dashboard shows "entity is currently unavailable"
**Likely Causes**:
1. MQTT topics not publishing (detector not running, MQTT not connected)
2. Entity ID mismatch in dashboard YAML
3. BirdNET-Pi not configured for MQTT

**Debugging**:
```bash
# Check detector status
sudo systemctl status dog_bark_detector birdnet_recording --no-pager

# Check MQTT logs
docker logs homeassistant 2>&1 | grep -i mqtt

# Check if entities are being created
# Home Assistant Settings → Devices & Services → MQTT → Configured
```

### Issue 3: Dog Bark Detector Not Starting
**Common Errors**:
- `Model not found` - Models not downloaded to `/home/demeter/audio_detection/models/`
- `Cannot set tensor: Dimension mismatch` - Wrong CHUNK_SIZE (must be 15600)
- `Cannot open audio device` - No audio input available
- `Permission denied: /mnt/usb` - USB mount doesn't exist (should fallback to local)

**Solution Steps**:
```bash
# 1. Verify models exist
ls -lah /home/demeter/audio_detection/models/

# 2. Check CHUNK_SIZE in script
grep "CHUNK_SIZE = " ~/Air-quality-sensors/scripts/dog_bark_detector.py

# 3. Check service configuration
cat /etc/systemd/system/dog_bark_detector.service

# 4. Review detector logs
sudo journalctl -u dog_bark_detector -n 100 --no-pager | grep -i error
```

### Issue 4: ApexCharts Cards Not Rendering
**Symptom**: Cards show "custom:apexcharts-card not found"
**Solution**: Install ApexCharts frontend add-on in Home Assistant
```
Home Assistant → Settings → Add-ons → Create add-on repository → apexcharts-card
```

---

## Service Management

### Systemd Services
```bash
# Check status
sudo systemctl status dog_bark_detector
sudo systemctl status birdnet_recording
sudo systemctl status homeassistant  # (if applicable)

# Restart
sudo systemctl restart dog_bark_detector
sudo systemctl restart birdnet_recording

# View logs
sudo journalctl -u dog_bark_detector -n 50 --no-pager
sudo journalctl -u birdnet_recording -n 50 --no-pager

# Enable auto-start on boot
sudo systemctl enable dog_bark_detector
sudo systemctl enable birdnet_recording
```

### Service Configuration Files
- **Dog Bark Detector**: `/etc/systemd/system/dog_bark_detector.service`
  - User: `demeter`
  - Working Directory: `/home/demeter/Air-quality-sensors`
  - ExecStart: `/usr/bin/python3 /home/demeter/Air-quality-sensors/scripts/dog_bark_detector.py`
  - Restart: `always` (auto-restarts on failure, wait 10 seconds between attempts)

- **BirdNET Recording**: `/etc/systemd/system/birdnet_recording.service`
  - Similar structure, runs BirdNET recording script

---

## Git Repository Structure

### Branch for Development
- **Current Branch**: `claude/ha-dog-bark-bird-detection-SFB7v`
- **Main Branch**: `main` (stable)
- **Remote**: GitHub (`ericabelson/Air-quality-sensors`)

### Key Directories
```
homeassistant/
├── packages/
│   └── audio_detection.yaml          # ✅ Source of truth for HA sensors
├── dashboards/
│   ├── audio_detection_dashboard.yaml # (Standalone, not integrated)
│   └── (home-test.yaml is not in repo, created locally)
└── automations/
    └── audio_alerts.yaml              # (Not yet implemented)

scripts/
├── dog_bark_detector.py              # ✅ Main service script (WORKING)
├── install_birdnet.sh                # ✅ Already run on Pi
├── create_services.sh                # ✅ Already run on Pi
└── csv_exporter.py                   # (Not yet integrated)

docs/
├── DOG_BARK_BIRD_DETECTION_GUIDE.md  # ✅ Complete implementation guide
└── (other setup guides)
```

### Files to Push Before Closing Session
- `homeassistant/packages/audio_detection.yaml` (YAML syntax fixes)
- `scripts/dog_bark_detector.py` (model input fixes)
- `SETUP_IMPLEMENTATION_NOTES.md` (this file)
- `NEXT_INSTANCE_PROMPT.md` (prompt for next Claude Code session)

---

## Dependencies & Versions

### Python Packages
```
tensorflow==2.20.0          # Was 2.13.0, upgraded for compatibility
tensorflow-lite             # Included with tensorflow
librosa==0.10.1
soundfile==0.12.1
pyaudio==0.2.13
pydub==0.25.1
scipy==1.11.3
paho-mqtt==1.6.1            # MQTT client
numpy==1.24.3
flatbuffers==24.3.25        # Upgraded from old version to fix 'imp' module error
```

### System Packages
```
libatlas-base-dev           # Audio processing (optional with newer TensorFlow)
portaudio19-dev
python3-pyaudio
ffmpeg                      # For RTSP stream capture and audio conversion
sox, libsox-fmt-all         # Audio processing
alsa-utils                  # ALSA audio configuration
```

### Home Assistant Add-ons/Integrations
- **MQTT**: Enabled (default in HA)
- **ApexCharts**: Required for chart visualization
- **Template Engine**: Built-in
- **History Stats**: Built-in

---

## Debugging Tips for Next Instance

### Quick Health Check
```bash
# 1. Verify both services running
sudo systemctl status dog_bark_detector birdnet_recording --no-pager

# 2. Check MQTT data flowing
mosquitto_sub -h localhost -t "audio/#" -v &
mosquitto_sub -h localhost -t "birdnet/#" -v &

# 3. Check Home Assistant sees entities
docker exec homeassistant hass --script check_config

# 4. Check for recent errors
sudo journalctl -u dog_bark_detector -n 20 --no-pager | grep ERROR
```

### Enable Debug Logging
Edit `/home/demeter/Air-quality-sensors/scripts/dog_bark_detector.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

### Common Commands
```bash
# Pull latest changes
cd ~/Air-quality-sensors && git pull origin main

# Restart detector after code changes
sudo systemctl restart dog_bark_detector

# View detector logs in real-time
sudo journalctl -u dog_bark_detector -f --no-pager

# Monitor MQTT traffic
mosquitto_sub -h localhost -t "audio/#" -v

# SSH into Pi from any machine
ssh demeter@192.168.68.109
```

---

## What Works
✅ Dog bark detector running continuously
✅ BirdNET recording running continuously
✅ MQTT sensors created in Home Assistant
✅ Audio input via iPhone/Periscope working
✅ TensorFlow model loading and inferencing
✅ Recording directory with USB fallback
✅ MQTT topic publishing functional

## What Needs Work
❌ Dashboard entity rendering (some configuration errors)
❌ Bird species list not populating last 20 detections
❌ ApexCharts cards may need custom apexcharts-card add-on
❌ BirdNET-Pi MQTT topic configuration (verify topics being published)
❌ CSV export automation
❌ Email/notification alerts

---

## Contact Points for Future Work
- **Dog Bark Detector**: Line 63 has CHUNK_SIZE, critical for model input
- **Recording Directory**: Lines 103-115 handle USB fallback logic
- **MQTT Sensors**: `audio_detection.yaml` lines 17-150
- **Template Sensors**: `audio_detection.yaml` lines 156-222
- **Dashboard**: `/home/demeter/homeassistant/dashboards/home-test.yaml`
- **Models**: Always at `/home/demeter/audio_detection/models/`

---

## Historical Challenges Overcome
1. **Service hardcoded for wrong user** - Fixed sed scripts to update from `pi` to `demeter`
2. **Python paths in venv vs system** - Switched to system Python at `/usr/bin/python3`
3. **TensorFlow version incompatibility** - Upgraded from 2.13.0 to 2.20.0, fixed flatbuffers
4. **Model input shape mismatch** - Discovered YAMNet expects exactly 15600 samples, not 16000
5. **/mnt/usb permission errors** - Added fallback to local directory with existence check
6. **Legacy HA template syntax** - Converted all sensors to modern `template:` format (2026.6+)
7. **MQTT binary_sensor misconfiguration** - Moved bird sensors from binary to sensor section

