# Complete Raspberry Pi 4 Setup Guide

This guide takes you from an unboxed Raspberry Pi 4 and sensor kit to a fully functional air quality monitoring system.

**Time Required:** 2-3 hours
**Skill Level:** Beginner (no prior experience needed)
**What You'll Have:** A working air quality monitor with a web dashboard

**IMPORTANT:** Before starting, review the [Technical Reference Appendix](TECHNICAL_REFERENCE.md) for:
- Verified sensor specifications and datasheets
- Official software download links
- Detailed wiring diagrams
- Calibration procedures

---

## Table of Contents

1. [What You Need](#what-you-need)
2. [Part 1: Prepare the Raspberry Pi](#part-1-prepare-the-raspberry-pi)
3. [Part 2: Connect the Hardware](#part-2-connect-the-hardware)
4. [Part 3: Install the Software](#part-3-install-the-software)
5. [Part 4: Configure the System](#part-4-configure-the-system)
6. [Part 5: Test Everything](#part-5-test-everything)
7. [Part 6: Set Up Auto-Start](#part-6-set-up-auto-start)
8. [Part 7: Install Home Assistant Dashboard](#part-7-install-home-assistant-dashboard)
9. [Troubleshooting](#troubleshooting)

---

## What You Need

### Hardware Checklist

Check off each item as you verify you have it:

- [ ] Raspberry Pi 4 (2GB, 4GB, or 8GB RAM)
- [ ] MicroSD card (32GB or larger, Class 10)
- [ ] USB-C power supply (5V, 3A minimum)
- [ ] Arduino Nano (with USB cable)
- [ ] Micro USB cable (for Arduino to Pi connection)
- [ ] Sensor kit containing:
  - [ ] SCD30 (CO2 sensor)
  - [ ] BME680 (Environmental sensor)
  - [ ] SGP30 (VOC sensor)
  - [ ] PMSA003I (Particulate matter sensor)
  - [ ] SEN0321 (Ozone sensor)
  - [ ] MGSV2 (Multi-gas sensor)
  - [ ] MQ136 (H2S sensor)
- [ ] Grove I2C Hub cables (at least 3)
- [ ] Computer with SD card reader (for initial setup)
- [ ] Ethernet cable OR WiFi credentials

### Software You'll Download

- Raspberry Pi Imager (free)
- This repository (free)

---

## Part 1: Prepare the Raspberry Pi

### Step 1.1: Download Raspberry Pi Imager

On your computer (not the Pi), go to:

```
https://www.raspberrypi.com/software/
```

Download and install the Raspberry Pi Imager for your operating system (Windows, Mac, or Linux).

### Step 1.2: Flash the SD Card

1. Insert your MicroSD card into your computer
2. Open Raspberry Pi Imager
3. Click **"Choose OS"**
4. Select **"Raspberry Pi OS (64-bit)"** (the recommended version)
5. Click **"Choose Storage"**
6. Select your MicroSD card (be careful to select the right drive!)
7. Click the **gear icon** (settings) in the bottom right
8. Configure these settings:

```
Set hostname: utsensing
Enable SSH: Yes (Use password authentication)
Set username: pi
Set password: [choose a secure password - write it down!]
Configure wireless LAN: [enter your WiFi name and password]
Set locale settings: [your timezone]
```

9. Click **"Save"**
10. Click **"Write"**
11. Wait for the process to complete (5-10 minutes)
12. Remove the SD card when done

### Step 1.3: First Boot

1. Insert the SD card into the Raspberry Pi
2. Connect an Ethernet cable (recommended) OR rely on WiFi
3. Plug in the USB-C power supply
4. Wait 2-3 minutes for the Pi to boot

### Step 1.4: Find Your Pi's IP Address

**Method A: Using your router**
- Log into your router's admin page
- Look for connected devices
- Find "utsensing" in the list
- Note the IP address (e.g., 192.168.1.100)

**Method B: Using a monitor**
- Connect a monitor and keyboard to the Pi
- Log in with username `pi` and your password
- Run: `hostname -I`
- Note the IP address

### Step 1.5: Connect via SSH

On your computer, open a terminal (or PowerShell on Windows):

```bash
ssh pi@[YOUR_PI_IP_ADDRESS]
```

For example:
```bash
ssh pi@192.168.1.100
```

Type `yes` when asked about the fingerprint, then enter your password.

**You should now see:**
```
pi@utsensing:~ $
```

---

## Part 2: Connect the Hardware

### Step 2.1: Understand the Connections

All sensors connect to the Arduino Nano via I2C (a communication protocol). The Nano then connects to the Raspberry Pi via USB.

```
                    ┌──────────────────┐
                    │  Raspberry Pi 4  │
                    │                  │
                    │   USB Port       │
                    └────────┬─────────┘
                             │ USB Cable
                    ┌────────┴─────────┐
                    │   Arduino Nano   │
                    │                  │
                    │  A4(SDA) A5(SCL) │
                    └────────┬─────────┘
                             │ I2C
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
         │Grove Hub│    │Grove Hub│    │Grove Hub│
         └────┬────┘    └────┬────┘    └────┬────┘
              │              │              │
         ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
         │ SCD30   │    │ BME680  │    │ SGP30   │
         │ PMSA003I│    │ SEN0321 │    │ MGSV2   │
         └─────────┘    └─────────┘    └─────────┘
```

### Step 2.2: Connect the I2C Sensors

**Important:** Do this with the power OFF!

1. **Connect Grove Hub to Arduino Nano:**
   - Connect the first Grove I2C Hub to the Nano's I2C pins
   - SDA wire to pin A4
   - SCL wire to pin A5
   - VCC to 5V
   - GND to GND

2. **Daisy-chain the Grove Hubs:**
   - Connect second hub to first hub
   - Connect third hub to second hub

3. **Connect each sensor to a Grove Hub port:**
   - SCD30 → Hub 1, Port 1
   - BME680 → Hub 1, Port 2
   - SGP30 → Hub 2, Port 1
   - PMSA003I → Hub 2, Port 2
   - SEN0321 → Hub 3, Port 1
   - MGSV2 → Hub 3, Port 2

4. **Connect MQ136 (Analog sensor):**
   - Signal wire → Arduino Nano A0
   - VCC → 5V
   - GND → GND

### Step 2.3: Connect Arduino to Raspberry Pi

1. Connect the Arduino Nano to the Raspberry Pi using the USB cable
2. The Arduino should light up (power indicator)

---

## Part 3: Install the Software

### Step 3.1: Update the Raspberry Pi

SSH into your Pi and run:

```bash
sudo apt update && sudo apt upgrade -y
```

This may take 5-10 minutes. Wait for it to complete.

### Step 3.2: Install Required System Packages

```bash
sudo apt install -y python3-pip python3-venv git screen i2c-tools
```

### Step 3.3: Enable I2C Interface

```bash
sudo raspi-config
```

Navigate using arrow keys:
1. Select **"Interface Options"**
2. Select **"I2C"**
3. Select **"Yes"** to enable
4. Select **"Finish"**
5. Reboot when prompted, or run: `sudo reboot`

Wait 1-2 minutes, then SSH back in.

### Step 3.4: Install PlatformIO (for Arduino programming)

**What is PlatformIO?**
PlatformIO is a professional development tool for embedded systems that replaces the Arduino IDE. It's faster, more reliable, and works perfectly on a headless Raspberry Pi.

**Official Website:** [https://platformio.org](https://platformio.org)
**Documentation:** [https://docs.platformio.org](https://docs.platformio.org)

Install PlatformIO Core (command-line version):

```bash
pip3 install platformio
```

This will download and install PlatformIO. **It may take 2-5 minutes.**

Add PlatformIO to your PATH so you can run it from anywhere:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Verify installation:**
```bash
pio --version
```

You should see output like: `PlatformIO Core, version X.X.X`

**If the `pio` command is not found:**
- Log out and back in (SSH disconnect and reconnect)
- Or manually add to PATH: `export PATH="$HOME/.local/bin:$PATH"`

**Troubleshooting:**
- **"Command not found"**: Ensure ~/.local/bin is in PATH (check with `echo $PATH`)
- **Permission denied**: Don't use sudo with pip3
- **Installation failed**: Ensure Python 3 is installed (`python3 --version`)

### Step 3.5: Clone the Repository

```bash
cd ~
git clone https://github.com/ericabelson/Air-quality-sensors.git
cd Air-quality-sensors
```

### Step 3.6: Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

If you see errors, try:
```bash
pip3 install pyserial pynmea2 paho-mqtt getmac netifaces PyYAML
```

### Step 3.7: Flash the Arduino Nano

**What this does:** This uploads the sensor-reading firmware from your computer to the Arduino Nano's memory.

**Before proceeding:**
1. Ensure Arduino Nano is connected to Raspberry Pi via USB cable
2. Verify Arduino is detected:
   ```bash
   ls /dev/ttyUSB*
   ```
   You should see `/dev/ttyUSB0` or similar

**Set permissions (IMPORTANT):**
```bash
# Give permission to access the serial port
sudo chmod 666 /dev/ttyUSB0

# Add your user to dialout group for permanent access
sudo usermod -a -G dialout $USER
```

**Log out and back in for group change to take effect:**
```bash
exit
```
Then SSH back in: `ssh pi@[YOUR_PI_IP]`

**Now flash the firmware:**
```bash
cd ~/Air-quality-sensors/firmware/airNano
pio run -t upload
```

**What you should see:**
```
Processing nanoatmega328 (platform: atmelavr; board: nanoatmega328; framework: arduino)
...
Linking .pio/build/nanoatmega328/firmware.elf
Building .pio/build/nanoatmega328/firmware.hex
...
avrdude: 6502 bytes of flash written
avrdude: verifying ...
avrdude: 6502 bytes of flash verified

SUCCESS
```

**If upload fails with "permission denied":**
- Run: `sudo chmod 666 /dev/ttyUSB0`
- Ensure you logged out and back in after adding user to dialout group

**If upload fails with "device not found":**
- Check USB cable is connected
- Try a different USB port on the Raspberry Pi
- Verify with: `dmesg | tail -20` (you should see "USB device" messages)
- Try a different USB cable (some cables are power-only, not data)

**If upload fails with "programmer not responding":**
- Arduino Nano clone may use old bootloader
- Edit `platformio.ini` and add: `upload_speed = 57600`
- Try uploading again

**To see detailed Arduino output:**
```bash
dmesg | tail -20
```

Look for lines like:
```
usb 1-1.3: new full-speed USB device number 5 using dwc_otg
usb 1-1.3: New USB device found, idVendor=1a86, idProduct=7523
ch341-uart converter now attached to ttyUSB0
```

---

## Part 4: Configure the System

### Step 4.1: Set Up Data Directories

```bash
sudo mkdir -p /home/utsensing/utData/raw
sudo mkdir -p /home/utsensing/utData/reference
sudo chown -R pi:pi /home/utsensing
```

### Step 4.2: Configure Definitions

Edit the configuration file:

```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
```

Update these lines:

```python
# Change data folder to match your setup
dataFolder = "/home/utsensing/utData/raw"
dataFolderReference = "/home/utsensing/utData/reference"

# Set to True to enable features
latestOn = True          # Enable JSON output
latestDisplayOn = True   # Enable display updates
mqttOn = False           # Set True if using MQTT
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### Step 4.3: Test Serial Connection

```bash
ls /dev/ttyUSB*
```

You should see something like `/dev/ttyUSB0`. If you see multiple ports, the Arduino is usually `ttyUSB0`.

---

## Part 5: Test Everything

### Step 5.1: Test the Sensor Reader

```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt
python3 nanoReader.py
```

**Expected output:**
```
-----------------------------------
BME680
OrderedDict([('dateTime', '2024-01-15 10:30:45.123456'),
             ('temperature', '25.3'), ('pressure', '1.013'),
             ('humidity', '45.2'), ('gas', '50.2')])
-----------------------------------
SCD30
OrderedDict([('dateTime', '2024-01-15 10:30:46.234567'),
             ('co2', '450'), ('temperature', '25.1'),
             ('humidity', '44.8')])
```

Press `Ctrl+C` to stop.

### Step 5.2: Check Data Files

```bash
ls -la /home/utsensing/utData/raw/
```

You should see a folder named with your Pi's MAC address.

### Step 5.3: Check JSON Output

```bash
cat /home/utsensing/utData/raw/*/BME680.json
```

**Expected output:**
```json
{"dateTime": "2024-01-15 10:30:45.123456", "temperature": "25.3", ...}
```

---

## Part 6: Set Up Auto-Start

### Step 6.1: Create Systemd Service

```bash
sudo nano /etc/systemd/system/utsensing.service
```

Paste this content:

```ini
[Unit]
Description=UTSensing Air Quality Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Air-quality-sensors/firmware/xu4Mqqt
ExecStart=/usr/bin/python3 /home/pi/Air-quality-sensors/firmware/xu4Mqqt/nanoReader.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

### Step 6.2: Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable utsensing
sudo systemctl start utsensing
```

### Step 6.3: Verify It's Running

```bash
sudo systemctl status utsensing
```

**Expected output:**
```
● utsensing.service - UTSensing Air Quality Monitor
     Loaded: loaded (/etc/systemd/system/utsensing.service; enabled)
     Active: active (running) since ...
```

---

## Part 7: Install Home Assistant Dashboard

### Step 7.1: Install Home Assistant

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Log out and back in
exit
# SSH back in

# Install Home Assistant Container
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v /home/pi/homeassistant:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Wait 5-10 minutes for initial setup.

### Step 7.2: Access Home Assistant

Open a web browser and go to:

```
http://[YOUR_PI_IP]:8123
```

Follow the onboarding wizard to create an account.

### Step 7.3: Configure Sensor Integration

See [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md) for detailed dashboard configuration.

---

## Troubleshooting

### Problem: "Permission denied" when accessing serial port

```bash
sudo chmod 666 /dev/ttyUSB0
sudo usermod -a -G dialout pi
# Log out and back in
```

### Problem: Arduino not detected

1. Try a different USB port
2. Try a different USB cable
3. Check with: `dmesg | tail -20`

### Problem: Sensors not responding

1. Check I2C connections:
   ```bash
   i2cdetect -y 1
   ```
   You should see addresses like 0x61, 0x76, 0x58

2. Verify wiring (SDA to A4, SCL to A5)

### Problem: No data in CSV files

1. Check service is running:
   ```bash
   sudo systemctl status utsensing
   ```

2. Check for errors:
   ```bash
   journalctl -u utsensing -f
   ```

### Problem: Wrong sensor readings

1. Make sure sensors have warmed up (wait 5-10 minutes after power on)
2. MQ136 needs 24-48 hours of burn-in for accurate readings

---

## Next Steps

Congratulations! Your air quality monitor is now running!

- [Set up the dashboard](HOME_ASSISTANT_SETUP.md)
- [Understand sensor data](SENSOR_INTERPRETATION.md)
- [Configure a Fire tablet display](FIRE_TABLET_SETUP.md)

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the logs: `journalctl -u utsensing -n 100`
3. Open an issue on GitHub with:
   - Your error message
   - Output of `sudo systemctl status utsensing`
   - Output of `ls /dev/ttyUSB*`
