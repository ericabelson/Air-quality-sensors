# Claude Code Handoff - Odroid C1+ Air Quality Sensor Setup

**Date:** 2025-12-29
**Project:** Air-quality-sensors (MINTS-based air quality monitoring)
**Repository:** https://github.com/ericabelson/Air-quality-sensors
**Branch:** `claude/sensor-communication-setup-G2628`

---

## CURRENT STATUS SUMMARY

You are picking up an Odroid C1+ setup that is **90% complete**. The system is booted, SSH is working, and we're waiting for automatic updates to finish before proceeding with sensor deployment.

---

## HARDWARE CONFIGURATION

### Odroid C1+ Setup
- **Device:** Hardkernel Odroid C1+ (2015, Amlogic S805 SoC)
- **OS:** Ubuntu 18.04.3 LTS minimal (kernel 3.10.107-13)
- **Image File:** `ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz`
- **Flashed With:** Balena Etcher (v1.19.x)
- **SD Card:** 32GB (brand unknown, working)
- **Network:** Currently connected via Ethernet
- **IP Address:** `192.168.68.117` (DHCP-assigned, may change)
- **Hostname:** `odroid`
- **Power:** 5V/2A adapter

### Arduino Nano + Sensors
- **Microcontroller:** Arduino Nano
- **Connection:** USB serial to Odroid (will be `/dev/ttyUSB0`)
- **Baud Rate:** 9600
- **Data Format:** MINTS protocol with `!`, `>`, `~` delimiters

**Connected Sensors (all via I2C to Arduino):**
1. SCD30 - CO2, Temperature, Humidity
2. BME680 - Environmental (Pressure, Humidity, Temperature, VOC)
3. SGP30 - VOC and eCO2
4. MGSV2 - Multichannel Gas (NO2, Ethanol, VOC, CO)
5. SEN0321 - Ozone (O3)
6. PMSA003I - Particulate Matter (PM1, PM2.5, PM10)
7. MQ136 - Hydrogen Sulfide (H2S)

### Home Assistant Setup
- **Platform:** Raspberry Pi 4
- **IP Address:** Unknown (user needs to provide)
- **MQTT Broker:** Running on HA Pi (port 1883)
- **Network:** Main network (same as Odroid will be)
- **WiFi Router:** Deco M9 Plus mesh system

---

## CURRENT SYSTEM STATE

### User Accounts
- **Currently Logged In As:** `root`
- **Created User:** Yes (username unknown - user created one but didn't specify name)
- **Root Password:** Changed from default `odroid` to user's secure password
- **User Password:** Set during creation

### System Updates
- **Status:** `apt.systemd.daily` is running automatic background updates
- **Started:** ~20 minutes ago
- **Expected Completion:** Should be done by now or finishing soon
- **What's Running:**
  ```
  PID 597: /bin/sh /usr/lib/apt/apt.systemd.daily update
  PID 605: /bin/sh /usr/lib/apt/apt.systemd.daily lock_is_held update
  ```

**To check if done:**
```bash
ps aux | grep apt.systemd.daily
```

### What's Installed (Base System)
- Python 3.6.x (Ubuntu 18.04 default)
- Basic system utilities
- SSH server (working)
- **NOT YET INSTALLED:**
  - Network Manager / WiFi tools
  - Git
  - Python pip
  - Python dependencies (pyserial, paho-mqtt, etc.)
  - MQTT broker/client
  - Sensor collection scripts

### Network Configuration
- **Current:** Ethernet only (cable plugged in)
- **WiFi:** Not configured yet
- **WiFi Credentials:** User has them but hasn't provided (will need to ask)
- **Target:** WiFi connection so Ethernet can be unplugged

---

## DATA MIGRATION COMPLETED

**Historical sensor data has been archived:**
- **Backed up:** 262MB of data from 2016, 2021, 2022
- **Archive File:** `mints_historical_data_2016-2022.zip` (61MB compressed)
- **Location:** User's Windows PC Downloads folder
- **Old System:** Ubuntu 16.04 with UT Dallas sync (completely wiped)

**UT Dallas Data Sync:**
- **Status:** REMOVED (was syncing every minute to `mintsdata.utdallas.edu`)
- **User Requirement:** Absolutely NO data to UT Dallas - all local only
- **Verified:** Old cron jobs deleted, old system wiped

---

## REPOSITORY CONTEXT

### Code Location
- **Repository:** `/home/user/Air-quality-sensors` (on development machine, not Odroid)
- **Branch:** `claude/sensor-communication-setup-G2628`
- **Key Files:**
  - `firmware/airNano/` - Arduino firmware (PlatformIO)
  - `firmware/xu4Mqqt/` - Python sensor readers for Odroid
    - `nanoReader.py` - Reads Arduino serial data
    - `mintsSensorReader.py` - Parses MINTS protocol
    - `ipReader.py` - Records IP addresses
    - `GPSReader.py` - GPS (if available)
    - `mintsDefinitions.py` - Configuration (MAC address, MQTT settings)
    - `runAll.sh` - Startup script
  - `homeassistant/packages/utsensing_sensors.yaml` - HA MQTT sensor configs
  - `homeassistant/dashboards/` - Pre-built dashboards
  - `docs/ODROID_C1_SETUP.md` - **NEW: Complete setup guide** (just created)

### Configuration Needed
- `mintsDefinitions.py` settings:
  - `mqttBroker` - Set to HA Pi IP (currently localhost)
  - `mqttPort` - 1883
  - `mqttOn` - Set to True
  - `dataFolder` - `/home/<username>/utData/raw/`
  - MAC address detection - Should auto-detect from wlan0 or eth0

---

## WHAT'S BEEN DONE (Chronologically)

1. ✅ Explored old Odroid system (Ubuntu 16.04)
2. ✅ Found active UT Dallas data sync (rsync every minute)
3. ✅ Archived 262MB historical sensor data
4. ✅ Downloaded archive to Windows PC (verified 61MB zip)
5. ✅ Researched compatible OS images (tried Armbian 6.12.28 - FAILED with I/O errors)
6. ✅ Identified working image: Ubuntu 18.04.3 kernel 3.10.107
7. ✅ Downloaded from official Hardkernel mirror
8. ✅ Installed Balena Etcher (after Rufus failed - Rufus corrupts ARM bootloaders!)
9. ✅ Flashed Ubuntu 18.04.3 minimal to SD card
10. ✅ Booted Odroid successfully (appeared as "wibrain" on network initially)
11. ✅ SSH connected at 192.168.68.117
12. ✅ Changed root password
13. ✅ Created regular user account
14. ✅ Started automatic system update (apt.systemd.daily running)
15. ✅ **Created comprehensive documentation:** `docs/ODROID_C1_SETUP.md`
16. ⏸️ **WAITING:** For apt.systemd.daily to finish (should be done or close)

---

## NEXT STEPS (In Order)

### Step 1: Verify System Update Complete

**Check if apt.systemd.daily is still running:**
```bash
ps aux | grep apt.systemd.daily
```

**If still running:** Wait 2-3 more minutes.

**If done (no processes except grep itself):** Proceed to Step 2.

**Verify system is updated:**
```bash
apt list --upgradable
```

Should show "All packages are up to date" or minimal updates remaining.

---

### Step 2: Install Essential Packages

**Run as root:**
```bash
apt update
apt install -y network-manager wireless-tools git python3 python3-pip build-essential python3-serial screen mosquitto mosquitto-clients
```

**This installs:**
- Network Manager (WiFi configuration)
- Git (to clone repository)
- Python 3 + pip (sensor scripts)
- Serial tools (Arduino communication)
- MQTT broker + client (for HA integration)

---

### Step 3: Configure WiFi

**Ask user for WiFi credentials:**
- SSID (network name)
- Password

**Connect to WiFi:**
```bash
nmcli device wifi list
nmcli device wifi connect "SSID" password "PASSWORD"
```

**Verify WiFi connection:**
```bash
ip addr show wlan0
ping -c 4 8.8.8.8
```

**Get new WiFi IP address:**
```bash
ip addr show wlan0 | grep "inet "
```

**Note the new IP for future SSH connections.**

**User can then unplug Ethernet cable.**

---

### Step 4: Switch to Regular User

**Find username created earlier:**
```bash
cat /etc/passwd | grep "/home"
```

Should show the user account created during setup.

**Switch to that user:**
```bash
su - <username>
```

**Or SSH in as that user from now on:**
```bash
ssh <username>@<wifi-ip>
```

**All subsequent operations should be done as regular user, not root.**

---

### Step 5: Clone Repository to Odroid

**As regular user:**
```bash
cd ~
git clone https://github.com/ericabelson/Air-quality-sensors.git
cd Air-quality-sensors
git checkout claude/sensor-communication-setup-G2628
```

---

### Step 6: Install Python Dependencies

**Navigate to sensor code:**
```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt
```

**Install required Python packages:**
```bash
pip3 install pyserial paho-mqtt python-dateutil pytz
```

**Or if requirements.txt exists:**
```bash
pip3 install -r requirements.txt
```

---

### Step 7: Plug in Arduino and Verify Connection

**Physical connection:**
- Plug Arduino Nano USB cable into Odroid USB port

**Check device detection:**
```bash
dmesg | tail -20
```

Should show: `FTDI USB Serial Device converter now attached to ttyUSB0`

**Verify serial port exists:**
```bash
ls -la /dev/ttyUSB0
```

**Test serial data (raw stream):**
```bash
screen /dev/ttyUSB0 9600
```

**Expected output:**
```
#mintsO>SCD30>412.5:24.3:48.2~
#mintsO>BME680>1013.2:23.1:51.3:48291~
#mintsO>PMSA003I>2:5:8~
```

**Exit screen:** Press `Ctrl+A`, then `K`, then `Y`

---

### Step 8: Configure Sensor Collection Scripts

**Edit mintsDefinitions.py:**
```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt
nano mintsDefinitions.py
```

**Update these settings:**
```python
# MQTT Configuration
mqttBroker = "192.168.1.XXX"  # User's Home Assistant Pi IP
mqttPort = 1883
mqttOn = True  # Enable MQTT publishing

# Data folder
dataFolder = "/home/<username>/utData/raw/"
```

**Save and exit:** `Ctrl+O`, `Enter`, `Ctrl+X`

**Create data directory:**
```bash
mkdir -p ~/utData/raw
```

---

### Step 9: Test Sensor Data Collection

**Run nanoReader manually to test:**
```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt
python3 nanoReader.py
```

**Expected behavior:**
- Detects `/dev/ttyUSB0`
- Prints sensor data to console
- Creates CSV files in `~/utData/raw/<MAC_ADDRESS>/<SENSOR>/YYYY/MM/DD/`
- Creates latest.json files for each sensor

**Let it run for 30 seconds to verify all sensors.**

**Stop with:** `Ctrl+C`

**Verify data files created:**
```bash
ls -la ~/utData/raw/
```

Should see MAC address folder with sensor subdirectories.

---

### Step 10: Configure Automatic Startup

**Make runAll.sh executable:**
```bash
chmod +x ~/Air-quality-sensors/firmware/xu4Mqqt/runAll.sh
```

**Edit crontab (as regular user):**
```bash
crontab -e
```

**Add these lines:**
```cron
@reboot cd /home/<username>/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
*/10 * * * * cd /home/<username>/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
```

**Save and exit.**

**Test runAll.sh:**
```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt
./runAll.sh
```

Should start nanoReader, ipReader, and GPSReader (if GPS present).

**Check processes:**
```bash
ps aux | grep python
```

Should see `python3 nanoReader.py` running.

---

### Step 11: Configure MQTT for Home Assistant

**Ask user for Home Assistant IP address.**

**Test MQTT connection to HA:**
```bash
mosquitto_pub -h <HA_IP> -t "test/odroid" -m "Hello from Odroid"
```

**Subscribe to sensor topics from HA to verify data flow:**
```bash
mosquitto_sub -h <HA_IP> -t "utsensing/#" -v
```

Should see sensor data every 1 second:
```
utsensing/SCD30 {"co2": 412.5, "temperature": 24.3, "humidity": 48.2}
utsensing/BME680 {"pressure": 1013.2, "temperature": 23.1, ...}
```

---

### Step 12: Add Sensors to Home Assistant

**On Home Assistant machine (user will need to do this):**

1. Copy `homeassistant/packages/utsensing_sensors.yaml` to HA config
2. Or manually add sensors to `configuration.yaml`
3. Restart Home Assistant
4. Verify sensors appear in Developer Tools → States

**All 7 sensors should show live data:**
- sensor.scd30_co2
- sensor.scd30_temperature
- sensor.scd30_humidity
- sensor.bme680_pressure
- sensor.bme680_temperature
- sensor.pmsa003i_pm25
- etc.

---

### Step 13: Set Up Dashboards

**User can use pre-built dashboards:**
- `homeassistant/dashboards/air_quality.yaml`
- Contains cards for all 7 sensors
- Formatted with units, icons, history graphs

**Or create custom dashboard in HA UI.**

---

### Step 14: Final Verification and Testing

**Reboot Odroid to test automatic startup:**
```bash
sudo reboot
```

**After reboot (2 minutes), SSH back in:**
```bash
ssh <username>@<wifi_ip>
```

**Verify services started automatically:**
```bash
ps aux | grep python
```

Should see nanoReader running.

**Check MQTT data flowing:**
```bash
mosquitto_sub -h <HA_IP> -t "utsensing/#" -v
```

**Verify Home Assistant shows live sensor data.**

---

## POTENTIAL ISSUES TO WATCH FOR

### Issue 1: Arduino Not Detected After Reboot
**Symptom:** No `/dev/ttyUSB0` after reboot

**Solution:**
```bash
# Check USB devices
lsusb
# Should see FTDI device

# Check dmesg
dmesg | grep tty

# Add user to dialout group if needed
sudo usermod -aG dialout <username>
# Logout and login again
```

---

### Issue 2: WiFi Connection Drops
**Symptom:** WiFi disconnects randomly

**Solution:**
```bash
# Disable power management for WiFi
sudo iwconfig wlan0 power off

# Make permanent (add to /etc/rc.local)
```

---

### Issue 3: MQTT Connection Refused
**Symptom:** `Connection refused` when testing MQTT

**Solutions:**
- Verify MQTT broker is running on HA: `systemctl status mosquitto`
- Check firewall on HA allows port 1883: `sudo ufw allow 1883`
- Verify IP address is correct
- Test with mosquitto_pub from another device

---

### Issue 4: Sensors Show Stale Data
**Symptom:** Sensor values don't update in HA

**Solutions:**
- Check nanoReader is running: `ps aux | grep nanoReader`
- Check Arduino USB connection
- View serial data: `screen /dev/ttyUSB0 9600`
- Check MQTT messages: `mosquitto_sub -h <HA_IP> -t "utsensing/#"`
- Restart runAll.sh: `./runAll.sh`

---

## USER CONTEXT AND PREFERENCES

### User's Technical Level
- Comfortable with command line
- Windows 11 user (using PowerShell for SSH)
- Security-conscious (questioned legitimacy of downloads, concerned about telemetry)
- Wants thorough research and documented sources
- Dislikes installing unnecessary software
- **Important:** Gets frustrated with unresearched guesses - wants verified solutions

### User's Requirements
- **NO data to UT Dallas** (absolutely critical)
- All sensor data local only
- Report to Home Assistant on local network
- Use main network (not guest network) for device communication
- Prefers simpler solutions over complex ones
- Values security and privacy

### Communication Style
- Be direct and specific
- Provide researched answers with sources
- Don't guess or speculate
- Acknowledge when you don't know something
- Give clear step-by-step instructions
- Explain *why* things work, not just *how*

---

## FILES AND DOCUMENTATION

### Just Created
- **docs/ODROID_C1_SETUP.md** - Comprehensive setup guide with all lessons learned

### Existing Documentation
- `docs/RASPBERRY_PI_SETUP.md` - Similar setup for Pi (reference for procedures)
- `docs/HOME_ASSISTANT_SETUP.md` - HA integration details
- `docs/SECURITY.md` - Security hardening (includes removal of UT Dallas sync)
- `docs/TECHNICAL_REFERENCE.md` - Sensor datasheets and specifications

### Configuration Files
- `firmware/xu4Mqqt/mintsDefinitions.py` - Main config (needs editing)
- `firmware/xu4Mqqt/credentials.yml.example` - MQTT credentials template
- `homeassistant/packages/utsensing_sensors.yaml` - HA sensor definitions

---

## GIT WORKFLOW

### Current Branch
- **Branch:** `claude/sensor-communication-setup-G2628`
- **Must push to this branch** when complete
- **Will create PR** to merge to main after testing

### Commit Strategy
- Commit after each major milestone
- Clear commit messages
- Don't commit until sensors are working and verified
- Final commit should include updated documentation

---

## SUCCESS CRITERIA

### The setup is complete when:
1. ✅ Odroid boots automatically with WiFi
2. ✅ Arduino sensors are read every second
3. ✅ Data stored locally in CSV files
4. ✅ Data published to local MQTT broker
5. ✅ Home Assistant shows all 7 sensors with live data
6. ✅ Data updates every 1-2 seconds in HA
7. ✅ System survives reboot (auto-starts)
8. ✅ No data going to UT Dallas (verified)
9. ✅ User can view sensors on HA dashboard
10. ✅ Documentation updated and committed

---

## IMMEDIATE NEXT ACTION

**When you start:**

1. **SSH into Odroid:**
   ```
   ssh root@192.168.68.117
   ```
   (User may need to reconnect if connection dropped)

2. **Check if apt.systemd.daily is done:**
   ```bash
   ps aux | grep apt.systemd.daily
   ```

3. **If done:** Proceed with Step 2 (Install Essential Packages)

4. **If still running:** Wait 2-3 minutes, then proceed

5. **Follow the "NEXT STEPS" section above in order**

---

## QUESTIONS TO ASK USER

You will need to ask the user for:

1. **WiFi credentials:**
   - SSID (network name)
   - Password

2. **Home Assistant IP address:**
   - Example: 192.168.1.50

3. **Username created during setup:**
   - They created a user but didn't specify the name
   - Can find it with: `cat /etc/passwd | grep "/home"`

4. **Preferences:**
   - Do they want static IP for Odroid?
   - Do they want to set up dashboards now or later?

---

## ADDITIONAL NOTES

### ESP32 Future Migration
- User is aware ESP32 would simplify this setup
- Documented in ODROID_C1_SETUP.md
- Not pursuing now, but keep in mind for future recommendations

### Network Details
- Router: Deco M9 Plus mesh system
- Main network (not guest) for IoT devices
- DHCP assigns IPs automatically
- May want static IP for Odroid for reliability

### Time Investment
- User has spent significant time troubleshooting (multiple failed OS attempts)
- Be efficient and accurate to respect their time
- Don't send them on "wild goose chases"
- Research thoroughly before suggesting solutions

---

## FINAL CHECKLIST BEFORE COMPLETION

Before marking this task complete:

- [ ] WiFi configured and stable
- [ ] Arduino detected at `/dev/ttyUSB0`
- [ ] All 7 sensors reporting data
- [ ] CSV files being created locally
- [ ] MQTT publishing to Home Assistant
- [ ] All sensors visible in HA with live data
- [ ] Auto-start working (tested with reboot)
- [ ] No UT Dallas connections (verified)
- [ ] Documentation updated
- [ ] Changes committed to branch
- [ ] User confirms everything working

---

**Good luck! You're starting from a solid foundation. The hard part (OS installation and troubleshooting) is done. Now it's just configuration and deployment.**
