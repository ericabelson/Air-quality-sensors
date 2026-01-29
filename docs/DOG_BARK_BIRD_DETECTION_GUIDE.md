# Complete Dog Bark and Bird Detection System Setup Guide

## Overview

This guide will help you set up a comprehensive audio detection system that:
- Detects and records dog barking events
- Identifies bird species using BirdNET-Pi
- Displays real-time data on Home Assistant dashboards
- Exports detailed CSV reports with timestamps
- Records audio clips for posterity
- Creates beautiful visualizations

**Total Setup Time:** 3-4 hours
**Difficulty Level:** Beginner-friendly (no prior knowledge required)
**Hardware Required:** iPhone 7, Raspberry Pi (already installed), USB cable or network connection

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Hardware Setup](#hardware-setup)
3. [iPhone Setup as Microphone](#iphone-setup-as-microphone)
4. [Raspberry Pi Software Installation](#raspberry-pi-software-installation)
5. [BirdNET-Pi Installation](#birdnet-pi-installation)
6. [Dog Bark Detection Setup](#dog-bark-detection-setup)
7. [Home Assistant Integration](#home-assistant-integration)
8. [CSV Export System](#csv-export-system)
9. [Audio Recording System](#audio-recording-system)
10. [Dashboard Visualization](#dashboard-visualization)
11. [Testing and Troubleshooting](#testing-and-troubleshooting)

---

## System Architecture Overview

### How It All Works Together

```
┌─────────────────┐
│   iPhone 7      │  Captures audio with built-in microphone
│  (Microphone)   │  Streams audio over network or USB
└────────┬────────┘
         │
         │ Audio Stream
         ▼
┌─────────────────────────────────────────────────────────┐
│           Raspberry Pi (Your Existing System)           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  BirdNET-Pi (Bird Detection)                    │  │
│  │  - Identifies 3,000+ bird species               │  │
│  │  - Runs 24/7 analysis                           │  │
│  │  - Creates spectrograms                         │  │
│  │  - Confidence scores for each detection         │  │
│  └────────────┬────────────────────────────────────┘  │
│               │                                        │
│               │ MQTT Messages                          │
│               ▼                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Dog Bark Detector (Custom Python)              │  │
│  │  - Audio classification using TensorFlow        │  │
│  │  - Decibel level monitoring                     │  │
│  │  - 5-min gap grouping logic                     │  │
│  │  - 10-min gap grouping logic                    │  │
│  └────────────┬────────────────────────────────────┘  │
│               │                                        │
│               │ MQTT Messages                          │
│               ▼                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  MQTT Broker (Mosquitto - Already Running)     │  │
│  └────────────┬────────────────────────────────────┘  │
│               │                                        │
│               │ MQTT Topics:                           │
│               │ - audio/dog_bark                       │
│               │ - audio/bird_detection                 │
│               │ - audio/decibels                       │
│               ▼                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  CSV Export System                              │  │
│  │  - 5-minute gap CSV (bark_events_5min.csv)     │  │
│  │  - 10-minute gap CSV (bark_events_10min.csv)   │  │
│  │  - Bird detections CSV (bird_events.csv)       │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Audio Recording System                         │  │
│  │  - Saves bark clips to /mnt/usb/bark_audio/    │  │
│  │  - MP3 compression (high quality, small size)   │  │
│  │  - Organized by date                            │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │
         │ Web Interface & Data
         ▼
┌─────────────────────────────────────────────────────────┐
│              Home Assistant Dashboard                   │
│                                                         │
│  ┌─────────────────┐  ┌────────────────────────────┐  │
│  │  Dog Barking    │  │  Bird Detections            │  │
│  │  - Live status  │  │  - Species icons            │  │
│  │  - Timeline bar │  │  - Last 2 hours             │  │
│  │  - Decibels     │  │  - Confidence scores        │  │
│  │  - Daily total  │  │  - Species diversity chart  │  │
│  └─────────────────┘  └────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  24-Hour Barking Timeline (Visual Bar Chart)    │  │
│  │  ████░░░███░░░░░░░██████░░░░░░░░░░░░░░░░░░░░░  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Statistics                                      │  │
│  │  - Minutes barking per hour: 12 min             │  │
│  │  - Total barking today: 2h 45min                │  │
│  │  - Longest quiet period: 8h 23min               │  │
│  │  - Bird species today: 14 species               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Hardware Setup

### What You Need

#### Already Have (From Your Existing System)
- ✅ Raspberry Pi 4 (2GB+ RAM)
- ✅ 32GB+ microSD card with your air quality system
- ✅ Power supply
- ✅ Network connection (WiFi or Ethernet)
- ✅ Home Assistant running in Docker

#### New Hardware Needed
- 📱 iPhone 7 (you have this)
- 🔌 Lightning to USB cable (for wired connection) OR WiFi (for wireless)
- 💾 **RECOMMENDED:** 1TB USB flash drive or external SSD for audio storage

### Storage Recommendations

You asked about SD card vs USB storage. Here's my advice:

#### Option 1: 1TB USB Drive (STRONGLY RECOMMENDED) ⭐
**Pros:**
- Much more storage (1TB vs 32-64GB)
- Faster write speeds
- Doesn't wear out your Pi's SD card
- Easy to remove and view/backup files on computer
- Longer lifespan for continuous recording

**Cons:**
- Requires USB port (but you have plenty)

#### Option 2: Larger SD Card
**Pros:**
- No extra hardware needed
- Slightly simpler setup

**Cons:**
- Limited space (even 256GB fills up quickly with audio)
- Wears out faster with constant writes
- Harder to backup
- If SD card fails, entire system goes down

**MY RECOMMENDATION:** Use a 1TB USB flash drive or external SSD. It's the best solution for long-term audio recording.

---

## iPhone Setup as Microphone

Your iPhone 7 can act as a network microphone. Here are two methods:

### Method 1: AudioRelay App (EASIEST - RECOMMENDED) ⭐

This is the simplest method. AudioRelay turns your iPhone into a wireless microphone.

#### Step 1: Install AudioRelay on iPhone

1. Open **App Store** on your iPhone 7
2. Search for **"AudioRelay"**
3. Download and install **AudioRelay: Stream PC Audio** (free version is fine)
4. Open the app

#### Step 2: Install AudioRelay Server on Raspberry Pi

SSH into your Raspberry Pi:
```bash
ssh pi@<your-pi-ip-address>
```

Install AudioRelay server:
```bash
# Download and install
cd ~
wget https://github.com/grishka/AudioRelay/releases/latest/download/audiorelay-server-linux-arm64.tar.gz
tar -xzf audiorelay-server-linux-arm64.tar.gz
cd audiorelay-server

# Run the server
./audiorelay-server
```

#### Step 3: Connect iPhone to Raspberry Pi

1. On your iPhone, open AudioRelay app
2. Tap **"Connect"**
3. Select your Raspberry Pi from the list (should appear automatically on same WiFi network)
4. Tap **"Start Streaming"**

That's it! Your iPhone is now streaming audio to the Raspberry Pi.

---

### Method 2: Microphone Live App (Alternative)

#### Step 1: Install App on iPhone

1. Open **App Store**
2. Search for **"Microphone Live"**
3. Install **Microphone Live** by Von Bruno
4. Open the app

#### Step 2: Configure Streaming

1. In the app, go to **Settings**
2. Enable **"WiFi Audio Streaming"**
3. Note the IP address shown (something like `192.168.1.150:8080`)

#### Step 3: Capture Stream on Raspberry Pi

```bash
# Install FFmpeg if not already installed
sudo apt-get install ffmpeg

# Capture audio stream
ffmpeg -i http://<IPHONE-IP>:8080/audio.wav -f alsa default
```

---

### Method 3: USB Connection (Most Stable)

If you want a wired connection for maximum reliability:

#### Step 1: Install Required Software on Raspberry Pi

```bash
sudo apt-get update
sudo apt-get install -y usbmuxd libimobiledevice-utils
```

#### Step 2: Connect iPhone with USB Cable

1. Connect iPhone 7 to Raspberry Pi USB port using Lightning cable
2. Unlock your iPhone
3. Tap **"Trust This Computer"** when prompted

#### Step 3: Set Up Audio Capture

```bash
# Check if iPhone is recognized
ideviceinfo

# You'll use this connection with our dog bark detector later
```

---

**RECOMMENDATION:** Start with **Method 1 (AudioRelay)** - it's the easiest and works great for this project.

---

## Raspberry Pi Software Installation

### Step 1: Connect to Your Raspberry Pi

From your computer, open a terminal (Mac/Linux) or PowerShell (Windows):

```bash
ssh pi@<your-pi-ip-address>
```

Enter your password when prompted.

### Step 2: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

This will take 5-10 minutes.

### Step 3: Install Required Packages

```bash
# Audio processing libraries
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    sox \
    libsox-fmt-all \
    alsa-utils

# Machine learning libraries
sudo apt-get install -y \
    python3-numpy \
    python3-scipy \
    libatlas-base-dev \
    libopenblas-dev
```

### Step 4: Set Up USB Storage (Recommended)

If you're using a USB drive for audio storage:

```bash
# Plug in your 1TB USB drive

# Find the drive name
lsblk

# You should see something like /dev/sda1

# Create mount point
sudo mkdir -p /mnt/usb

# Format the drive (WARNING: This erases all data!)
sudo mkfs.ext4 /dev/sda1

# Mount the drive
sudo mount /dev/sda1 /mnt/usb

# Make it mount automatically on boot
echo "/dev/sda1 /mnt/usb ext4 defaults 0 2" | sudo tee -a /etc/fstab

# Set permissions
sudo chown -R pi:pi /mnt/usb
```

### Step 5: Create Directory Structure

```bash
# Create audio storage directories
mkdir -p /mnt/usb/bark_audio/{recordings,compressed}
mkdir -p /mnt/usb/bird_audio

# Create data directories
mkdir -p ~/audio_detection/{logs,data,models}

# Create CSV export directory
mkdir -p ~/audio_detection/csv_exports
```

---

## BirdNET-Pi Installation

BirdNET-Pi is an amazing open-source project that identifies bird calls in real-time. It's incredibly popular and well-maintained.

### Step 1: Download BirdNET-Pi Installer

```bash
cd ~
git clone https://github.com/mcguirepr89/BirdNET-Pi.git
cd BirdNET-Pi
```

### Step 2: Run Installation Script

```bash
./install.sh
```

**What this does:**
- Installs BirdNET (the AI model)
- Installs required Python packages
- Sets up a web interface
- Configures audio capture
- Creates systemd services for auto-start

This will take **30-60 minutes**. Go get a coffee!

### Step 3: Configure BirdNET-Pi

After installation completes, open your web browser and go to:
```
http://<your-pi-ip-address>
```

You'll see the BirdNET-Pi web interface!

#### Configuration Steps:

1. Click **"Settings"** in the top menu

2. **Audio Source Settings:**
   - Audio Source: Select your iPhone audio stream
   - Recording Length: 3 seconds (default is good)
   - Audio Format: WAV

3. **Detection Settings:**
   - Minimum Confidence: 0.7 (70% - good starting point)
   - Species Range: Select your location (helps narrow down species)
   - Enable "Real-time Detection"

4. **Database Settings:**
   - Enable "Store Detections in Database"
   - Enable "Create Spectrograms"

5. **MQTT Settings (IMPORTANT!):**
   - Enable MQTT
   - MQTT Broker: `localhost`
   - MQTT Port: `1883`
   - Topic Prefix: `birdnet`

6. Click **"Save Settings"**

### Step 4: Verify BirdNET-Pi is Running

```bash
# Check service status
sudo systemctl status birdnet

# Should show "active (running)" in green

# Check the logs
tail -f ~/BirdNET-Pi/birdnet.log
```

You should see log entries showing it's analyzing audio!

### Step 5: Test Bird Detection

1. Play a bird call on YouTube (search "robin bird call")
2. Hold your iPhone near the speaker
3. Wait 10-20 seconds
4. Check the BirdNET-Pi web interface - you should see a detection!

---

## Dog Bark Detection Setup

Now for the custom dog bark detector. This will detect barking, measure decibels, and group events based on your 5-minute and 10-minute gap requirements.

### Step 1: Install Python Dependencies

```bash
cd ~/audio_detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
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
```

This takes about 15-20 minutes.

### Step 2: Download Pre-trained Dog Bark Model

We'll use YAMNet, a pre-trained audio classification model from Google that recognizes dog barks:

```bash
cd ~/audio_detection/models

# Download YAMNet model
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/lite-model_yamnet_classification_tflite_1.tflite

# Rename for convenience
mv lite-model_yamnet_classification_tflite_1.tflite yamnet.tflite

# Download class labels
wget https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv
```

### Step 3: Test Audio Input

Let's verify your iPhone audio is working:

```bash
# Activate virtual environment if not already active
cd ~/audio_detection
source venv/bin/activate

# List available audio devices
python3 -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

You should see a list like:
```
0: bcm2835 Headphones
1: USB Audio Device
2: AudioRelay
```

Note the device number for your iPhone audio source.

### Step 4: Configure Dog Bark Detector

The detector script is provided in the next section. You'll need to edit one line to set your audio device:

```bash
# In the script, change this line:
AUDIO_DEVICE_INDEX = 2  # Change to match your iPhone device number
```

---

## Home Assistant Integration

Now we'll connect everything to Home Assistant so you can see beautiful dashboards!

### Step 1: Configure MQTT Sensors

SSH to your Raspberry Pi and navigate to your Home Assistant directory:

```bash
cd ~/Air-quality-sensors/homeassistant/packages
```

We'll create a new YAML file for audio detection sensors.

### Step 2: Add Audio Detection Package

The YAML configuration will be created in the next section with all sensors defined.

### Step 3: Add Automations

Automations will trigger notifications and actions based on detections.

### Step 4: Restart Home Assistant

```bash
# Restart Home Assistant container
docker restart homeassistant
```

Wait 30 seconds, then check Home Assistant web interface.

---

## CSV Export System

The CSV export system will create your two spreadsheets:
1. **bark_events_5min.csv** - Events grouped with 5-minute silence gaps
2. **bark_events_10min.csv** - Events grouped with 10-minute silence gaps

Both will include:
- Date (YYYY-MM-DD)
- Start Time (HH:MM:SS)
- End Time (HH:MM:SS)
- Duration (minutes)
- Max Decibels
- Number of Individual Barks

---

## Audio Recording System

Audio clips of barking will be:
- Saved to `/mnt/usb/bark_audio/recordings/YYYY/MM/DD/`
- Compressed to MP3 (high quality, ~1MB per minute)
- Organized by date
- Named with timestamps: `bark_2024-03-15_14-30-45.mp3`

### Storage Estimates

With 1TB USB drive:
- **High quality MP3 (256kbps):** ~2MB per minute
- **If dogs bark 4 hours per day:** ~480MB per day
- **Storage duration:** ~2,000+ days (5+ years!)

---

## Dashboard Visualization

Your Home Assistant dashboard will show:

### Dog Barking Section:
- 🔴 Live status: "BARKING NOW" or "Quiet"
- 📊 24-hour timeline bar chart
- 📈 Decibel meter (real-time)
- ⏱️ Daily statistics:
  - Total barking time today
  - Minutes per hour average
  - Longest quiet period
  - Current quiet streak

### Bird Detection Section:
- 🐦 Bird species icons (last 2 hours)
- 📋 List of species names with timestamps
- 📊 Species diversity chart
- 🏆 Most common bird today
- 📈 Detections over time graph

---

## Testing and Troubleshooting

### Test 1: Audio Input

```bash
# Record 5 seconds of audio to test
arecord -D plughw:2,0 -d 5 -f cd test.wav

# Play it back
aplay test.wav
```

### Test 2: Dog Bark Detection

```bash
# Run detector manually
cd ~/audio_detection
source venv/bin/activate
python3 dog_bark_detector.py
```

Clap your hands or play a dog bark sound from YouTube. You should see:
```
[2024-03-15 14:30:45] DOG BARK DETECTED - Confidence: 0.87 - Decibels: 72dB
```

### Test 3: MQTT Messages

```bash
# Subscribe to MQTT topics
mosquitto_sub -h localhost -t "audio/#" -v
```

You should see messages flowing when barks are detected.

### Test 4: Bird Detection

Play a bird call and check BirdNET-Pi web interface for detections.

---

## Common Issues and Solutions

### Issue: iPhone disconnects frequently
**Solution:** Use USB connection instead of WiFi, or enable "Prevent Auto-Lock" on iPhone.

### Issue: No audio detected
**Solution:** Check audio device index in script. Run `arecord -l` to see devices.

### Issue: Too many false positives
**Solution:** Increase confidence threshold in detector settings (default 0.7, try 0.8 or 0.9).

### Issue: Missing bird detections
**Solution:** Lower BirdNET confidence threshold to 0.6, ensure iPhone is near windows.

### Issue: Running out of storage
**Solution:** Enable automatic old file deletion in recording script (keeps last 30 days).

---

## Next Steps

Once everything is running, you can:

1. **Adjust sensitivity:** Tune confidence thresholds for your environment
2. **Add more automations:** Send notifications when rare birds detected
3. **Create reports:** Weekly summary emails with statistics
4. **Add cameras:** Sync video recordings with bark events
5. **Machine learning:** Train custom model on your specific dog's bark

---

## Support and Resources

- **BirdNET-Pi Documentation:** https://github.com/mcguirepr89/BirdNET-Pi
- **TensorFlow Lite:** https://www.tensorflow.org/lite
- **Home Assistant MQTT:** https://www.home-assistant.io/integrations/mqtt/
- **Audio Processing with Python:** https://realpython.com/python-audio/

---

## What's Next?

The following files will be created for you:

1. `scripts/dog_bark_detector.py` - Main detection script
2. `scripts/csv_exporter.py` - CSV generation script
3. `scripts/audio_recorder.py` - Audio recording handler
4. `homeassistant/packages/audio_detection.yaml` - HA sensor definitions
5. `homeassistant/automations/audio_alerts.yaml` - Alert automations
6. `homeassistant/dashboards/audio_dashboard.yaml` - Visualization dashboard

All these files are documented with comments and easy to customize!

---

**Ready to start? Let's install everything step by step!**
