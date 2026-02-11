# Audio System Setup for Raspberry Pi

## Quick Start

Copy these two files to your Raspberry Pi:
- `START_AUDIO_SYSTEM.sh`
- `START_DETECTORS.sh`
- `dog_bark_detector.py`

Then run on the Pi:

```bash
sudo chmod +x START_AUDIO_SYSTEM.sh START_DETECTORS.sh
sudo ./START_AUDIO_SYSTEM.sh
```

Wait for it to complete, then in another terminal:

```bash
./START_DETECTORS.sh
```

---

## What This Does

### START_AUDIO_SYSTEM.sh (Run with sudo)

This script:
1. **Installs dependencies** - FFmpeg, PulseAudio, ALSA
2. **Loads ALSA loopback** - Creates virtual audio device
3. **Starts PulseAudio** - Audio middleware
4. **Starts FFmpeg** - Captures RTSP stream from iPhone at `192.168.68.106:8554/live.sdp`
5. **Pipes audio** - iPhone audio → ALSA loopback → PulseAudio

**Output:**
- FFmpeg log: `/var/log/air-quality/ffmpeg.log`
- Status report: `/tmp/audio_system_status.txt`

### START_DETECTORS.sh

This script:
1. **Verifies audio system** is running
2. **Starts dog bark detector** - Reads from PulseAudio, publishes to MQTT
3. **Logs to** `/var/log/air-quality/dog_bark_detector.log`

---

## Troubleshooting

### Check if audio is flowing:
```bash
# Check FFmpeg is running
ps aux | grep ffmpeg

# Check loopback device exists
arecord -l | grep Loopback

# Check PulseAudio is running
pgrep pulseaudio

# View FFmpeg log
tail -f /var/log/air-quality/ffmpeg.log
```

### If iPhone stream won't connect:
```bash
# Test if iPhone is reachable
ping 192.168.68.106

# Test RTSP stream URL
ffprobe -rtsp_transport tcp rtsp://192.168.68.106:8554/live.sdp
```

### If detector shows silence:
1. Verify FFmpeg is capturing: `tail /var/log/air-quality/ffmpeg.log`
2. Check ALSA loopback: `arecord -l`
3. Check PulseAudio: `pactl list sources`

---

## Configuration

The iPhone IP is hardcoded to `192.168.68.106` in `START_AUDIO_SYSTEM.sh`.
To use a different IP:
```bash
sudo ./START_AUDIO_SYSTEM.sh 192.168.X.X
```

---

## What Needs to be Running

For the audio system to work, you need:

1. **Home Assistant** - Running with MQTT broker on localhost:1883
2. **Raspberry Pi** - With:
   - FFmpeg
   - PulseAudio
   - ALSA
   - Python3 with TensorFlow, PyAudio, librosa

The scripts install FFmpeg, PulseAudio, and ALSA automatically.

---

## Files Generated

- `/var/log/air-quality/ffmpeg.log` - FFmpeg output/errors
- `/var/log/air-quality/dog_bark_detector.log` - Detector logs
- `/tmp/audio_system_status.txt` - Status report
