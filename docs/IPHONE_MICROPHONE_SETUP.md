# iPhone 7 with Periscope HD - Complete Setup Guide for Audio Streaming

## What is Periscope HD?

**Periscope HD** is a professional iOS app that turns your iPhone into a network RTSP (Real-Time Streaming Protocol) camera with high-quality audio streaming. It broadcasts both video and audio over your WiFi network, which your Raspberry Pi can capture and process.

**App Store Link:** [Periscope HD - H.264 RTSP Cam](https://apps.apple.com/us/app/periscope-hd-h-264-rtsp-cam/id1095600218)

### Technical Specifications

- **Video:** H.264 codec, 1280x720 resolution, 30 fps
- **Audio:** G.711 PCMU codec, 8000 Hz sample rate (perfect for voice/bark detection)
- **Protocol:** RTSP over UDP or TCP
- **Discovery:** Bonjour/mDNS automatic discovery
- **Cost:** Free (with optional Pro upgrade for additional features)

### Why Periscope HD is Perfect for This Project

✅ **Professional RTSP stream** - Industry standard protocol
✅ **Built-in audio** - No separate audio routing needed
✅ **Reliable** - Designed for 24/7 surveillance use
✅ **Low latency** - Real-time audio capture
✅ **Auto-reconnect** - Handles network interruptions
✅ **Background operation** - Keeps running when screen locks

---

## Complete Step-by-Step Setup (Beginner-Friendly)

### Part 1: Installing Periscope HD on iPhone 7

#### Step 1: Open the App Store

1. **Locate the App Store icon** on your iPhone home screen
   - It's a blue icon with a white "A" made of three sticks
2. **Tap the App Store icon** once to open it
3. **Wait** for the App Store to load (2-3 seconds)

#### Step 2: Search for Periscope HD

1. **Tap the Search tab** at the bottom of the screen
   - It's the magnifying glass icon on the far right
2. **Tap the search bar** at the top (where it says "Games, Apps, Stories, and More")
3. **Type exactly:** `Periscope HD`
4. **Tap the Search button** on the keyboard (blue button, bottom right)

#### Step 3: Find the Correct App

**IMPORTANT:** There are several apps with similar names. Make sure you get the RIGHT one!

**The correct app:**
- **Name:** "Periscope HD - H.264 RTSP Cam"
- **Developer:** "Alice Dev Team"
- **Icon:** Blue/teal circular icon with camera symbol
- **Description:** Says "Turn your iOS device into an IP camera"

**NOT these apps:**
- ❌ Periscope Pro (different app)
- ❌ Any other Periscope apps
- ❌ Twitter/X apps

#### Step 4: Download and Install

1. **Tap the "GET" button** next to the correct app
2. **The button changes to "INSTALL"** - tap it again
3. **Enter your Apple ID password** when prompted
   - OR use Face ID/Touch ID if enabled
4. **Wait for download** to complete
   - You'll see a circular progress indicator
   - Takes about 30-60 seconds depending on connection
5. **When complete,** button changes to "OPEN"

#### Step 5: Initial App Launch

1. **Tap "OPEN"** in the App Store
   - OR find the app icon on your home screen and tap it
2. **The app will request permissions** - you MUST allow these:

**Permission 1: Camera Access**
- **Prompt:** "Periscope HD Would Like to Access the Camera"
- **Tap:** "OK" or "Allow"
- **Why needed:** Captures video (we use audio, but camera must be enabled)

**Permission 2: Microphone Access**
- **Prompt:** "Periscope HD Would Like to Access the Microphone"
- **Tap:** "OK" or "Allow"
- **Why needed:** THIS IS CRITICAL - captures audio for bark/bird detection

**Permission 3: Local Network Access**
- **Prompt:** "Periscope HD Would Like to Find and Connect to Devices on Your Local Network"
- **Tap:** "OK" or "Allow"
- **Why needed:** Allows Raspberry Pi to discover and connect to the stream

#### Step 6: First-Time App Configuration

When you first open Periscope HD, you'll see the main camera view:

1. **Camera preview** - Shows what the iPhone camera sees
2. **Red "LIVE" indicator** at the top when streaming
3. **Settings gear icon** at the bottom - This is what we need!

---

### Part 2: Configuring Periscope HD for Audio Streaming

#### Step 7: Access Settings

1. **Tap the gear icon** (⚙️) at the bottom of the screen
2. **Settings screen opens** - You'll see several options

#### Step 8: Configure Video Settings (Optional but Recommended)

Even though we primarily want audio, proper video settings ensure stable streaming:

1. **Scroll to "Video" section**
2. **Resolution:** Set to **"720p"** (default - good balance of quality and performance)
3. **Frame Rate:** Set to **"30 fps"** (default - smooth video)
4. **Bitrate:** Set to **"2 Mbps"** (default - good quality without overwhelming WiFi)

#### Step 9: Configure Audio Settings (CRITICAL!)

1. **Scroll to "Audio" section**
2. **Audio Enabled:** Make sure this is **ON** (toggle should be green/blue)
   - If it's OFF (gray), tap the toggle to turn it ON
3. **Audio Codec:** Should show **"G.711"** (this is automatic, can't change)
4. **Sample Rate:** Should show **"8000 Hz"** (automatic)

**VERIFICATION:** If you don't see an "Audio Enabled" toggle, the audio is always on by default in your version.

#### Step 10: Configure Network Settings

1. **Scroll to "Network" section**
2. **Port:** Should show **"8554"** (default RTSP port - don't change unless you have conflicts)
3. **Transport:** Set to **"UDP"** (default - lowest latency)
   - If you have connection issues later, can try "TCP" for stability
4. **Bonjour:** Should be **ON** (allows auto-discovery)

#### Step 11: Get Your RTSP URL (IMPORTANT!)

This is the address your Raspberry Pi will use to connect.

1. **Scroll to top of Settings screen**
2. **Look for "RTSP URL"** or "Stream URL" section
3. **You'll see a URL like this:**
   ```
   rtsp://192.168.1.XXX:8554/live.sdp
   ```

4. **WRITE THIS DOWN!** You'll need it later. Example:
   - If your iPhone IP is 192.168.1.150, the URL is:
   - `rtsp://192.168.1.150:8554/live.sdp`

**HOW TO FIND YOUR IPHONE'S IP ADDRESS:**
- It's shown in the Periscope HD settings screen
- OR go to: iPhone Settings → WiFi → Tap the (i) icon next to connected network → See "IP Address"

#### Step 12: Exit Settings

1. **Tap "Done"** or **tap outside the settings area** to go back to main screen
2. **Settings are automatically saved**

---

### Part 3: Starting the Stream

#### Step 13: Start Broadcasting

1. **Tap the big red "Start" button** in the center of the screen
   - OR it might say "Go Live" or have a camera icon
2. **The button turns to "Stop"** and becomes red
3. **"LIVE" indicator appears** at the top in red
4. **Stream is now active!** Your iPhone is broadcasting audio and video over the network

**WHAT YOU'LL SEE:**
- Live camera preview
- Red "LIVE" indicator at top
- Stream duration timer counting up
- Network indicator showing data transfer

#### Step 14: Lock Screen Behavior (IMPORTANT!)

**KEY POINT:** Periscope HD continues streaming even when the screen locks!

1. **You can press the side button** to lock your iPhone screen (saves battery on display)
2. **The stream continues** in the background
3. **To verify it's still running:**
   - Press side button to wake screen
   - You should see "LIVE" indicator still active

---

### Part 4: Connecting Raspberry Pi to the Stream

Now we configure your Raspberry Pi to capture the audio from your iPhone's RTSP stream.

#### Step 15: SSH into Your Raspberry Pi

From your computer:

**On Mac/Linux:**
```bash
ssh pi@<your-pi-ip-address>
```

**On Windows (PowerShell or Command Prompt):**
```powershell
ssh pi@<your-pi-ip-address>
```

**Example:** If your Pi's IP is 192.168.1.100:
```bash
ssh pi@192.168.1.100
```

**Enter password when prompted** (default is usually "raspberry" but you may have changed it)

#### Step 16: Install Required Tools

```bash
# Update package list
sudo apt-get update

# Install FFmpeg (handles RTSP streams)
sudo apt-get install -y ffmpeg

# Install GStreamer (alternative streaming tool)
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-rtsp

# Install ALSA utilities (audio system)
sudo apt-get install -y alsa-utils
```

**This takes about 5 minutes.**

#### Step 17: Test the RTSP Connection

First, let's verify we can reach the iPhone stream:

```bash
# Replace with YOUR iPhone's RTSP URL
ffprobe rtsp://192.168.1.150:8554/live.sdp
```

**EXPECTED OUTPUT (Good):**
```
Input #0, rtsp, from 'rtsp://192.168.1.150:8554/live.sdp':
  Duration: N/A, start: 0.000000, bitrate: N/A
    Stream #0:0: Video: h264, 1280x720, 30 fps
    Stream #0:1: Audio: pcm_mulaw, 8000 Hz, mono
```

**IF YOU SEE THIS:** ✅ Connection successful! Audio stream detected!

**IF YOU SEE ERRORS:**
- ❌ "Connection refused" → Check iPhone IP address
- ❌ "Timeout" → Check WiFi network (iPhone and Pi on same network?)
- ❌ "No route to host" → Check firewall settings

#### Step 18: Test Audio Capture

Let's record 5 seconds of audio to verify it works:

```bash
# Record 5-second test
ffmpeg -i rtsp://192.168.1.150:8554/live.sdp \
       -t 5 \
       -vn \
       -acodec pcm_s16le \
       -ar 16000 \
       test_capture.wav
```

**What this does:**
- `-i` = input from RTSP stream
- `-t 5` = record for 5 seconds
- `-vn` = ignore video (we only want audio)
- `-acodec pcm_s16le` = audio format (16-bit PCM)
- `-ar 16000` = resample to 16kHz (what our detector needs)

**You should see:**
```
frame=  150 fps= 30 q=-0.0 Lsize=     512kB time=00:00:05.00
```

**Play it back:**
```bash
aplay test_capture.wav
```

**Can you hear audio from your iPhone?** If yes, SUCCESS! ✅

#### Step 19: Create Virtual Audio Device

We need to create a "virtual" audio device that our dog bark detector can read from:

```bash
# Create ALSA loopback device
sudo modprobe snd-aloop

# Make it permanent (load on boot)
echo "snd-aloop" | sudo tee -a /etc/modules

# Verify it was created
arecord -l
```

**You should see:**
```
card 1: Loopback [Loopback], device 0: Loopback PCM [Loopback PCM]
```

**Note the card number** (in this example it's card 1)

#### Step 20: Create Audio Streaming Service

We'll create a systemd service that continuously pipes iPhone audio to the virtual device:

```bash
sudo nano /etc/systemd/system/iphone-audio-stream.service
```

**Paste this content** (update the RTSP URL with YOUR iPhone IP):

```ini
[Unit]
Description=iPhone Periscope HD Audio Stream
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Restart=always
RestartSec=10

# Replace 192.168.1.150 with YOUR iPhone IP address!
ExecStart=/usr/bin/ffmpeg \
    -rtsp_transport udp \
    -i rtsp://192.168.1.150:8554/live.sdp \
    -vn \
    -acodec pcm_s16le \
    -ar 16000 \
    -ac 1 \
    -f alsa \
    hw:1,0

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Save and exit:** Press `Ctrl+O`, then `Enter`, then `Ctrl+X`

**What this service does:**
- Continuously captures audio from iPhone RTSP stream
- Converts to 16kHz mono (perfect for our detector)
- Pipes it to ALSA loopback device (hw:1,0)
- Auto-restarts if connection drops
- Starts automatically on boot

#### Step 21: Enable and Start the Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable iphone-audio-stream.service

# Start service now
sudo systemctl start iphone-audio-stream.service

# Check status
sudo systemctl status iphone-audio-stream.service
```

**EXPECTED OUTPUT (Good):**
```
● iphone-audio-stream.service - iPhone Periscope HD Audio Stream
     Loaded: loaded (/etc/systemd/system/iphone-audio-stream.service; enabled)
     Active: active (running) since Wed 2024-03-15 10:30:00 PDT
```

**If you see "active (running)" in GREEN:** ✅ Success!

#### Step 22: Verify Audio is Flowing

```bash
# Record from loopback device for 5 seconds
arecord -D hw:1,1 -f S16_LE -r 16000 -c 1 -d 5 verification.wav

# Play it back
aplay verification.wav
```

**Can you hear audio captured from your iPhone?** If yes, PERFECT! ✅

---

### Part 5: Configuring the Dog Bark Detector

#### Step 23: Update Detector Configuration

```bash
nano ~/Air-quality-sensors/scripts/dog_bark_detector.py
```

**Find this section** (around line 40-50):

```python
# Audio Settings
AUDIO_DEVICE_INDEX = None  # None = default device, or specify device number
```

**Change it to:**

```python
# Audio Settings
# Using ALSA loopback from iPhone Periscope HD stream
AUDIO_DEVICE_INDEX = None  # Will use default ALSA device
SAMPLE_RATE = 16000  # Hz (already set correctly)
```

**Also find this section:**

```python
# IMPORTANT: If using ALSA loopback device, specify like this:
# AUDIO_DEVICE_INDEX = 1  # Card 1, subdevice 1 (loopback input)
```

**Change it to:**

```python
# Using ALSA loopback from Periscope HD iPhone stream
AUDIO_DEVICE_INDEX = (1, 1)  # Card 1, subdevice 1 (loopback input)
```

**Save:** Press `Ctrl+O`, Enter, `Ctrl+X`

#### Step 24: Update Dog Bark Detector to Use ALSA Device Name

Actually, let's use a more reliable method - device name instead of number:

```bash
nano ~/Air-quality-sensors/scripts/dog_bark_detector.py
```

**Find the section where the stream opens** (around line 450):

```python
self.stream = self.audio.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    input_device_index=AUDIO_DEVICE_INDEX,
    frames_per_buffer=CHUNK_SIZE
)
```

**Change to:**

```python
# Open audio stream from ALSA loopback device
self.stream = self.audio.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    input_device_index=self._get_loopback_device_index(),
    frames_per_buffer=CHUNK_SIZE
)
```

**Then add this method around line 400:**

```python
def _get_loopback_device_index(self):
    """Find the ALSA loopback device index"""
    for i in range(self.audio.get_device_count()):
        info = self.audio.get_device_info_by_index(i)
        if 'Loopback' in info['name'] and info['maxInputChannels'] > 0:
            logger.info(f"Using audio device: {info['name']} (index {i})")
            return i

    # Fallback to default
    logger.warning("Loopback device not found, using default")
    return AUDIO_DEVICE_INDEX
```

**Save:** Ctrl+O, Enter, Ctrl+X

---

### Part 6: iPhone Placement and Settings

#### Step 25: Optimal iPhone Positioning

**For Dog Bark Detection:**
- **Location:** Place near where barking is loudest
  - Near back door if dogs are in backyard
  - In central room if detecting indoor barking
  - Near fence line if detecting neighbor's dogs

- **Height:** 3-5 feet off ground
  - Eye level is ideal
  - Don't place on floor (muffled sound)
  - Don't place too high (sound attenuates)

- **Orientation:** Camera facing the area you want to monitor
  - Doesn't matter much for audio, but nice to have video too
  - Point away from direct sunlight (prevents overheating)

**For Bird Detection:**
- **Location:** Near windows facing bird-active areas
  - Near bird feeders
  - Facing trees and bushes
  - Open yard areas

- **Height:** Window level
  - Look outside to where birds typically are

- **Multiple iPhones:** Use multiple old iPhones for multi-zone coverage!

#### Step 26: Power and Charging

**CRITICAL:** iPhone must stay plugged in 24/7

1. **Plug in Lightning cable** to iPhone
2. **Connect to wall charger** (use official Apple charger or quality third-party)
3. **Verify charging:**
   - Battery icon shows lightning bolt
   - Screen shows "Charging" when you wake it

**TIP:** Use a long Lightning cable (6-10 feet) for flexible positioning

#### Step 27: Prevent Screen Burn-In and Battery Issues

**Configure iPhone Settings:**

1. **Open Settings app** on iPhone
2. **Go to "Display & Brightness"**
3. **Set "Auto-Lock" to "Never"**
   - This prevents stream from stopping
   - Screen will stay on (dims automatically in Periscope HD)

4. **Go back to Settings main screen**
5. **Go to "Battery"**
6. **Turn OFF "Low Power Mode"**
   - Low Power Mode can interfere with streaming

7. **Turn OFF "Optimized Battery Charging"**
   - Settings → Battery → Battery Health → Optimized Battery Charging → OFF
   - Reason: Prevents charge limiting that might cause shutdown

**Optional but Recommended:**

1. **Settings → General → Background App Refresh**
2. **Ensure it's ON globally**
3. **Find "Periscope HD" in the list**
4. **Make sure toggle is ON**

#### Step 28: Network Stability

**For most reliable streaming:**

1. **Use 5GHz WiFi if available:**
   - Settings → WiFi → Tap (i) next to your network
   - If it shows "5GHz" or "WiFi 6" → Good!
   - 2.4GHz works but can be choppy

2. **Position iPhone near WiFi router:**
   - Ideally same room or adjacent room
   - Strong signal = stable stream

3. **Optional: Assign static IP to iPhone:**
   - In your router settings, assign permanent IP to iPhone
   - Prevents IP address changes that break connection
   - (Router-specific - Google "[your router model] static IP assignment")

---

### Part 7: Testing Everything Together

#### Step 29: Full System Test

Now let's make sure everything works end-to-end!

**Test 1: Verify iPhone is Streaming**

On iPhone:
1. Open Periscope HD
2. Check for red "LIVE" indicator
3. Stream duration should be counting up

**Test 2: Verify Raspberry Pi is Receiving**

On Raspberry Pi:
```bash
# Check stream service status
sudo systemctl status iphone-audio-stream.service

# Should show "active (running)"
```

**Test 3: Verify Audio Flow**

```bash
# Record 5 seconds from loopback
arecord -D hw:1,1 -f S16_LE -r 16000 -c 1 -d 5 fulltest.wav

# During recording, make noise near iPhone (clap, talk, etc.)

# Play back
aplay fulltest.wav

# You should hear the sounds you made!
```

**Test 4: Test Dog Bark Detection**

```bash
# Start detector manually to see live output
cd ~/audio_detection
source venv/bin/activate
python3 ~/Air-quality-sensors/scripts/dog_bark_detector.py
```

**While it's running:**
1. Play dog barking sounds from YouTube on another device
2. Hold it near your iPhone
3. **Watch the terminal** - you should see:
```
[2024-03-15 14:30:45] DOG BARK DETECTED - Confidence: 0.87 - Decibels: 72dB
```

Press `Ctrl+C` to stop when done testing.

**Test 5: Verify MQTT Messages**

In another terminal/SSH session:
```bash
mosquitto_sub -h localhost -t "audio/#" -v
```

You should see real-time messages when barks are detected!

#### Step 30: Enable Automatic Startup

If all tests pass, enable the bark detector to run automatically:

```bash
# Start service
sudo systemctl start dog_bark_detector.service

# Enable auto-start on boot
sudo systemctl enable dog_bark_detector.service

# Verify running
sudo systemctl status dog_bark_detector.service
```

---

### Part 8: Monitoring and Maintenance

#### Daily Monitoring

**Check iPhone:**
- Still showing "LIVE" indicator?
- Still plugged in and charging?
- Warm but not hot? (Some warmth is normal)

**Check Raspberry Pi:**
```bash
# Check services
sudo systemctl status iphone-audio-stream.service
sudo systemctl status dog_bark_detector.service

# Both should show "active (running)"
```

**Check Home Assistant:**
- Open dashboard: http://your-pi-ip:8123
- Navigate to Audio Detection dashboard
- See live data updating?

#### Weekly Maintenance

**Every Sunday:**
1. **Restart iPhone** (good practice)
   - Hold Side button + Volume button
   - "Slide to Power Off"
   - Wait 30 seconds
   - Turn back on
   - Re-open Periscope HD and start stream

2. **Check storage space:**
```bash
df -h /mnt/usb
```

3. **Review CSV exports:**
```bash
ls -lh ~/audio_detection/csv_exports/
```

#### Monthly Maintenance

**Once per month:**
1. **Clean iPhone camera lens** (for video quality)
2. **Check Lightning cable** for damage
3. **Backup audio recordings:**
```bash
# From your computer
scp -r pi@your-pi-ip:/mnt/usb/bark_audio/recordings ~/backup/
```

---

## Troubleshooting

### Problem: "Connection Refused" Error

**Symptom:** Can't connect to RTSP stream from Raspberry Pi

**Solutions:**

1. **Verify iPhone and Pi are on same WiFi network:**
   - iPhone: Settings → WiFi → Check network name
   - Pi: `hostname -I` → Should be same subnet (e.g., both 192.168.1.x)

2. **Check iPhone IP address hasn't changed:**
   - In Periscope HD settings, look at RTSP URL
   - Update service if IP changed:
   ```bash
   sudo nano /etc/systemd/system/iphone-audio-stream.service
   # Update IP address
   sudo systemctl daemon-reload
   sudo systemctl restart iphone-audio-stream.service
   ```

3. **Verify Periscope HD is running:**
   - Check for red "LIVE" indicator on iPhone
   - If not, tap Start button

4. **Try TCP instead of UDP:**
   - Edit service: `sudo nano /etc/systemd/system/iphone-audio-stream.service`
   - Change `-rtsp_transport udp` to `-rtsp_transport tcp`
   - Restart service

### Problem: Audio is Choppy or Cutting Out

**Symptom:** Audio has gaps, stutters, or drops

**Solutions:**

1. **Check WiFi signal strength:**
   - Move iPhone closer to router
   - Or move router closer to iPhone

2. **Switch to 5GHz WiFi:**
   - Less interference than 2.4GHz
   - Faster, more reliable

3. **Reduce WiFi interference:**
   - Move away from microwave ovens
   - Move away from cordless phones
   - Other WiFi networks on same channel?

4. **Increase buffer size in detector:**
   ```bash
   nano ~/Air-quality-sensors/scripts/dog_bark_detector.py
   ```
   Find:
   ```python
   CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
   ```
   Change to:
   ```python
   CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION * 2)  # Double buffer
   ```

5. **Check CPU usage on Pi:**
   ```bash
   top
   ```
   If CPU is maxed out, Pi may be struggling

### Problem: iPhone Stream Stops After Screen Locks

**Symptom:** Stream works but stops when iPhone screen turns off

**Solution:**

1. **Disable Auto-Lock:**
   - Settings → Display & Brightness → Auto-Lock → Never

2. **Ensure Background App Refresh is ON:**
   - Settings → General → Background App Refresh → ON
   - Scroll down to Periscope HD → ON

3. **Disable Low Power Mode:**
   - Settings → Battery → Low Power Mode → OFF

4. **Keep iPhone plugged in** - Battery saver features can interfere

### Problem: No Audio Detected by Bark Detector

**Symptom:** Stream is working but detector sees no audio

**Solution:**

1. **Verify loopback device:**
   ```bash
   arecord -l
   ```
   Look for "Loopback" device

2. **Test loopback directly:**
   ```bash
   arecord -D hw:1,1 -f S16_LE -r 16000 -c 1 -d 5 test.wav
   aplay test.wav
   ```

3. **Check detector configuration:**
   ```bash
   nano ~/Air-quality-sensors/scripts/dog_bark_detector.py
   ```
   Verify `AUDIO_DEVICE_INDEX` is correct

4. **Check service logs:**
   ```bash
   sudo journalctl -u dog_bark_detector.service -f
   ```
   Look for audio device errors

### Problem: iPhone Gets Too Hot

**Symptom:** iPhone becomes very warm during streaming

**Solutions:**

1. **Remove iPhone case** - Allows heat dissipation

2. **Position away from direct sunlight**

3. **Point at cooler area** or use small fan

4. **Reduce video quality:**
   - Periscope HD Settings → Video → Resolution → 480p
   - We mainly need audio anyway

5. **iPhone overheating protection:**
   - If iPhone gets too hot, it will automatically stop
   - Move to cooler location

### Problem: Stream Drops During Night

**Symptom:** Works during day but fails overnight

**Solutions:**

1. **Disable iOS "Attention Aware Features":**
   - Settings → Face ID & Passcode → Attention Aware Features → OFF
   - (iPhone 7 doesn't have this, but other models do)

2. **Prevent iOS sleep:**
   - Keep plugged in (prevents battery-saving sleep)
   - Auto-Lock set to Never

3. **Check router sleep/energy saving:**
   - Some routers reduce power at night
   - Disable "Green Ethernet" or similar features in router settings

4. **Ensure iPhone doesn't auto-update overnight:**
   - Settings → General → Software Update → Automatic Updates → OFF
   - Or set update time to when you can monitor

### Problem: RTSP URL Changes

**Symptom:** Was working, suddenly stops, IP address changed

**Solution:**

**Option 1: Assign Static IP in Router (Best)**

1. Find iPhone MAC address:
   - Settings → General → About → WiFi Address
2. Log into router admin panel
3. Assign static IP to that MAC address
4. (Router-specific steps - consult router manual)

**Option 2: Update Service with New IP**

```bash
# Get new iPhone IP from Periscope HD settings
# Then update service:
sudo nano /etc/systemd/system/iphone-audio-stream.service

# Change the RTSP URL line
# Save and restart:
sudo systemctl daemon-reload
sudo systemctl restart iphone-audio-stream.service
```

**Option 3: Use mDNS/Bonjour Name (Advanced)**

```bash
# Instead of IP address, use iPhone hostname
# Example: rtsp://iphone.local:8554/live.sdp
# Requires Bonjour enabled on Pi:
sudo apt-get install avahi-daemon
```

---

## Advanced Configuration

### Using Multiple iPhones

Want coverage of multiple areas? Use multiple old iPhones!

**Setup:**

1. **Install Periscope HD on each iPhone**
2. **Each iPhone gets unique RTSP URL** (different IP addresses)
3. **Create separate services for each:**

```bash
# iPhone 1 (Backyard)
sudo cp /etc/systemd/system/iphone-audio-stream.service \
       /etc/systemd/system/iphone-backyard-stream.service

# iPhone 2 (Front Yard)
sudo cp /etc/systemd/system/iphone-audio-stream.service \
       /etc/systemd/system/iphone-frontyard-stream.service

# Edit each to point to different iPhone IP and different loopback device
```

### Recording Video Too

Want video recordings along with audio?

**Modify the streaming service:**

```bash
sudo nano /etc/systemd/system/iphone-audio-stream.service
```

**Change ExecStart to:**

```bash
ExecStart=/usr/bin/ffmpeg \
    -rtsp_transport udp \
    -i rtsp://192.168.1.150:8554/live.sdp \
    -c:v copy \
    -c:a pcm_s16le \
    -ar 16000 \
    -ac 1 \
    -f tee \
    "[f=alsa]hw:1,0|[f=segment:segment_time=3600]/mnt/usb/video/%%Y%%m%%d_%%H%%M%%S.mp4"
```

This saves video in 1-hour segments while still streaming audio to detector!

### Battery Backup

Power outages? Add UPS:

**Recommended UPS for this project:**
- APC Back-UPS 600VA (~$60) - Powers Pi and iPhone charger for 2-3 hours
- CyberPower CP1500PFCLCD (~$200) - Powers full setup for 4-6 hours

---

## Conclusion

You now have a professional-grade audio streaming setup using your iPhone 7 and Periscope HD!

**What's Running:**
- ✅ iPhone streaming RTSP with audio
- ✅ Raspberry Pi capturing audio continuously
- ✅ ALSA loopback device for detector access
- ✅ Services auto-start on boot
- ✅ Reconnects automatically if disconnected

**Next Steps:**
- Continue with main setup guide for BirdNET and Home Assistant
- Test dog bark detection
- Configure dashboards
- Set up CSV exports

**You're ready to detect those barks and birds!** 🐕🐦

---

## Sources

- [Periscope HD App Store Page](https://apps.apple.com/us/app/periscope-hd-h-264-rtsp-cam/id1095600218)
- [Complete Periscope App IP Camera Setup Guide](https://www.ispyconnect.com/camera/periscope-app)
- [Using a Mobile Device as an IP Camera](https://support.nvplay.com/hc/en-gb/articles/38795267516441-Using-a-Mobile-Device-as-an-IP-Camera)
- [ZipZapMac Periscope HD Guide](https://zipzapmac.com/periscopehd)
