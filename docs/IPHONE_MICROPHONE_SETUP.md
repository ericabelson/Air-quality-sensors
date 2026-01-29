# iPhone 7 as Network Microphone Setup Guide

## Complete Step-by-Step Instructions

This guide shows you exactly how to turn your iPhone 7 into a wireless microphone for the dog bark and bird detection system.

---

## Table of Contents

1. [Method 1: AudioRelay (Recommended)](#method-1-audiorelay-recommended)
2. [Method 2: Microphone Live](#method-2-microphone-live)
3. [Method 3: USB Connection](#method-3-usb-connection)
4. [Troubleshooting](#troubleshooting)
5. [Best Placement for Detection](#best-placement-for-detection)

---

## Method 1: AudioRelay (Recommended) ⭐

AudioRelay is the easiest and most reliable method. It creates a WiFi audio stream from your iPhone to the Raspberry Pi.

### Step 1: Install AudioRelay App on iPhone

1. **Open the App Store** on your iPhone 7
2. **Tap the search icon** (magnifying glass) at the bottom
3. **Type:** `AudioRelay`
4. **Look for:** "AudioRelay: Stream PC Audio" by Grishka
5. **Tap "GET"** then **"INSTALL"**
6. **Enter your Apple ID password** or use Face ID if prompted
7. **Wait for download** to complete (about 1 minute)
8. **Tap "OPEN"** when installation finishes

### Step 2: Configure AudioRelay on iPhone

1. **Open AudioRelay app**
2. **Allow microphone access** when prompted (tap "OK")
3. **Allow local network access** when prompted (tap "Allow")
4. **Grant notification permissions** (tap "Allow")

The app is now ready! Don't start streaming yet - first we need to set up the server on the Raspberry Pi.

### Step 3: Install AudioRelay Server on Raspberry Pi

SSH into your Raspberry Pi from your computer:

**On Mac/Linux:**
```bash
ssh pi@<your-pi-ip-address>
```

**On Windows (PowerShell):**
```powershell
ssh pi@<your-pi-ip-address>
```

Replace `<your-pi-ip-address>` with your Pi's actual IP (like `192.168.1.100`)

Once connected, run these commands:

```bash
# Create directory
mkdir -p ~/audiorelay
cd ~/audiorelay

# Download AudioRelay for ARM64
wget https://github.com/grishka/AudioRelay/releases/latest/download/audiorelay-server-linux-arm64.tar.gz

# Extract
tar -xzf audiorelay-server-linux-arm64.tar.gz

# Make executable
chmod +x audiorelay
```

### Step 4: Start AudioRelay Server

```bash
cd ~/audiorelay
./audiorelay
```

You should see output like:
```
AudioRelay server v1.2.0
Listening on port 59100
Waiting for connections...
```

**Keep this terminal window open!**

### Step 5: Connect iPhone to Raspberry Pi

Now go back to your iPhone:

1. **Open AudioRelay app**
2. **Tap the "Connect" button** (it's big and blue)
3. **Wait 5-10 seconds** for the Pi to appear
4. **You should see:** "raspberrypi" or your Pi's hostname in the device list
5. **Tap on it** to connect
6. **You should see:** "Connected" with a green checkmark

### Step 6: Start Streaming Audio

1. **Tap the "Record" button** (red circle icon)
2. **iPhone will ask permission to record audio** - tap "Allow"
3. **You should see:** Waveform animation showing audio is being captured
4. **The app shows:** "Streaming to raspberrypi"

**That's it!** Your iPhone is now streaming audio to the Raspberry Pi!

### Step 7: Configure Audio Input on Raspberry Pi

The AudioRelay stream appears as a virtual audio device. To use it with the bark detector:

```bash
# List audio devices
arecord -l
```

You should see an entry like:
```
card 2: AudioRelay [AudioRelay], device 0: USB Audio [USB Audio]
```

Note the card number (in this example, it's card 2).

Edit the dog bark detector script to use this device:

```bash
nano ~/audio_detection/dog_bark_detector.py
```

Find the line:
```python
AUDIO_DEVICE_INDEX = None
```

Change it to:
```python
AUDIO_DEVICE_INDEX = 2  # Or whatever card number you saw
```

Save with `Ctrl+O`, then `Enter`, then exit with `Ctrl+X`.

### Step 8: Test the Setup

```bash
# Record 5 seconds of test audio
arecord -D plughw:2,0 -d 5 -f cd test.wav

# Play it back
aplay test.wav
```

You should hear the audio that was captured by your iPhone!

### Step 9: Keep iPhone Streaming 24/7

To prevent the iPhone from stopping the stream:

**iPhone Settings:**

1. **Open Settings app**
2. **Tap "Display & Brightness"**
3. **Tap "Auto-Lock"**
4. **Select "Never"** (this prevents screen from turning off)

5. **Go back to Settings**
6. **Tap "Battery"**
7. **Ensure "Low Power Mode" is OFF**

**Plug in iPhone charger!** The iPhone should stay plugged in 24/7 to keep streaming.

**Position iPhone near windows** where you want to detect dog barks and birds.

---

## Method 2: Microphone Live

Alternative method using Microphone Live app.

### Step 1: Install Microphone Live on iPhone

1. **Open App Store**
2. **Search for:** "Microphone Live"
3. **Install:** "Microphone Live" by Von Bruno
4. **Open the app**

### Step 2: Configure WiFi Streaming

1. **Tap "Settings"** (gear icon)
2. **Enable "WiFi Broadcasting"**
3. **Note the URL shown** (like `http://192.168.1.150:8080`)

### Step 3: Capture Stream on Raspberry Pi

```bash
# Install required tools
sudo apt-get install ffmpeg vlc

# Create capture script
cat > ~/audiorelay/capture_iphone.sh << 'EOF'
#!/bin/bash
# Capture audio from Microphone Live app
ffmpeg -i http://<IPHONE-IP>:8080/audio.wav -f alsa hw:0,0
EOF

chmod +x ~/audiorelay/capture_iphone.sh
```

Replace `<IPHONE-IP>` with your iPhone's IP address.

Run the script:
```bash
~/audiorelay/capture_iphone.sh
```

---

## Method 3: USB Connection

For a wired, more stable connection.

### Step 1: Install USB Audio Tools

```bash
sudo apt-get update
sudo apt-get install -y \
    usbmuxd \
    libimobiledevice-utils \
    libimobiledevice6 \
    libusbmuxd-tools
```

### Step 2: Connect iPhone via USB

1. **Plug Lightning cable into iPhone**
2. **Plug USB end into Raspberry Pi**
3. **Unlock iPhone**
4. **Tap "Trust This Computer"** when prompted
5. **Enter iPhone passcode**

### Step 3: Verify Connection

```bash
# Check if iPhone is detected
ideviceinfo

# You should see iPhone details like:
# DeviceName: iPhone
# ProductType: iPhone9,1
# etc.
```

### Step 4: Use App to Stream Audio

Even with USB connection, you'll need to use one of the apps above (AudioRelay or Microphone Live) to stream audio. The USB connection just makes it more stable than WiFi.

---

## Troubleshooting

### iPhone Not Appearing in Device List

**Problem:** AudioRelay app doesn't show the Raspberry Pi

**Solutions:**
1. **Check WiFi:** Make sure iPhone and Pi are on the same WiFi network
   - iPhone: Settings > WiFi (note the network name)
   - Pi: Run `hostname -I` to see IP address

2. **Check firewall:** Disable firewall temporarily on Pi:
   ```bash
   sudo ufw disable
   ```
   Try connecting again, then re-enable:
   ```bash
   sudo ufw enable
   ```

3. **Restart AudioRelay server:**
   - Stop the server (Ctrl+C in terminal)
   - Start it again: `./audiorelay`

4. **Check server is running:**
   ```bash
   netstat -ln | grep 59100
   ```
   Should show the server listening on port 59100

### Audio Quality Issues

**Problem:** Audio is choppy or has delays

**Solutions:**
1. **Move iPhone closer to WiFi router**
2. **Use 5GHz WiFi instead of 2.4GHz** (if available)
   - iPhone Settings > WiFi > Tap (i) next to network
   - Make sure connected to 5GHz network
3. **Reduce WiFi interference:**
   - Move away from microwave ovens
   - Move away from cordless phones
4. **Consider USB connection instead** (Method 3)

### iPhone Keeps Stopping Stream

**Problem:** Stream stops after phone screen turns off

**Solutions:**
1. **Disable Auto-Lock:**
   - Settings > Display & Brightness > Auto-Lock > Never
2. **Keep iPhone plugged in** to charger
3. **Disable Low Power Mode:**
   - Settings > Battery > Low Power Mode > OFF
4. **Background App Refresh:**
   - Settings > General > Background App Refresh > Enable for AudioRelay

### No Audio Detected on Raspberry Pi

**Problem:** Server shows connection but no audio is captured

**Solutions:**
1. **Check audio device:**
   ```bash
   arecord -l
   ```
   Make sure AudioRelay device is listed

2. **Test audio capture:**
   ```bash
   arecord -D plughw:2,0 -d 5 test.wav
   aplay test.wav
   ```

3. **Check iPhone microphone:**
   - Make sure nothing is blocking the mic
   - Try recording in Voice Memos app to verify mic works

4. **Restart AudioRelay app** on iPhone:
   - Close app completely (swipe up from home screen)
   - Open app again
   - Reconnect to Pi

### Connection Keeps Dropping

**Problem:** Stream disconnects every few minutes

**Solutions:**
1. **Update AudioRelay app** to latest version
2. **Restart WiFi router**
3. **Assign static IP to iPhone:**
   - Settings > WiFi > Tap (i) next to network
   - Configure IP > Manual
   - Enter static IP, subnet, router
4. **Use Ethernet on Raspberry Pi** instead of WiFi
5. **Consider USB connection** for maximum stability

---

## Best Placement for Detection

### For Dog Bark Detection

**Indoor Placement:**
- **Near windows** where dog barking is loudest
- **In central location** of home for general coverage
- **Avoid:** Near fans, air conditioners, or noisy appliances

**Outdoor Placement (if weatherproof):**
- **In covered patio** or under eaves
- **Facing backyard** where dogs are most active
- **Protected from rain** and direct sunlight

### For Bird Detection

**Best Placement:**
- **Near windows** that face bird-active areas
- **Near bird feeders** for maximum detections
- **Open areas** with good sound transmission
- **Away from traffic noise** and human voices

### General Tips

1. **Height:** Place iPhone 3-5 feet off ground for best audio capture
2. **Angle:** Point microphone toward sound source
3. **Obstructions:** Clear line of "hearing" - no walls or furniture blocking
4. **Power:** Keep iPhone plugged into charger
5. **Temperature:** Avoid extreme heat or cold (phones shut down outside safe range)

---

## Mounting Options

### Simple Phone Stand

Use a phone holder or stand to position the iPhone:
- Car phone mount with suction cup
- Desk phone stand
- DIY stand made from cardboard box

### Permanent Installation

For long-term deployment:
- Weather-resistant phone case
- Mounted with adhesive strips or screws
- Run charging cable through wall if needed

### Example Setup

```
┌─────────────────┐
│   Window        │
│                 │
│  ┌──────────┐  │
│  │ iPhone 7 │  │  ← Position here
│  │          │  │     (on windowsill)
│  └──────────┘  │
│       ↓         │
│   [Charger]    │
└─────────────────┘
```

---

## Testing Your Setup

### Quick Audio Test

1. **Start AudioRelay** on iPhone
2. **Connect to Pi**
3. **Clap your hands** loudly near iPhone
4. **On Raspberry Pi terminal:**
   ```bash
   mosquitto_sub -h localhost -t "audio/#" -v
   ```
5. **You should see:** Real-time decibel readings changing when you make noise

### Dog Bark Test

1. **Play dog barking sound** from YouTube on another device
2. **Hold it near iPhone**
3. **Check Home Assistant** dashboard - should show bark detection!

### Bird Call Test

1. **Play bird calls** from YouTube (try Robin, Cardinal, etc.)
2. **Hold near iPhone**
3. **Check BirdNET-Pi** web interface for detections
4. **Check Home Assistant** for bird detection notifications

---

## Daily Operation

Once everything is set up:

1. **iPhone stays plugged in** 24/7
2. **AudioRelay app stays open** and streaming
3. **Raspberry Pi runs** detection automatically
4. **Home Assistant** shows real-time data
5. **CSV files** exported daily at midnight

**That's it!** The system runs fully automatically.

---

## Advanced: Multiple iPhones

You can use multiple iPhones for coverage of different areas!

### Setup Multiple Streams

Each iPhone needs:
1. Own AudioRelay app running
2. Unique audio device on Pi
3. Separate detector instance (or multi-input configuration)

### Example Configuration

```
iPhone 1 (Backyard) → AudioRelay card 2 → Bark Detector Instance 1
iPhone 2 (Front yard) → AudioRelay card 3 → Bark Detector Instance 2
```

---

## Conclusion

Your iPhone 7 is now a powerful network microphone for audio detection!

**Recommended setup:**
- ✅ Method 1 (AudioRelay) for WiFi streaming
- ✅ Keep iPhone plugged in
- ✅ Disable auto-lock
- ✅ Position near windows
- ✅ Monitor with Home Assistant

If you have any issues, check the Troubleshooting section above!
