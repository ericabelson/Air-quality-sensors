# Odroid C1+ Setup Guide for Air Quality Sensors

**Complete guide based on real-world troubleshooting and proven solutions**

This guide documents the EXACT steps to set up an Odroid C1+ for the MINTS air quality sensor system, including all the pitfalls to avoid and solutions that actually work.

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Compatible OS Images](#compatible-os-images)
3. [Flashing the SD Card](#flashing-the-sd-card)
4. [First Boot and Initial Setup](#first-boot-and-initial-setup)
5. [System Configuration](#system-configuration)
6. [Sensor Setup](#sensor-setup)
7. [Home Assistant Integration](#home-assistant-integration)
8. [Troubleshooting](#troubleshooting)
9. [Future Alternative: ESP32](#future-alternative-esp32)

---

## Hardware Overview

### Odroid C1+ Specifications
- **Manufacturer:** Hardkernel
- **Release Year:** 2015
- **SoC:** Amlogic S805 (ARM Cortex-A5 quad-core)
- **RAM:** 1GB DDR3
- **Storage:** MicroSD card (32GB recommended)
- **Network:** Ethernet + WiFi dongle support
- **Power:** 5V/2A minimum (2.5A recommended)

### Sensor Array (Connected to Arduino Nano)
1. **SCD30** - CO2, Temperature, Humidity
2. **BME680** - Environmental (Pressure, Humidity, Temperature, VOC Gas Resistance)
3. **SGP30** - VOC and eCO2 readings
4. **MGSV2** - Multichannel Gas (NO2, Ethanol, VOC, CO)
5. **SEN0321** - Ozone (O3)
6. **PMSA003I** - Particulate Matter (PM1, PM2.5, PM10)
7. **MQ136** - Hydrogen Sulfide (H2S)

### System Architecture
```
Sensors (I2C) → Arduino Nano → USB Serial (9600 baud) → Odroid C1+ → WiFi → Home Assistant (MQTT)
```

---

## Compatible OS Images

### ✅ WHAT WORKS: Ubuntu 18.04.3 LTS with Kernel 3.10.107

**Official Hardkernel Release (Tested and Verified)**

- **Image:** `ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz`
- **Kernel:** 3.10.107-13 (vendor kernel optimized for S805)
- **Release Date:** 2019-09-23
- **Size:** 383MB compressed
- **Type:** Minimal/Server (no desktop environment)

**Official Download Locations:**
- **US East Coast:** https://east.us.odroid.in/ubuntu_18.04lts/C0_C1/
- **US West Coast:** https://odroid.in/ubuntu_18.04lts/C0_C1/
- **EU Germany:** https://de.eu.odroid.in/ubuntu_18.04lts/C0_C1/
- **Korea:** https://dn.odroid.com/S805/Ubuntu/

**Verify with MD5 hash:** Download `ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz.md5sum` and verify locally.

**Official Documentation:** https://wiki.odroid.com/odroid-c1/os_images/ubuntu/v3.1

---

### ❌ WHAT DOESN'T WORK (Avoid These!)

#### Armbian with Kernel 6.x (FAILS)
- **Tested:** Armbian 25.5.1 with kernel 6.12.28
- **Result:** Catastrophic I/O errors, filesystem corruption, won't boot
- **Why:** Modern mainline kernels (6.x) dropped support for Amlogic S805 hardware
- **Symptoms:**
  - Red LED only (no blue flashing)
  - "Input/output error" messages
  - Missing system commands (adduser, sed, grep, etc.)
  - Bootloader failure

#### Ubuntu 24.04 / Modern Distributions
- **Result:** Same kernel 6.x compatibility issues
- **Recommendation:** Stick with Ubuntu 18.04.3 LTS

#### Why Modern Kernels Fail
The Amlogic S805 SoC (2015 hardware) requires vendor-specific drivers and device tree configurations that were removed from mainline Linux kernel 6.x. The official vendor kernel (3.10.107) is the only reliable option.

---

## Flashing the SD Card

### ✅ RECOMMENDED TOOL: Balena Etcher

**Official Download:** https://etcher.balena.io/

**Why Etcher:**
- Official Hardkernel recommendation for Odroid boards
- Handles .xz compressed images automatically (no pre-extraction needed)
- Preserves ARM bootloader partitions correctly
- Built-in verification after flashing
- Cross-platform (Windows, Mac, Linux)
- Open source: https://github.com/balena-io/etcher

**Privacy Note:** Etcher collects anonymous telemetry by default. Disable it:
1. Open Etcher
2. Click gear icon (⚙️) → Settings
3. Uncheck "Anonymously report errors and usage information"

**Flashing Steps:**
1. Download `ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz`
2. Insert microSD card into computer
3. Open Balena Etcher
4. Click "Flash from file" → select the `.img.xz` file (no extraction needed!)
5. Click "Select target" → choose your SD card
6. Click "Flash!"
7. Wait for verification to complete (~10 minutes)
8. Eject SD card safely

---

### ❌ TOOLS THAT DON'T WORK (Avoid!)

#### Rufus - CORRUPTS ODROID BOOTLOADERS
**Official Hardkernel Warning:** "Rufus is not recommended for ODROID devices"

**Why Rufus Fails:**
- Designed for x86/x64 PC boot media, not ARM boards
- Overwrites the hidden bootloader partition (sectors 0-49151)
- Odroid C1+ stores U-Boot bootloader between MBR and first partition
- Rufus destroys this, causing red-LED-only boot failure

**Source:** https://wiki.odroid.com/troubleshooting/odroid_flashing_tools

#### Raspberry Pi Imager - UNVERIFIED
- Designed specifically for Raspberry Pi hardware
- Not tested/documented for Odroid compatibility
- May or may not preserve Odroid bootloader structure
- Not worth the risk when Etcher is proven

---

### SD Card Compatibility Notes

**Recommended Brands:**
- **SanDisk** - Most reliable with Odroid C1+
- Avoid Samsung EVO (known bootloader compatibility issues)

**Size:** 32GB recommended (8GB minimum)

---

## First Boot and Initial Setup

### Boot Indicators (LED Behavior)

**Normal Boot:**
- Red LED: Solid (power)
- Blue LED: Flashing (boot activity)
- Device appears on network within 60 seconds

**Boot Failure:**
- Red LED only: Bootloader failure (corrupted image or SD card issue)
- No LEDs: Power supply failure

### Network Discovery

**Expected Behavior:**
- Device may appear with unexpected hostname (e.g., "wibrain" instead of "odroid")
- Check your router's DHCP client list for new devices
- Default hostname: `odroid`
- MAC address prefix: Various (check router for recent connections)

### First SSH Connection

**From Windows PowerShell:**
```powershell
ssh root@<odroid-ip-address>
```

**Default Credentials:**
- **Username:** `root`
- **Password:** `odroid`

**First Login Behavior:**
- Ubuntu 18.04 minimal does NOT force password change on first boot
- You log in directly as root
- **IMPORTANT:** Change root password immediately for security

**Note:** If SSH key fingerprint warning appears, type `yes` to accept.

---

### Initial Configuration

#### 1. Change Root Password (CRITICAL)
```bash
passwd
```
Enter new password twice.

#### 2. Create Regular User (Recommended)
```bash
adduser yourusername
usermod -aG sudo yourusername
```

#### 3. Wait for Automatic Updates

**On first boot, Ubuntu runs automatic updates in background:**
```bash
# Check if running
ps aux | grep apt.systemd.daily
```

**If you see `apt.systemd.daily` processes:**
- **WAIT 3-5 minutes for it to finish**
- This updates the system automatically
- Don't interrupt it - let it complete

**Verify it's done:**
```bash
ps aux | grep apt.systemd.daily
```
Should show nothing (or just the grep command itself).

#### 4. Manual System Update (if needed)
```bash
apt update
apt upgrade -y
```

If you get a "lock" error, the automatic update is still running. Wait.

---

## System Configuration

### Install Essential Packages

```bash
# Network and WiFi tools
apt install -y network-manager wireless-tools

# Development tools
apt install -y git python3 python3-pip build-essential

# Serial port tools
apt install -y python3-serial screen minicom

# MQTT broker (optional - for local MQTT)
apt install -y mosquitto mosquitto-clients
```

### Configure WiFi

**Using NetworkManager:**
```bash
# Scan for networks
nmcli device wifi list

# Connect to WiFi
nmcli device wifi connect "YourWiFiSSID" password "YourWiFiPassword"

# Verify connection
ip addr show wlan0
```

**Verify WiFi is working:**
```bash
ping -c 4 8.8.8.8
```

**Once WiFi is stable, you can unplug Ethernet.**

### Set Static IP (Optional but Recommended)

**Edit netplan configuration:**
```bash
nano /etc/netplan/01-netcfg.yaml
```

**Example static WiFi config:**
```yaml
network:
  version: 2
  renderer: NetworkManager
  wifis:
    wlan0:
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
      access-points:
        "YourWiFiSSID":
          password: "YourWiFiPassword"
```

**Apply changes:**
```bash
netplan apply
```

---

## Sensor Setup

### Clone This Repository

```bash
cd /home/yourusername
git clone https://github.com/yourusername/Air-quality-sensors.git
cd Air-quality-sensors
```

### Install Python Dependencies

```bash
pip3 install -r firmware/xu4Mqqt/requirements.txt
```

**If requirements.txt doesn't exist, install manually:**
```bash
pip3 install pyserial paho-mqtt python-dateutil pytz
```

### Verify Arduino Connection

**Plug Arduino Nano into Odroid USB port.**

**Check USB devices:**
```bash
ls -la /dev/ttyUSB*
```

**Should see:** `/dev/ttyUSB0` (or similar)

**Test serial connection:**
```bash
screen /dev/ttyUSB0 9600
```

**You should see sensor data streaming in MINTS format:**
```
#mintsO>SCD30>400:25.5:45.2~
#mintsO>BME680>1013:22.3:50.1:45678~
```

**Exit screen:** Press `Ctrl+A`, then `K`, then `Y`

---

### Deploy Sensor Collection Scripts

**Copy sensor code to system location:**
```bash
cd /home/yourusername/Air-quality-sensors/firmware/xu4Mqqt

# Create data directory
mkdir -p /home/yourusername/utData/raw

# Test nanoReader script
python3 nanoReader.py
```

**You should see:**
- Serial port detected
- Sensor data being parsed
- CSV files created in `/home/yourusername/utData/raw/`

**Stop with:** `Ctrl+C`

---

### Configure Startup Scripts

**Edit crontab:**
```bash
crontab -e
```

**Add these lines:**
```cron
@reboot cd /home/yourusername/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
*/10 * * * * cd /home/yourusername/Air-quality-sensors/firmware/xu4Mqqt && ./runAll.sh
```

**Make runAll.sh executable:**
```bash
chmod +x /home/yourusername/Air-quality-sensors/firmware/xu4Mqqt/runAll.sh
```

---

## Home Assistant Integration

### Configure MQTT (Local Broker)

**Edit MQTT settings in `mintsDefinitions.py`:**
```bash
nano /home/yourusername/Air-quality-sensors/firmware/xu4Mqqt/mintsDefinitions.py
```

**Set MQTT broker to your Home Assistant IP:**
```python
mqttBroker = "192.168.1.50"  # Your HA IP
mqttPort = 1883
mqttOn = True
```

**Test MQTT connection:**
```bash
mosquitto_pub -h 192.168.1.50 -t "test/topic" -m "Hello from Odroid"
```

### Add Sensors to Home Assistant

**Copy MQTT sensor configuration:**
```bash
# On your Home Assistant machine
cd /config/packages/
# Copy utsensing_sensors.yaml from this repo
```

**Or manually add to `configuration.yaml`:**
```yaml
mqtt:
  sensor:
    - name: "SCD30 CO2"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "ppm"
      device_class: "carbon_dioxide"
```

**Restart Home Assistant:**
```bash
# In HA web UI
Developer Tools → Restart
```

### Verify Data Flow

**Check MQTT messages:**
```bash
mosquitto_sub -h 192.168.1.50 -t "utsensing/#" -v
```

**You should see sensor data every second.**

**Check Home Assistant:**
1. Go to Developer Tools → States
2. Search for "sensor.scd30"
3. Should show live CO2 readings

---

## Troubleshooting

### Red LED Only, Won't Boot

**Causes:**
1. Corrupted SD card image (reflash with Etcher)
2. Wrong flashing tool used (don't use Rufus!)
3. Incompatible OS image (use Ubuntu 18.04.3 kernel 3.10)
4. Bad SD card (try different brand, preferably SanDisk)
5. Insufficient power supply (need 5V/2A minimum)

**Solution:**
- Reflash using Balena Etcher
- Use the exact image: `ubuntu-18.04.3-3.10-minimal-odroid-c1-20190923.img.xz`
- Try different SD card
- Verify power supply voltage

---

### I/O Errors During Boot

**Symptom:**
```
/usr/lib/armbian/armbian-firstlogin: line 208: /usr/bin/stty: Input/output error
adduser: command not found
```

**Cause:** Modern kernel (6.x) incompatibility with S805 hardware

**Solution:** Use Ubuntu 18.04.3 with kernel 3.10.107 (not Armbian!)

---

### Can't Connect to WiFi

**Check WiFi adapter is detected:**
```bash
iwconfig
```

Should show `wlan0` or similar.

**If no WiFi adapter:**
```bash
# Install firmware
apt install -y linux-firmware

# Reboot
reboot
```

---

### Arduino Not Detected

**Check USB connection:**
```bash
dmesg | grep tty
```

Should show: `FTDI USB Serial Device converter now attached to ttyUSB0`

**Check permissions:**
```bash
ls -la /dev/ttyUSB0
```

**Add user to dialout group:**
```bash
usermod -aG dialout yourusername
```

**Reboot required after group change.**

---

### Sensors Not Publishing to MQTT

**Test MQTT broker connectivity:**
```bash
mosquitto_pub -h <HA-IP> -t "test" -m "hello"
```

**Check MQTT broker is running on Home Assistant:**
```bash
# On HA machine
systemctl status mosquitto
```

**Check firewall on Home Assistant:**
```bash
# Allow MQTT port
sudo ufw allow 1883
```

**Verify mintsDefinitions.py settings:**
```bash
nano firmware/xu4Mqqt/mintsDefinitions.py
```

Ensure `mqttOn = True` and correct IP/port.

---

## Future Alternative: ESP32

**For future deployments, consider replacing Arduino Nano + Odroid with a single ESP32 board:**

### ESP32 Advantages
- **Built-in WiFi** - No separate computer needed
- **ESPHome compatible** - Native Home Assistant integration
- **Lower cost** - ~$10 for ESP32 vs $35+ for Odroid
- **Less complexity** - One device instead of two
- **No OS to maintain** - Firmware-based, not Linux

### Migration Path
1. Purchase ESP32 DevKit (ESP32-WROOM-32 recommended)
2. Rewire sensors from Arduino to ESP32 (same I2C connections)
3. Use ESPHome to configure sensors (YAML-based)
4. Flash ESP32 with ESPHome firmware
5. Native Home Assistant discovery (no MQTT needed)

**ESPHome supports all 7 sensors in this project natively.**

**Documentation:** https://esphome.io/

---

## Network Configuration Notes

### Main Network vs Guest Network

**For Odroid + Home Assistant setup:**
- **Put Odroid on MAIN network** (same as Home Assistant)
- **Don't use guest network** - guest networks isolate devices and prevent communication

**Why:**
- MQTT requires Odroid to communicate with Home Assistant
- Guest networks block device-to-device communication
- For trusted local sensors, main network is appropriate

**For enhanced security later:**
- Consider setting up a dedicated IoT VLAN
- Use firewall rules to restrict traffic
- Most consumer routers (like Deco M9 Plus) don't support advanced VLANs

---

## Security Best Practices

### Disable UT Dallas Data Sync (If Migrating from Old MINTS Setup)

**If you're upgrading from an old MINTS system that synced to UT Dallas:**

**Check crontab:**
```bash
crontab -l
```

**Look for this line (DELETE IT):**
```
*/1 * * * * rsync -avzrtu -e "ssh -p 2222" /home/utsensing/utData/raw/ mints@mintsdata.utdallas.edu:/home/mints/raw/
```

**Remove it:**
```bash
crontab -e
# Delete the rsync line
```

**Verify MQTT settings in mintsDefinitions.py:**
```python
# Should be localhost or your HA IP, NOT mqtt.circ.utdallas.edu
mqttBroker = "localhost"  # or "192.168.1.50"
```

### General Security
- Change default root password immediately
- Create non-root user for daily use
- Disable root SSH login (optional)
- Keep system updated: `apt update && apt upgrade`
- Use strong WiFi password (WPA3 if supported)

---

## Official Resources

### Hardkernel (Odroid Manufacturer)
- **Official Site:** https://www.hardkernel.com/
- **Wiki:** https://wiki.odroid.com/odroid-c1/odroid-c1
- **Forum:** https://forum.odroid.com/

### Ubuntu Images
- **Download Page:** https://wiki.odroid.com/odroid-c1/os_images/ubuntu/v3.1
- **Official Mirrors:** Listed in "Compatible OS Images" section above

### Tools
- **Balena Etcher:** https://etcher.balena.io/
- **Etcher GitHub:** https://github.com/balena-io/etcher

### This Project
- **Repository:** https://github.com/ericabelson/Air-quality-sensors
- **MINTS Original:** https://github.com/mi3nts (UT Dallas MINTS project)

---

## Version History

- **2025-12-29:** Initial comprehensive guide based on real-world deployment
- Documented all tested configurations, failures, and solutions
- Added troubleshooting for common issues
- Included ESP32 migration path for future deployments

---

## Credits

Based on extensive troubleshooting and research:
- Hardkernel official documentation
- Odroid community forum solutions
- Real-world deployment experience
- Ubuntu ARM platform documentation

**This guide represents actual tested solutions, not theoretical configurations.**
