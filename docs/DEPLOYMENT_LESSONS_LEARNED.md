# Deployment Lessons Learned: Odroid C1+ Air Quality Sensor System

**Date:** December 29, 2025
**System:** Odroid C1+ with Arduino Nano + 7 Sensors
**Outcome:** ✅ FULLY OPERATIONAL - All sensors reading, data stored locally, MQTT publishing to Home Assistant

> **Note:** This document uses placeholder values like `YOUR_HA_IP`, `YOUR_USER`, etc.
> Replace these with your actual values from `config.env` in the repository root.

---

## Table of Contents

1. [What Worked](#what-worked)
2. [What Didn't Work](#what-didnt-work)
3. [Critical Configuration Steps](#critical-configuration-steps)
4. [Dependencies and Python 3.6 Compatibility](#dependencies-and-python-36-compatibility)
5. [MQTT Configuration Details](#mqtt-configuration-details)
6. [Serial Port and USB Issues](#serial-port-and-usb-issues)
7. [Troubleshooting Decision Tree](#troubleshooting-decision-tree)
8. [Exact Configuration Files Needed](#exact-configuration-files-needed)
9. [Common Pitfalls for Next Deployment](#common-pitfalls-for-next-deployment)

---

## What Worked

### ✅ Complete Success Path

1. **OS Image:** Ubuntu 18.04.3 minimal with kernel 3.10.107-13 (official Hardkernel)
2. **Flashing Tool:** Balena Etcher v1.19.x
3. **Network:** Ethernet for initial setup, then WiFi (nmcli NetworkManager)
4. **System Updates:** Waited for apt.systemd.daily automatic updates to complete (3-5 minutes)
5. **User Permissions:** cerberus user with sudo and dialout groups
6. **Python Packages:** pyserial, paho-mqtt, pynmea2, getmac, netifaces, PyYAML, requests
7. **Sensor Reading:** All 7 sensors detect and stream data via Arduino on /dev/ttyUSB0
8. **CSV Storage:** Data properly formatted with timestamps, stored in `/home/YOUR_USER/utData/raw/`
9. **JSON Output:** Latest values written to `.json` files every ~10 seconds
10. **MQTT Publishing:** Data published to `utsensing/*` topics successfully
11. **Auto-Startup:** Cron configured with `@reboot` and `*/10 * * * *` schedules
12. **Full System Reboot:** After reboot, nanoReader started automatically and sensors operational

### Data Collection Pipeline (Verified Working)

```
Arduino Sensors (I2C)
  → USB Serial (9600 baud)
    → /dev/ttyUSB0
      → nanoReader.py (parses MINTS format)
        → mintsSensorReader.py (splits by sensor)
          → CSV files (stored locally)
          → JSON files (latest values)
            → mintsLatest.py (MQTT publishing)
              → Home Assistant at YOUR_HA_IP:1883
```

**CSV File Format (Verified):**
```
dateTime,co2,temperature,humidity
2025-12-29 22:10:04.333705,304,22,49
2025-12-29 22:10:14.374152,0,22,49
```

**JSON File Format (Verified):**
```json
{"dateTime": "2025-12-29 22:16:23.713896", "co2": "0", "temperature": "22", "humidity": "49"}
```

**MQTT Topic Format (Verified):**
```
utsensing/SCD30 → {"dateTime": "2025-12-29 22:16:23.713896", "co2": "0", "temperature": "22", "humidity": "49"}
utsensing/BME680 → {"dateTime": "...", "temperature": "...", "pressure": "...", "humidity": "...", "gas": "..."}
utsensing/SGP30 → {"dateTime": "...", "TVOC": "...", "eCO2": "...", "rawEthanol": "..."}
utsensing/MGSV2 → {"dateTime": "...", "NO2": "...", "C2H5OH": "...", "VOC": "...", "CO": "..."}
utsensing/SEN0321 → {"dateTime": "...", "Ozone": "..."}
utsensing/PMSA003I → {"dateTime": "...", "pm1Standard": "...", "pm2p5Standard": "...", ...}
utsensing/MQ136 → {"dateTime": "...", "rawH2s": "..."}
```

---

## What Didn't Work

### ❌ Python 3.6 Dependency Issues

**Problem:** Original `requirements.txt` specified versions incompatible with Python 3.6 (Ubuntu 18.04 default).

**Failed Versions:**
- `requests>=2.28.0` - Doesn't support Python 3.6
- `numpy>=1.21.0` - Requires Cython to compile from source, fails on ARM hardware

**Error Messages:**
```
No matching distribution found for requests>=2.28.0
ModuleNotFoundError: No module named 'Cython'
RuntimeError: Running cythonize failed!
```

**Solution Applied:**
- Changed `requirements.txt` to `requests>=2.27.0` (last version supporting Python 3.6)
- Changed `numpy>=1.16.0` (compatible with Python 3.6)
- Removed numpy from installation (it's optional, not needed for sensor reading)

**Correct Installation:**
```bash
pip3 install pyserial pynmea2 getmac netifaces PyYAML paho-mqtt requests
# Skip numpy - it's optional and causes build failures on ARM
```

---

### ❌ PyYAML 6.0+ Breaking Change

**Problem:** PyYAML 6.0+ requires explicit `Loader` parameter in `yaml.load()`.

**Error Message:**
```
TypeError: load() missing 1 required positional argument: 'Loader'
```

**Location:** `firmware/xu4Mqqt/mintsXU4/mintsLatest.py` line 22

**Original Code (BROKEN):**
```python
credentials = yaml.load(open(mqttCredentialsFile))
```

**Fixed Code (WORKING):**
```python
credentials = yaml.safe_load(open(mqttCredentialsFile))
```

**Why:** PyYAML 6.0 disabled the unsafe loader by default for security. `safe_load()` is the recommended approach.

---

### ❌ TLS Configuration for Local MQTT Broker

**Problem:** mintsLatest.py had TLS configuration (lines 53-56) enabled for local Mosquitto broker.

**Error Behavior:** Silent failure - connection appeared to work but no data published.

**Location:** `firmware/xu4Mqqt/mintsXU4/mintsLatest.py` lines 53-56

**Original Code (BROKEN):**
```python
mqtt_client.tls_set(ca_certs=tlsCert, certfile=None,
                    keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
mqtt_client.tls_insecure_set(False)
```

**Fixed Code (WORKING):**
```python
# Commented out TLS for local MQTT broker
# mqtt_client.tls_set(ca_certs=tlsCert, certfile=None,
#                     keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
#                     tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
# mqtt_client.tls_insecure_set(False)
```

**Why:** Local Mosquitto on same network should not use TLS. TLS is for external/internet-facing brokers only.

---

### ❌ Serial Console Output Appears Garbled

**Problem:** During nanoReader.py foreground execution, console prints appear corrupted/garbled.

**Example Output:**
```
itOSD002:2:0
================
itBE8>42:010:4.00:itOSP0>:0:42291:mns!GV>7:7:7:1
```

**Root Cause:** Unclear - possibly terminal encoding, serial line buffering, or Python stdout buffering issue.

**Impact Assessment:** NONE - CSV and JSON files are completely clean and valid. Console corruption is purely cosmetic.

**Verification Method:** Always verify actual data by checking files, not console output:
```bash
tail ~/utData/raw/001e06122a5a/2025/12/29/MINTS_001e06122a5a_SCD30_2025_12_29.csv
# Output is clean with proper timestamps and values
```

**Workaround:** Ignore console output, rely on file verification.

**Not Investigated Further:** Since files are valid, console display corruption was not pursued as it has no impact on functionality.

---

### ❌ Initial MQTT Non-Publishing

**Problem:** Data was being collected and written to CSV/JSON files, but not published to MQTT topics.

**Symptom:** `mosquitto_sub -h YOUR_HA_IP -t "utsensing/#"` showed nothing.

**Root Causes (Multiple):**
1. TLS enabled for local broker (see above)
2. nanoReader not running (serial port held by old process)
3. No visible error messages (silent failure in try/except blocks)

**Troubleshooting Method That Worked:**
```bash
# Step 1: Verify MQTT broker is accessible
nc -zv YOUR_HA_IP 1883
# Output: Connection succeeded!

# Step 2: Verify Python can connect
python3 << 'EOF'
import paho.mqtt.client as mqttClient
client = mqttClient.Client()
client.connect("YOUR_HA_IP", 1883, 60)
client.loop_start()
import time
time.sleep(2)
if client.is_connected():
    print("Connected!")
    client.publish("test", "data")
EOF
# Output: Connected! (connection works)

# Step 3: Start nanoReader in foreground with full reboot
sudo reboot
# Wait 2 minutes
pkill -9 nanoReader.py  # Kill old processes
python3 nanoReader.py 0 > /tmp/nanoReader.log 2>&1 &
sleep 5
mosquitto_sub -h YOUR_HA_IP -t "utsensing/#" -v
# Output: DATA FLOWING!
```

**Key Insight:** MQTT was working all along, but:
- Old nanoReader processes were holding the serial port
- Garbled console output suggested the parser was failing
- Full system reboot cleared all stuck processes
- Fresh nanoReader connection succeeded immediately

---

### ❌ Serial Port Reconnection Issues

**Problem:** After unplugging Arduino USB and replugging, port moved from /dev/ttyUSB0 to /dev/ttyUSB1.

**Behavior:**
- First plug: /dev/ttyUSB0
- Unplug and replug: /dev/ttyUSB1
- Multiple unplug/replug cycles: /dev/ttyUSB2, /dev/ttyUSB3, etc.

**Side Effect:** Old nanoReader processes still held the old port, causing serial conflicts.

**Solution:** Full system reboot with Arduino disconnected:
1. Kill all nanoReader processes
2. Unplug Arduino USB
3. Reboot Odroid: `sudo reboot`
4. After reboot completes, plug Arduino back in
5. nanoReader auto-starts from cron and gets fresh port assignment

**Why This Works:**
- Reboot clears all zombie processes and hung file descriptors
- Arduino re-enumeration assigns clean port number
- nanoReader's auto-detection finds the correct port

---

## Critical Configuration Steps

### Step 1: Python Dependencies (In Exact Order)

```bash
# First, update pip
pip3 install --upgrade pip

# Install core dependencies (Python 3.6 compatible versions)
pip3 install pyserial==3.5
pip3 install pynmea2==1.19.0
pip3 install getmac==0.9.5
pip3 install netifaces==0.11.0
pip3 install PyYAML==6.0.1
pip3 install paho-mqtt==1.6.1
pip3 install requests==2.27.1

# DO NOT install numpy (optional, causes ARM compilation failures)
```

**Why This Order:** Some packages depend on others. Install core libraries first.

**Python 3.6 Check:**
```bash
python3 --version
# Should show Python 3.6.x
```

### Step 2: User Permissions Setup

```bash
# Ensure user is in required groups
sudo usermod -aG dialout YOUR_USER
sudo usermod -aG sudo YOUR_USER

# CRITICAL: New login required for group changes
# Logout and SSH back in
exit
ssh YOUR_USER@<odroid-ip>

# Verify groups
groups
# Should show: YOUR_USER dialout sudo
```

### Step 3: mintsDefinitions.py Configuration

**IMPORTANT:** This file needs to be customized for each deployment.

**Template for `/home/YOUR_USER/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py`:**

Lines 70-73 (Data Folders - MUST MATCH YOUR USERNAME):
```python
dataFolderReference       = "/home/YOUR_USER/utData/reference"      # ← CHANGE cerberus TO YOUR USERNAME
dataFolderMQTTReference   = "/home/YOUR_USER/utData/referenceMQTT"  # ← CHANGE cerberus TO YOUR USERNAME
dataFolder                = "/home/YOUR_USER/utData/raw"             # ← CHANGE cerberus TO YOUR USERNAME
dataFolderMQTT            = "/home/YOUR_USER/utData/rawMQTT"         # ← CHANGE cerberus TO YOUR USERNAME
```

Lines 95-98 (MQTT Configuration):
```python
mqttOn                   = True                    # Enable MQTT
mqttCredentialsFile      = 'mintsXU4/credentials.yml'
mqttBroker               = "YOUR_HA_IP"        # ← CHANGE TO YOUR HOME ASSISTANT IP
mqttPort                 = 1883
```

**How to Get Your Home Assistant IP:**
- On HA machine: `hostname -I`
- Or check your router's DHCP client list
- Or in HA web UI: Settings → System → About → IP Address

### Step 4: credentials.yml File

**Create:** `/home/YOUR_USER/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/credentials.yml`

```yaml
mqtt:
  username: "local_user"
  password: "local_pass"
```

**Important Notes:**
- File MUST exist (mintsLatest.py loads it at import time)
- Credentials don't matter if HA Mosquitto accepts anonymous (which it does by default)
- File is already in .gitignore - don't commit it
- Same credentials can be used for all Odroid units

### Step 5: Create Data Directory

```bash
mkdir -p /home/YOUR_USER/utData/raw
```

This must exist before nanoReader runs.

### Step 6: Cron Auto-Startup

```bash
crontab -e
```

Add these exact lines:
```cron
@reboot cd /home/YOUR_USER/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
*/10 * * * * cd /home/YOUR_USER/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
```

And ensure runAll.sh is executable:
```bash
chmod +x /home/YOUR_USER/Air-quality-sensors/firmware/xu4Mqqt/runAll.sh
```

---

## Dependencies and Python 3.6 Compatibility

### Confirmed Working Versions

```
pyserial==3.5              # Serial port communication
pynmea2==1.19.0            # GPS/NMEA parsing (optional)
getmac==0.9.5              # MAC address detection
netifaces==0.11.0          # Network interface info
PyYAML==6.0.1              # YAML parsing (credentials.yml)
paho-mqtt==1.6.1           # MQTT client
requests==2.27.1           # HTTP requests
Python 3.6.9               # Ubuntu 18.04 default
```

### Why NOT These Versions

- `numpy>=1.21.0` - Requires Cython, fails to compile on ARM
- `requests>=2.28.0` - Drops Python 3.6 support
- `PyYAML<6.0` - Missing features, breaks on edge cases
- `paho-mqtt>=1.7.0` - Not tested, stick with 1.6.1

### Testing Dependency Compatibility

```bash
# Test each package after install
python3 << 'EOF'
import serial
import paho.mqtt.client
import yaml
import requests
import getmac
import netifaces
print("All dependencies loaded successfully!")
EOF
```

---

## MQTT Configuration Details

### Broker Discovery

**Test MQTT broker connectivity:**
```bash
# 1. Verify port is open
nc -zv YOUR_HA_IP 1883
# Output: Connection succeeded! (or Connection refused)

# 2. Test anonymous connection
mosquitto_pub -h YOUR_HA_IP -t "test/odroid" -m "Hello"
# No error = anonymous allowed
```

### Troubleshooting MQTT Data Not Flowing

**Decision Tree:**

```
1. Is mosquitto_pub working? (test above)
   YES → Go to 2
   NO  → Check firewall on HA machine, check if Mosquitto is running

2. Is nanoReader.py running?
   ps aux | grep nanoReader
   YES → Go to 3
   NO  → Start it and wait 10 seconds

3. Are CSV files being created?
   ls -la ~/utData/raw/001e06122a5a/2025/12/29/
   YES → Go to 4
   NO  → Serial port issue, check Arduino connection

4. Are JSON files being updated?
   ls -la ~/utData/raw/001e06122a5a/*.json
   Check timestamps are recent (within 10 seconds)
   YES → MQTT should be publishing
   NO  → Parsing issue, reboot system

5. Subscribe and listen
   mosquitto_sub -h YOUR_HA_IP -t "utsensing/#" -v
   Should see data streaming
```

### Why MQTT Publishing Can Appear to Fail

**Scenario:** CSV and JSON files are being updated, but `mosquitto_sub` shows nothing.

**Likely Causes (In Order):**
1. ❌ TLS enabled for local broker (see mintsLatest.py lines 53-56)
2. ❌ Old nanoReader process still running, new one can't bind to port
3. ❌ MQTT broker on HA machine not running/accessible
4. ❌ Firewall blocking port 1883
5. ❌ Wrong broker IP in mintsDefinitions.py

**Diagnostic Sequence:**
```bash
# 1. Check mintsLatest.py TLS settings
grep -n "tls_set" firmware/xu4Mqqt/mintsXU4/mintsLatest.py
# Should see # (commented) at start of lines 53-56

# 2. Check for old processes
ps aux | grep nanoReader
# Should see only one process, not multiple

# 3. Check broker IP in config
grep mqttBroker firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
# Should match your HA IP

# 4. Full system reboot
sudo reboot
```

---

## Serial Port and USB Issues

### Expected Behavior

**First Time Connection:**
- Arduino plugged in
- `ls /dev/ttyUSB0` exists
- `dmesg | tail` shows: `FTDI USB Serial Device converter now attached to ttyUSB0`

**After Unplug/Replug:**
- Arduino unplugged for >10 seconds
- Arduino plugged back in
- `ls /dev/ttyUSB1` exists (port number increases)
- This is NORMAL - USB re-enumeration

### Fixing Serial Port Issues

**Problem:** Old nanoReader still has /dev/ttyUSB0 open, Arduino reconnected to /dev/ttyUSB1

**Solution:**
```bash
# 1. Kill all Python processes holding serial ports
pkill -9 nanoReader.py
pkill -9 python3

# 2. Unplug Arduino
# (wait 10 seconds)

# 3. Reboot entire system
sudo reboot

# 4. After reboot, plug Arduino back in
# (wait 30 seconds for Arduino to boot)

# 5. Verify port
ls /dev/ttyUSB0
# Should exist and be readable

# 6. Test raw serial
timeout 30 cat /dev/ttyUSB0
# Should see sensor initialization messages
```

### Why Full Reboot is Necessary

- Reboot clears all file descriptors held by dead processes
- Fresh bootloader initialization on Arduino
- Clean re-enumeration of USB device
- Cron auto-starts nanoReader with correct port

---

## Troubleshooting Decision Tree

```
System Not Responding?
├─ Red LED only (no blue flashing)
│  ├─ Reflash SD card with Balena Etcher
│  ├─ Use EXACT image: ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz
│  └─ Try different SD card (SanDisk preferred)
│
└─ Blue LED flashing, no network
   ├─ Check power supply (need 5V/2A minimum)
   ├─ Wait 60 seconds for boot
   └─ Check router DHCP client list for new device

Data Collected but Not Publishing?
├─ CSV files exist and are valid?
│  ├─ YES → Parsing IS working, issue is MQTT only
│  └─ NO  → Serial port issue
│
├─ Verify MQTT broker accessible
│  ├─ nc -zv YOUR_HA_IP 1883
│  └─ Should show "Connection succeeded"
│
└─ Check mintsLatest.py
   ├─ Lines 53-56 must be commented out (TLS disabled)
   ├─ Lines 95-98 must have correct broker IP
   └─ Full system reboot after any changes

Console Output Garbled?
├─ Check CSV files are clean
│  ├─ tail ~/utData/raw/001e06122a5a/2025/12/29/*.csv
│  └─ Should be properly formatted (cosmetic console issue only)
│
└─ Safe to ignore console output, rely on file verification

Arduino Not Detected?
├─ Check USB connection
│  ├─ dmesg | grep tty
│  └─ Should show "FTDI... attached to ttyUSB0"
│
├─ Check user permissions
│  ├─ ls -la /dev/ttyUSB0
│  ├─ usermod -aG dialout YOUR_USER
│  └─ Logout and login (or reboot)
│
└─ If port is USB1 instead of USB0 (after reconnect)
   ├─ This is normal re-enumeration
   ├─ nanoReader auto-detects correct port
   └─ Full reboot to reset port numbering
```

---

## Exact Configuration Files Needed

### File 1: requirements.txt

**Location:** `/home/user/Air-quality-sensors/requirements.txt`

**Content:**
```
# UTSensing Air Quality Monitor - Python Dependencies
# Install with: pip3 install -r requirements.txt
# NOTE: Python 3.6 compatibility required for Ubuntu 18.04

# Core dependencies
pyserial>=3.5           # Serial communication with Arduino
pynmea2>=1.18.0         # GPS NMEA sentence parsing
getmac>=0.9.0           # MAC address detection
netifaces>=0.11.0       # Network interface information
PyYAML>=6.0             # YAML configuration files

# MQTT communication
paho-mqtt>=1.6.0        # MQTT client for Home Assistant integration

# HTTP requests
requests>=2.27.0        # HTTP library for IP detection (Python 3.6 compatible)

# Data processing
# numpy optional - causes ARM compilation failures, skipping
```

### File 2: mintsDefinitions.py (Template)

**Location:** `/home/<username>/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py`

**CRITICAL LINES TO CUSTOMIZE:**
```python
# Lines 70-73: DATA PATHS
dataFolderReference       = "/home/<USERNAME>/utData/reference"        # ← REPLACE <USERNAME>
dataFolderMQTTReference   = "/home/<USERNAME>/utData/referenceMQTT"   # ← REPLACE <USERNAME>
dataFolder                = "/home/<USERNAME>/utData/raw"              # ← REPLACE <USERNAME>
dataFolderMQTT            = "/home/<USERNAME>/utData/rawMQTT"          # ← REPLACE <USERNAME>

# Lines 95-98: MQTT CONFIGURATION
mqttOn                   = True                            # Enable MQTT
mqttCredentialsFile      = 'mintsXU4/credentials.yml'
mqttBroker               = "192.168.X.X"                   # ← SET TO YOUR HA IP
mqttPort                 = 1883
```

### File 3: credentials.yml

**Location:** `/home/<username>/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/credentials.yml`

**Content:**
```yaml
mqtt:
  username: "local_user"
  password: "local_pass"
```

### File 4: mintsLatest.py (MUST HAVE FIXES)

**Location:** `/home/<username>/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsLatest.py`

**Line 22 (MUST BE):**
```python
credentials = yaml.safe_load(open(mqttCredentialsFile))  # ← safe_load NOT load
```

**Lines 53-56 (MUST BE COMMENTED):**
```python
#        mqtt_client.tls_set(ca_certs=tlsCert, certfile=None,
#                            keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
#                            tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
#        mqtt_client.tls_insecure_set(False)
```

---

## Common Pitfalls for Next Deployment

### ❌ Pitfall #1: Not Waiting for apt.systemd.daily

**Symptom:** "dpkg lock" errors immediately after first boot

**Cause:** Automatic updates running in background

**Solution:** Wait 3-5 minutes, then verify with:
```bash
ps aux | grep apt.systemd.daily
```

**Prevention:** Document this in deployment runbook

### ❌ Pitfall #2: Using Wrong Flashing Tool

**Tools to AVOID:**
- Rufus (destroys Odroid bootloader)
- Raspberry Pi Imager (not tested for Odroid)

**Tool to USE:**
- Balena Etcher (tested, verified, recommended by Hardkernel)

### ❌ Pitfall #3: Not Changing Default Root Password

**Security Issue:** System boots with default password `odroid`

**Solution:** Change immediately after first boot:
```bash
passwd
```

### ❌ Pitfall #4: Installing numpy from requirements.txt

**Symptom:** Compilation errors, "Cython needs to be installed"

**Solution:** Remove numpy from requirements.txt (it's optional)

### ❌ Pitfall #5: Using yaml.load() Instead of yaml.safe_load()

**Symptom:** `TypeError: load() missing 1 required positional argument: 'Loader'`

**Solution:** Always use `yaml.safe_load()` in mintsLatest.py line 22

### ❌ Pitfall #6: Leaving TLS Enabled for Local MQTT

**Symptom:** MQTT data not publishing, no error messages

**Solution:** Comment out lines 53-56 in mintsLatest.py

### ❌ Pitfall #7: Not Fixing mintsDefinitions.py Path from /home/pi

**Symptom:** Files not written, "Permission denied" errors

**Solution:** Change ALL data folder paths from `/home/pi/` to `/home/<username>/`

### ❌ Pitfall #8: Forgetting to Add User to dialout Group

**Symptom:** "Permission denied" when accessing /dev/ttyUSB0

**Solution:** Add to dialout group and logout/login:
```bash
usermod -aG dialout <username>
```

### ❌ Pitfall #9: Not Creating credentials.yml File

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'mintsXU4/credentials.yml'`

**Solution:** Create file even though contents don't matter if broker allows anonymous

### ❌ Pitfall #10: Testing MQTT Before nanoReader Running

**Symptom:** `mosquitto_sub` shows nothing, assume MQTT broken

**Solution:** Always verify nanoReader is running first:
```bash
ps aux | grep nanoReader
```

---

## Pre-Deployment Checklist for Next System

- [ ] Ubuntu 18.04.3 kernel 3.10.107 image downloaded and MD5 verified
- [ ] Balena Etcher installed and configured (telemetry disabled)
- [ ] SD card backed up (if reusing)
- [ ] Home Assistant IP address known
- [ ] WiFi SSID and password available
- [ ] Username chosen (e.g., `cerberus`)
- [ ] Arduino firmware loaded and tested (before physical setup)
- [ ] All 7 sensor breakouts checked for cold solder joints
- [ ] Arduino powered separately during testing to avoid overcurrent

## Post-Deployment Verification

After initial setup, verify:

1. **System is updating:** `ps aux | grep apt.systemd.daily` (should be empty after 5 min)
2. **SSH works:** `ssh <username>@<odroid-ip>` with password
3. **WiFi connected:** `ip addr show wlan0` shows valid IP
4. **Arduino detected:** `ls -la /dev/ttyUSB0`
5. **Serial data clean:** `timeout 10 cat /dev/ttyUSB0 | head` shows legible text
6. **Permissions set:** `groups` shows `dialout sudo`
7. **Dependencies installed:** `pip3 list | grep mqtt`
8. **Config files customized:** `grep mqttBroker firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py` shows your HA IP
9. **Data directory exists:** `mkdir -p ~/utData/raw` runs without errors
10. **Manual sensor test:** `python3 nanoReader.py` creates CSV files
11. **Cron configured:** `crontab -l` shows @reboot and */10 schedules
12. **System reboots:** `sudo reboot` then verify nanoReader auto-starts
13. **MQTT publishes:** `mosquitto_sub -h <HA-IP> -t "utsensing/#" -v` shows data
14. **Data flows:** Verify CSV and JSON files update every 10 seconds

---

## Version History

- **2025-12-29:** Initial comprehensive deployment lessons document
  - Documented all working configuration steps
  - Recorded all failures and solutions
  - Captured Python 3.6 compatibility gotchas
  - Created decision trees for troubleshooting
  - Provided exact configuration file templates
  - Listed common pitfalls to avoid
  - Included pre/post deployment checklists

---

## For Future Deployments

**Use this document to:**
1. Skip all the trial-and-error
2. Go directly to what's known to work
3. Avoid the 10 common pitfalls
4. Troubleshoot systematically
5. Configure identically for multiple units

**When something new goes wrong:**
1. Document it here
2. Record the fix
3. Update the "Common Pitfalls" section
4. Share with team

This is institutional knowledge. Every problem solved should be recorded here so nobody has to solve it twice.
