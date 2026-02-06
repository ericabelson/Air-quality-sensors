# Prompt for Next Claude Code Instance - Dog Bark & Bird Detection Dashboard Issues

## Context & Background
This is a continuation of implementing dog bark and bird detection monitoring into Home Assistant running on a Raspberry Pi. The detection services are **fully operational and publishing data**, but the Home Assistant dashboard is showing **configuration errors and entity not found errors**.

**Reference Documents**:
- Read this first: `/home/user/Air-quality-sensors/SETUP_IMPLEMENTATION_NOTES.md` - Complete system overview and file locations
- Implementation guide: `/home/user/Air-quality-sensors/docs/DOG_BARK_BIRD_DETECTION_GUIDE.md`
- Current branch: `claude/ha-dog-bark-bird-detection-SFB7v`

## Current Status

### ✅ What's Working
- Dog bark detector service: Running, detecting barks, publishing to MQTT
- BirdNET-Pi service: Running, recording birds, detecting species
- MQTT broker: Operational on localhost:1883
- Audio input: iPhone streaming via Periscope HD
- Home Assistant: Running in Docker, MQTT integration enabled
- Sensors defined: All MQTT and template sensors created in `audio_detection.yaml`

### ❌ What's Broken
1. **Dashboard Configuration Errors**
   - Orange warning triangles with ! in Home Assistant dashboard cards
   - "Entity currently unavailable" errors on several sensor cards
   - Some cards not rendering (ApexCharts)

2. **Entity Not Found Errors**
   - Specific entities showing as unavailable in dashboard
   - Bird species list not populating
   - Some template sensors not calculating

3. **Missing Data**
   - Last 20 birds list showing "No birds detected in the last 24 hours" (even though BirdNET is running)
   - Bark timeline may not be updating
   - Statistics not accumulating

## System Details to Reference

### File Locations
```
Home Assistant config: /home/demeter/homeassistant/
├── packages/audio_detection.yaml                  ← MQTT & template sensors
└── dashboards/home-test.yaml                     ← Dashboard YAML (local file, not in repo)

Audio detection repo: /home/demeter/Air-quality-sensors/
├── scripts/dog_bark_detector.py                  ← Working dog detector
└── homeassistant/packages/audio_detection.yaml   ← Source of truth

Services:
/etc/systemd/system/dog_bark_detector.service     ← Running, publishing to MQTT
/etc/systemd/system/birdnet_recording.service     ← Running, detecting birds
```

### Key Entities & Topics
**MQTT Topics Being Published** (verify with `mosquitto_sub -h localhost -t "audio/#" -v`):
- `audio/dog_bark` - Real-time bark detections
- `audio/decibels` - Current sound level
- `audio/bark_stats` - Daily statistics
- `birdnet/detection` - Bird species (from BirdNET-Pi)
- `birdnet/stats` - Bird statistics

**Expected Home Assistant Entities**:
- `sensor.audio_decibels`
- `sensor.dog_bark_confidence`
- `sensor.total_barks_today`
- `sensor.bark_minutes_per_hour`
- `sensor.decibel_status`
- `sensor.quiet_streak`
- `sensor.latest_bird_species`
- `sensor.bird_confidence`
- `sensor.bird_species_today`
- `binary_sensor.dog_barking`

## Your Task

### Step 1: Verify Current State
1. SSH into Pi: `ssh demeter@192.168.68.109`
2. Confirm both services running:
   ```bash
   sudo systemctl status dog_bark_detector birdnet_recording --no-pager
   ```
3. Verify MQTT data flowing:
   ```bash
   mosquitto_sub -h localhost -t "audio/#" -v
   ```
4. Check what entities Home Assistant has created:
   - HA Settings → Developer Tools → States
   - Search for "dog_bark", "bird", "audio_decibels"

### Step 2: Diagnose Configuration Errors
**Do NOT send the user on fishing expeditions.** Before asking them to do anything, you must:

1. Read the complete SETUP_IMPLEMENTATION_NOTES.md to understand the system
2. Read the audio_detection.yaml file to understand what sensors should exist
3. Check Home Assistant logs for actual error messages:
   ```bash
   docker logs homeassistant 2>&1 | grep -i "error\|warning" | tail -50
   ```
4. Verify the dashboard YAML at `/home/demeter/homeassistant/dashboards/home-test.yaml` for entity ID typos

**Common Issues to Check**:
- Entity IDs with hyphens vs underscores (e.g., `dog_bark_confidence` vs `dog-bark-confidence`)
- Missing `custom:apexcharts-card` add-on (causes chart cards to fail)
- BirdNET-Pi not configured to publish to correct MQTT topics
- MQTT topics in audio_detection.yaml not matching what BirdNET-Pi publishes

### Step 3: Fix Issues Systematically
1. **Entity Availability Issues**: Check if entities exist in HA; if not, check if MQTT topics are publishing
2. **Configuration Errors**: Fix entity ID mismatches in dashboard YAML
3. **Missing Data**: Verify MQTT topics, check service logs for errors
4. **Chart Rendering**: Ensure ApexCharts add-on is installed

### Step 4: Test & Validate
- Navigate to Home Assistant dashboard
- Verify all cards render without errors
- Confirm data is updating (decibels should change, bird species should appear)
- Check both dog barking and bird detection sections

---

## Important Things to Know

### About the Repository
- **Branch**: `claude/ha-dog-bark-bird-detection-SFB7v` (do NOT push to main)
- **Workflow**: Make changes, test on Pi, commit & push to branch
- **Source of Truth**: `/home/user/Air-quality-sensors/` is your local copy
- **Files in repo**: Everything under `/home/user/Air-quality-sensors/`
- **Files NOT in repo**: `/home/demeter/homeassistant/home-test.yaml` is a local modification (created directly in HA)

### Docker Context
- Home Assistant runs in Docker container named `homeassistant`
- Config is mounted at `/home/demeter/homeassistant` (host) → `/config` (container)
- To access files inside container: `docker exec homeassistant cat /config/packages/audio_detection.yaml`
- To check logs: `docker logs homeassistant`

### MQTT & HA Integration
- MQTT broker is built into Home Assistant installation
- When you change `audio_detection.yaml`, HA may need restart to reload MQTT sensors
- To reload MQTT without full restart: Settings → Devices & Services → MQTT → ⋮ → Reload

### Python & Services
- Dog bark detector runs as `demeter` user
- Uses system Python at `/usr/bin/python3`
- Packages installed with: `sudo pip3 install --break-system-packages`
- TensorFlow 2.20.0 (not 2.13.0)
- Model input MUST be exactly 15600 samples (not 16000)

---

## Your Attitude & Approach

**DO**:
- Read the SETUP_IMPLEMENTATION_NOTES.md completely before doing anything
- Check actual error logs and real data before making suggestions
- Verify services are running before asking about missing data
- Test your fixes on the system
- Commit and push code changes to the branch

**DON'T**:
- Send users on fishing expeditions to check things without knowing the issue first
- Make changes without understanding the existing system
- Guess at entity IDs or file paths
- Suggest changes without verifying them in code first

---

## Success Criteria

When complete, the dashboard should:
- ✅ Display "BARKING NOW" or "All Quiet" status with correct color
- ✅ Show real-time decibel gauge (updating live)
- ✅ Display 72-hour barking timeline with red bands
- ✅ Show daily bark statistics (events, duration, max dB)
- ✅ List recent bird species (last 24 hours)
- ✅ Display bird detection trends (7-day chart)
- ✅ No orange warning triangles or configuration errors
- ✅ All sensor cards showing actual values, not "unavailable"

---

## Files You'll Be Working With

### Read-Only (Reference)
- `/home/user/Air-quality-sensors/SETUP_IMPLEMENTATION_NOTES.md` - This guide
- `/home/user/Air-quality-sensors/docs/DOG_BARK_BIRD_DETECTION_GUIDE.md` - Implementation details
- `/home/user/Air-quality-sensors/scripts/dog_bark_detector.py` - Working code (read to understand)

### Likely to Edit
- `/home/demeter/homeassistant/packages/audio_detection.yaml` - If MQTT topics need fixing
- `/home/demeter/homeassistant/dashboards/home-test.yaml` - If entity IDs need fixing
- Git commits back to branch when changes are made

### For Troubleshooting
```bash
# Check detector logs
sudo journalctl -u dog_bark_detector -n 100 --no-pager

# Check MQTT data
mosquitto_sub -h localhost -t "audio/#" -v

# Check HA logs
docker logs homeassistant 2>&1 | tail -100

# Check HA configuration validity
docker exec homeassistant hass --script check_config

# Restart HA after changes
docker restart homeassistant
```

---

## When You Get Started

1. **First action**: Read `/home/user/Air-quality-sensors/SETUP_IMPLEMENTATION_NOTES.md` completely
2. **Second action**: SSH into Pi and run the health check commands above
3. **Third action**: Examine Home Assistant logs and identify specific entity/configuration errors
4. **Fourth action**: Locate the source of each error in the YAML files
5. **Then**: Fix issues methodically, testing each fix before moving to the next

Do NOT make changes until you've read the setup notes and understand the full system architecture.

