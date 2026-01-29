# Dog Bark & Bird Detection - Quick Start Guide

## 🎯 What You're Building

A complete audio detection system that:
- 🐕 Detects and records dog barking with decibel measurements
- 🐦 Identifies 3,000+ bird species using AI
- 📊 Creates Excel/CSV reports with timestamps
- 📈 Beautiful Home Assistant dashboards
- 💾 Saves audio recordings for posterity
- ⏱️ Groups barking events with 5-min and 10-min gap logic

## ⚡ Super Quick Start (30-Second Summary)

1. **Hardware:** iPhone 7 as microphone, existing Raspberry Pi
2. **Storage:** Use 1TB USB drive (recommended)
3. **Software:** BirdNET-Pi + custom dog bark detector
4. **Time:** 3-4 hours total setup
5. **Result:** Automated 24/7 audio monitoring with beautiful dashboards!

---

## 📋 Prerequisites Check

Before starting, make sure you have:

- [x] iPhone 7 (and charger - it stays plugged in)
- [x] Raspberry Pi 4 (already set up with Home Assistant)
- [x] 1TB USB flash drive or external SSD
- [x] WiFi network (same network for iPhone and Pi)
- [x] Computer to SSH into the Pi
- [x] Basic command line knowledge (we guide you through everything!)

**Estimated Total Time:** 3-4 hours (mostly waiting for installations)

---

## 🚀 Installation Order (Follow This Sequence!)

### Phase 1: Hardware Setup (15 minutes)

1. **Plug in USB drive** to Raspberry Pi
2. **Connect iPhone to charger** and place near windows
3. **Ensure both on same WiFi** network

📄 **Detailed Guide:** [DOG_BARK_BIRD_DETECTION_GUIDE.md](DOG_BARK_BIRD_DETECTION_GUIDE.md#hardware-setup)

---

### Phase 2: iPhone Microphone (30 minutes)

1. **Install AudioRelay app** on iPhone from App Store
2. **Install AudioRelay server** on Raspberry Pi
3. **Connect and test** audio streaming

📄 **Detailed Guide:** [IPHONE_MICROPHONE_SETUP.md](IPHONE_MICROPHONE_SETUP.md)

**Quick Commands:**
```bash
# SSH to Pi
ssh pi@<your-pi-ip>

# Install AudioRelay
mkdir -p ~/audiorelay && cd ~/audiorelay
wget https://github.com/grishka/AudioRelay/releases/latest/download/audiorelay-server-linux-arm64.tar.gz
tar -xzf audiorelay-server-linux-arm64.tar.gz
chmod +x audiorelay
./audiorelay
```

---

### Phase 3: USB Storage Setup (10 minutes)

Format and mount the USB drive for audio storage.

**Commands:**
```bash
# Find USB drive
lsblk

# Format (WARNING: erases all data!)
sudo mkfs.ext4 /dev/sda1

# Mount
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb

# Auto-mount on boot
echo "/dev/sda1 /mnt/usb ext4 defaults 0 2" | sudo tee -a /etc/fstab

# Set permissions
sudo chown -R pi:pi /mnt/usb

# Create directories
mkdir -p /mnt/usb/bark_audio/{recordings,compressed}
mkdir -p /mnt/usb/bird_audio
```

---

### Phase 4: BirdNET-Pi Installation (60 minutes)

Install BirdNET-Pi for bird detection. **This takes the longest!**

**Commands:**
```bash
cd ~/Air-quality-sensors/scripts
chmod +x install_birdnet.sh
./install_birdnet.sh
```

The script will:
- ✓ Install dependencies
- ✓ Download BirdNET-Pi
- ✓ Configure MQTT
- ✓ Set up systemd services
- ✓ Test installation

**Go get coffee during this step!** ☕ It takes 30-60 minutes.

---

### Phase 5: Dog Bark Detector Setup (20 minutes)

Install Python packages and set up the detector.

**Commands:**
```bash
# Create environment
cd ~
mkdir -p audio_detection/{logs,data,models,csv_exports}
cd audio_detection
python3 -m venv venv
source venv/bin/activate

# Install packages (takes 15-20 minutes)
pip install --upgrade pip
pip install \
    tensorflow==2.13.0 \
    librosa==0.10.1 \
    soundfile==0.12.1 \
    pyaudio==0.2.13 \
    pydub==0.25.1 \
    paho-mqtt==1.6.1 \
    numpy==1.24.3 \
    scipy==1.11.3

# Download AI model
cd models
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/lite-model_yamnet_classification_tflite_1.tflite
mv lite-model_yamnet_classification_tflite_1.tflite yamnet.tflite

wget https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv
```

---

### Phase 6: Configure Audio Device (5 minutes)

Tell the detector which audio device to use.

**Commands:**
```bash
# List audio devices
arecord -l

# Note the card number for AudioRelay (e.g., card 2)

# Edit detector configuration
cd ~/Air-quality-sensors/scripts
nano dog_bark_detector.py

# Find line: AUDIO_DEVICE_INDEX = None
# Change to: AUDIO_DEVICE_INDEX = 2  (your card number)

# Save: Ctrl+O, Enter, Ctrl+X
```

---

### Phase 7: Home Assistant Integration (15 minutes)

Copy configuration files to Home Assistant.

**Commands:**
```bash
# Files are already created in the repo!
# Just restart Home Assistant to load them

# If using Docker Home Assistant:
docker restart homeassistant

# Wait 30 seconds, then check:
# http://<your-pi-ip>:8123
```

The following configs are already in place:
- `homeassistant/packages/audio_detection.yaml` - Sensors
- `homeassistant/automations/audio_alerts.yaml` - Automations
- `homeassistant/dashboards/audio_detection_dashboard.yaml` - Dashboard

---

### Phase 8: Create Systemd Services (5 minutes)

Set up automatic startup.

**Commands:**
```bash
cd ~/Air-quality-sensors/scripts
chmod +x create_services.sh
./create_services.sh

# Start services
sudo systemctl start dog_bark_detector
sudo systemctl start audio_csv_export.timer

# Check status
sudo systemctl status dog_bark_detector
```

---

### Phase 9: Testing (10 minutes)

Test everything works!

**Test 1: Audio Input**
```bash
# Record 5 seconds
arecord -D plughw:2,0 -d 5 -f cd test.wav

# Play back
aplay test.wav

# You should hear the audio!
```

**Test 2: Dog Bark Detection**
```bash
# View live detection logs
sudo journalctl -u dog_bark_detector -f

# In another room, clap loudly or play YouTube dog barking
# You should see detection messages!
```

**Test 3: MQTT Messages**
```bash
# Subscribe to all audio topics
mosquitto_sub -h localhost -t "audio/#" -v

# You should see real-time messages!
```

**Test 4: Bird Detection**
```bash
# Play bird calls from YouTube near iPhone
# Check BirdNET web interface: http://<your-pi-ip>
# Should see detections appearing!
```

**Test 5: Home Assistant Dashboard**
```bash
# Open in browser:
# http://<your-pi-ip>:8123

# Navigate to: Audio Detection dashboard
# Should see live data!
```

---

## 📊 What You Get

### CSV Files (Auto-Generated Daily)

Located in: `~/audio_detection/csv_exports/`

1. **bark_events_5min.csv**
   - Date, Start Time, End Time, Duration, Max dB, Num Barks
   - New row after 5+ minutes of silence

2. **bark_events_10min.csv**
   - Same format, but 10+ minutes of silence threshold

3. **bird_detections.csv**
   - Date, Time, Species, Common Name, Confidence, Location

4. **daily_summary.csv**
   - Overall statistics for the day

5. **weekly_report.csv**
   - Week-at-a-glance summary

### Audio Recordings

Located in: `/mnt/usb/bark_audio/recordings/YYYY/MM/DD/`

- Format: MP3 (compressed, high quality)
- Named: `bark_YYYY-MM-DD_HH-MM-SS.mp3`
- ~2MB per minute
- With 1TB: **5+ years of storage!**

### Home Assistant Dashboards

**Overview Page:**
- 🔴 Live bark status ("BARKING NOW" or "Quiet")
- 📊 Decibel gauge (real-time)
- 📈 24-hour timeline bar chart
- 📉 Daily statistics

**Birds Page:**
- 🐦 Latest bird detected
- 📋 Species list (last 2 hours)
- 📊 Species diversity chart
- 🏆 Most common bird today

**Statistics Page:**
- 📈 Weekly bark summary
- 📉 Decibel history
- 🎯 Barking patterns analysis
- 📊 Birds vs barks comparison

---

## 🎮 Daily Usage

Once set up, the system runs **completely automatically!**

### What Happens Automatically

- ✅ iPhone streams audio 24/7
- ✅ Dog barks detected and recorded
- ✅ Birds identified in real-time
- ✅ CSV files updated continuously
- ✅ Audio clips saved to USB drive
- ✅ Home Assistant dashboards update live
- ✅ Daily CSV export at midnight
- ✅ Notifications for excessive barking

### What You Do

**Option 1: Nothing!** Just let it run.

**Option 2: Check Dashboard**
- Open Home Assistant on phone/tablet/computer
- View real-time barking status
- See bird species detected today

**Option 3: Review Data**
```bash
# View today's bark events (5-min grouping)
cat ~/audio_detection/csv_exports/bark_events_5min_*.csv | tail -20

# View bird detections
cat ~/audio_detection/csv_exports/bird_detections_*.csv | tail -20

# Listen to recordings
cd /mnt/usb/bark_audio/recordings/$(date +%Y/%m/%d)
ls -lh
mpg123 bark_*.mp3
```

---

## 🔧 Common Operations

### View Live Logs

```bash
# Dog bark detector
sudo journalctl -u dog_bark_detector -f

# BirdNET
sudo journalctl -u birdnet -f

# MQTT messages
mosquitto_sub -h localhost -t "#" -v
```

### Restart Services

```bash
# Restart bark detector
sudo systemctl restart dog_bark_detector

# Restart BirdNET
sudo systemctl restart birdnet

# Restart Home Assistant
docker restart homeassistant
```

### Export CSV Manually

```bash
cd ~/audio_detection
source venv/bin/activate
python3 ~/Air-quality-sensors/scripts/csv_exporter.py --all
```

### View Statistics

```bash
cd ~/audio_detection
source venv/bin/activate
python3 ~/Air-quality-sensors/scripts/csv_exporter.py --stats
```

### Copy Recordings to Computer

```bash
# From your computer (not on the Pi)
scp -r pi@<your-pi-ip>:/mnt/usb/bark_audio/recordings/2024/03/15 ~/Desktop/bark_recordings/
```

---

## 📱 Home Assistant Mobile App

For notifications on your phone:

1. **Install Home Assistant Companion** app (iOS/Android)
2. **Log in** to your Home Assistant
3. **Enable notifications** in app settings
4. **You'll get alerts** for:
   - Excessive barking (10+ minutes)
   - Very loud barking (>90 dB)
   - Rare bird detections (>90% confidence)
   - System offline warnings

---

## 🎨 Dashboard Customization

Want to customize the dashboards?

**Edit:**
```bash
nano ~/Air-quality-sensors/homeassistant/dashboards/audio_detection_dashboard.yaml
```

**Restart Home Assistant:**
```bash
docker restart homeassistant
```

**Or use Home Assistant UI:**
1. Go to Settings → Dashboards
2. Select "Audio Detection"
3. Click "Edit Dashboard"
4. Drag and drop cards!

---

## 🐛 Troubleshooting

### No Audio Detected

1. Check iPhone AudioRelay is connected and streaming
2. Verify audio device number:
   ```bash
   arecord -l
   ```
3. Test recording:
   ```bash
   arecord -D plughw:2,0 -d 5 test.wav && aplay test.wav
   ```

### No Bark Detections

1. Check detector is running:
   ```bash
   sudo systemctl status dog_bark_detector
   ```
2. View logs:
   ```bash
   sudo journalctl -u dog_bark_detector -f
   ```
3. Test with loud clapping or YouTube dog barking

### No Bird Detections

1. Check BirdNET is running:
   ```bash
   sudo systemctl status birdnet
   ```
2. View BirdNET web interface: `http://<your-pi-ip>`
3. Play bird calls from YouTube near iPhone

### Home Assistant Not Showing Data

1. Restart Home Assistant:
   ```bash
   docker restart homeassistant
   ```
2. Check MQTT broker:
   ```bash
   sudo systemctl status mosquitto
   ```
3. Test MQTT:
   ```bash
   mosquitto_sub -h localhost -t "audio/#" -v
   ```

---

## 📚 Full Documentation

For detailed information, see:

1. **[DOG_BARK_BIRD_DETECTION_GUIDE.md](DOG_BARK_BIRD_DETECTION_GUIDE.md)** - Complete implementation guide
2. **[IPHONE_MICROPHONE_SETUP.md](IPHONE_MICROPHONE_SETUP.md)** - iPhone setup details
3. **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Pi configuration (already done)
4. **[HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md)** - HA configuration (already done)

---

## 🎉 You're Done!

Congratulations! You now have a professional-grade audio detection system!

### What's Running:

- 🎤 iPhone streaming audio
- 🐕 Dog bark detector analyzing audio
- 🐦 BirdNET identifying birds
- 📊 Home Assistant displaying data
- 💾 Audio recordings being saved
- 📈 CSV reports being generated

### Check Your Dashboard:

**Open:** `http://<your-pi-ip>:8123/audio-detection`

You should see:
- Live bark status
- Real-time decibel meter
- Today's statistics
- Bird species detected
- Beautiful visualizations!

---

## 🚀 Next Steps (Optional)

### Advanced Features

1. **Add camera** to sync video with bark events
2. **Create custom alerts** for specific bird species
3. **Build weekly email reports** with charts
4. **Add second iPhone** for multi-zone coverage
5. **Train custom model** on your specific dog's bark
6. **Add Grafana dashboards** for advanced analytics
7. **Set up cloud backup** for recordings
8. **Create Telegram bot** for mobile notifications

### Share Your Setup

Found this useful? Share your setup on:
- Home Assistant Community Forum
- Reddit r/homeassistant
- GitHub (star the repo!)

---

## ❓ Need Help?

**Check logs:**
```bash
# All detection logs
tail -f ~/audio_detection/logs/*.log

# System logs
sudo journalctl -u dog_bark_detector -f
sudo journalctl -u birdnet -f
```

**Test components:**
```bash
# Audio test
arecord -D plughw:2,0 -d 5 test.wav && aplay test.wav

# MQTT test
mosquitto_sub -h localhost -t "#" -v

# Home Assistant test
curl http://localhost:8123
```

**Still stuck?** Check the detailed guides listed above!

---

**Enjoy your automated audio detection system!** 🎉🐕🐦
