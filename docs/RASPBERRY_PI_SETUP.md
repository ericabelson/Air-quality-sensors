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
9. [Part 8: Security Hardening](#part-8-security-hardening-recommended) (Recommended)
10. [Troubleshooting](#troubleshooting)

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

> **Note about Raspberry Pi Connect:** The Raspberry Pi Imager may offer to enable "Raspberry Pi Connect" - a remote access service from Raspberry Pi. **You do not need to enable this** for the air quality monitor. Pi Connect provides terminal/desktop access to your Pi but does not help with viewing your sensor dashboard remotely. If you want to access your dashboard from outside your home network, see [Remote Access Guide](REMOTE_ACCESS.md) for better options.

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

**Note:** If you configured a different username during the Raspberry Pi Imager setup (like `demeter`), use that username instead:
```bash
ssh demeter@192.168.1.100
```

Type `yes` when asked about the fingerprint, then enter your password.

**You should now see:**
```
pi@utsensing:~ $
```
or
```
demeter@utsensing:~ $
```

**Windows Users:** See [WINDOWS_SSH_SETUP.md](WINDOWS_SSH_SETUP.md) for detailed SSH key setup instructions.

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

**Modern Raspberry Pi OS uses "externally-managed environment" which prevents system-wide pip installs.**

**Option A: Use Virtual Environment (Recommended)**

```bash
cd ~/Air-quality-sensors
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

**You'll need to activate the virtual environment each time:**
```bash
cd ~/Air-quality-sensors
source venv/bin/activate
```

**Option B: Install System-Wide (Override Protection)**

```bash
pip3 install --break-system-packages -r requirements.txt
```

**⚠️ Warning:** Option B may cause conflicts with system packages. Option A is safer.

If you see errors, manually install core dependencies:
```bash
pip3 install pyserial pynmea2 paho-mqtt getmac netifaces PyYAML requests numpy
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
sudo mkdir -p /home/pi/utData/raw
sudo mkdir -p /home/pi/utData/reference
sudo chown -R pi:pi /home/pi
```

### Step 4.2: Configure Definitions

Edit the configuration file:

```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
```

Update these lines:

```python
# Change data folder to match your setup
dataFolder = "/home/pi/utData/raw"
dataFolderReference = "/home/pi/utData/reference"

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
ls -la /home/pi/utData/raw/
```

You should see a folder named with your Pi's MAC address.

### Step 5.3: Check JSON Output

```bash
cat /home/pi/utData/raw/*/BME680.json
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

### Problem: "FileNotFoundError: credentials.yml"

**Cause:** MQTT credentials file is missing, but the code tries to load it.

**Solution:**

MQTT is disabled by default (`mqttOn = False` in mintsDefinitions.py), but the credentials file is still referenced in the code.

```bash
cd ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4
cp credentials.yml.example credentials.yml
```

If you don't plan to use MQTT, you can leave the example values. If you want to use MQTT:

```bash
nano credentials.yml
# Update with your MQTT broker username and password
```

### Problem: "ModuleNotFoundError: No module named 'requests'"

**Cause:** The `requests` module wasn't installed with the requirements.

**Solution:**

```bash
cd ~/Air-quality-sensors
source venv/bin/activate  # If using virtual environment
pip3 install requests
```

Or reinstall all requirements:
```bash
pip3 install -r requirements.txt
```

### Problem: "externally-managed-environment" error when using pip

**Cause:** Modern Raspberry Pi OS prevents system-wide pip installs to avoid conflicts.

**Solution:** Use a virtual environment (recommended):

```bash
cd ~/Air-quality-sensors
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Problem: "Permission denied" when accessing serial port

```bash
sudo chmod 666 /dev/ttyUSB0
sudo usermod -a -G dialout pi
# Log out and back in
```

### Problem: Arduino not detected

1. Try a different USB port
2. Try a different USB cable (some cables are power-only)
3. Check with: `dmesg | tail -20`
4. Verify Arduino appears: `ls /dev/ttyUSB*`

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

3. Verify data directory exists:
   ```bash
   ls -la /home/pi/utData/raw/
   ```

### Problem: Wrong sensor readings

1. Make sure sensors have warmed up (wait 5-10 minutes after power on)
2. MQ136 needs 24-48 hours of burn-in for accurate readings
3. Check sensor connections are secure

### Problem: Virtual environment not activated

**Symptom:** Commands fail with module not found errors

**Solution:** Always activate the virtual environment before running scripts:

```bash
cd ~/Air-quality-sensors
source venv/bin/activate
# Now your prompt should show: (venv) pi@utsensing:~/Air-quality-sensors $
```

### Problem: Security verification checks fail

**Symptom:** One or more commands in Step 8.5 don't show expected results

**Solutions by component:**

**Firewall not active:**
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw status
```

**Fail2ban not running:**
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status sshd
```

**Automatic updates not enabled:**
```bash
sudo systemctl enable unattended-upgrades
sudo systemctl start unattended-upgrades
```

**Unexpected cron jobs found:**
```bash
# View the suspicious cron job
sudo crontab -u [username] -l

# Remove if unauthorized
sudo crontab -u [username] -r
```

**SSH key login not working:**
- See [WINDOWS_SSH_SETUP.md](WINDOWS_SSH_SETUP.md#troubleshooting) for detailed SSH key troubleshooting
- Check permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`
- Verify key is in authorized_keys: `cat ~/.ssh/authorized_keys`

---

## Part 8: Security Hardening (Recommended)

Your Raspberry Pi is a computer on your network. Take a few minutes to secure it.

### Step 8.1: Set Up SSH Key Authentication FIRST (Recommended)

**⚠️ IMPORTANT:** Set up SSH keys BEFORE running the security hardening script!

SSH keys are more secure than passwords and the security script may disable password authentication.

**Windows Users:** Follow the comprehensive guide at [WINDOWS_SSH_SETUP.md](WINDOWS_SSH_SETUP.md)

**Mac/Linux Users:**

```bash
# On your computer (not the Pi)
ssh-keygen -t ed25519 -C "air-quality-pi"

# Copy to your Pi
ssh-copy-id pi@[YOUR_PI_IP]
# Use your username if different from 'pi'
```

**Test it works:**
```bash
ssh pi@[YOUR_PI_IP]
# You should connect without entering a password!
```

### Step 8.2: Run the Security Hardening Script

Now that SSH keys are set up, run the security hardening script:

```bash
cd ~/Air-quality-sensors/scripts
chmod +x security-hardening.sh
sudo bash security-hardening.sh
```

**What the script does:**
- Configures SSH hardening (disable root login, limit connection attempts)
- Installs fail2ban (automatically blocks brute-force attacks)
- Sets up UFW firewall (blocks unauthorized network access)
- Enables automatic security updates

**During the script:**
- When asked "Do you want to continue WITHOUT disabling password authentication? [y/N]"
  - If you set up SSH keys: Type **`n`** and press Enter (script will disable passwords)
  - If you skipped SSH keys: Type **`y`** and press Enter (keeps passwords enabled)

**IMPORTANT:** After running the script, open a NEW terminal and verify you can still SSH in before closing your current session.

### Step 8.2.1: Verify Security Script Completed Successfully

After the security hardening script finishes, run these verification commands:

```bash
# Verify firewall is active and configured
sudo ufw status
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     LIMIT       Anywhere
22/tcp (v6)                LIMIT       Anywhere (v6)
```

```bash
# Verify fail2ban is running and protecting SSH
sudo fail2ban-client status sshd
```

**Expected output:**
```
Status for the jail: sshd
|- Filter
|  |- Currently failed: 0
|  |- Total failed:     0
|  `- Journal matches:  _SYSTEMD_UNIT=sshd.service
`- Actions
   |- Currently banned: 0
   |- Total banned:     0
   `- Banned IP list:
```

```bash
# Verify automatic security updates are enabled
sudo systemctl status unattended-upgrades
```

**Expected output:**
```
● unattended-upgrades.service - Unattended Upgrades Shutdown
     Loaded: loaded (/lib/systemd/system/unattended-upgrades.service; enabled; preset: enabled)
     Active: active (running) since ...
```

### Step 8.2.2: Check for Old Cron Jobs

Verify no old or unauthorized scheduled tasks are running:

```bash
# Check cron jobs for all common users
sudo crontab -u pi -l 2>/dev/null || echo "No crontab for demeter"
sudo crontab -u pi -l 2>/dev/null || echo "No crontab for pi"
sudo crontab -u root -l 2>/dev/null || echo "No crontab for root"
```

**Expected output:**
```
No crontab for demeter
No crontab for pi
```

Root may have system maintenance tasks - that's normal. Just verify there are no unexpected entries pointing to external servers.

### Step 8.2.3: Disable Password Authentication (After SSH Keys Work)

**ONLY do this after confirming SSH key login works!**

If you successfully set up SSH keys in Step 8.1, now disable password authentication:

```bash
# Edit the SSH security hardening configuration
sudo nano /etc/ssh/sshd_config.d/security-hardening.conf
```

Find this line:
```
# PasswordAuthentication no
```

Uncomment it (remove the `#`):
```
PasswordAuthentication no
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

Restart SSH service:
```bash
sudo systemctl restart sshd
```

**CRITICAL:** Open a NEW PowerShell/terminal window and test SSH login BEFORE closing your current session:

```bash
ssh pi@192.168.1.100
# Should connect using SSH key without asking for password!
```

If the new connection works, your Pi now only accepts SSH keys. If it fails, you can fix it from your current still-open session.

### Step 8.3: Enable Home Assistant 2FA

1. Log into Home Assistant at `http://[YOUR_PI_IP]:8123`
2. Click your username (bottom left of sidebar)
3. Scroll to **Multi-factor Authentication Modules**
4. Click **Enable** next to **Totp**
5. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)

### Step 8.4: Network Segmentation (Recommended)

Isolate your Raspberry Pi on a separate network to protect your computers and phones from potential IoT device vulnerabilities.

**For TP-Link Deco M9 Plus Users (Quick Steps):**

1. Open the **Deco app** on your phone
2. Tap **More** → **Guest Network**
3. Enable Guest Network and name it **"IoT-Devices"**
4. **IMPORTANT:** Ensure **Guest Network Isolation is ON**
5. Note the WiFi password
6. On your Raspberry Pi, reconnect to the "IoT-Devices" network:
   ```bash
   sudo raspi-config
   # Navigate to: System Options → Wireless LAN
   # Enter SSID: IoT-Devices
   # Enter password: [your guest network password]
   ```
7. Reboot: `sudo reboot`

**For Other Routers:**

- Use your router's "Guest Network" or "IoT Network" feature
- Ensure guest network isolation is enabled
- See [SECURITY.md](SECURITY.md#network-segmentation) for detailed instructions for other router brands

### Step 8.5: Complete Security Verification Checklist

Run through this final checklist to confirm everything is secured:

```bash
# 1. Verify firewall is active
sudo ufw status | grep "Status: active"

# 2. Verify fail2ban is protecting SSH
sudo fail2ban-client status sshd | grep "Currently banned"

# 3. Verify automatic updates enabled
sudo systemctl is-enabled unattended-upgrades

# 4. Verify no unexpected cron jobs
sudo crontab -u pi -l 2>/dev/null || echo "✓ No crontab for demeter"
sudo crontab -u pi -l 2>/dev/null || echo "✓ No crontab for pi"

# 5. Verify SSH key authentication works
# (Test from a NEW terminal window on your computer)

# 6. Verify password authentication is disabled (if you set it up)
sudo grep "^PasswordAuthentication no" /etc/ssh/sshd_config.d/security-hardening.conf
```

**Expected Results:**
- ✅ Firewall: Status: active
- ✅ Fail2ban: Currently banned: 0 (service is running)
- ✅ Auto-updates: enabled
- ✅ Cron jobs: No unexpected entries
- ✅ SSH keys: Can connect without password
- ✅ Password auth: Disabled (shows "PasswordAuthentication no")

If all checks pass, your Raspberry Pi is properly secured!

### Security Resources

For complete security documentation, see:
- [SECURITY.md](SECURITY.md) - Full security guide with network segmentation
- [REMOTE_ACCESS.md](REMOTE_ACCESS.md) - Secure remote access options
- [WINDOWS_SSH_SETUP.md](WINDOWS_SSH_SETUP.md) - Detailed SSH key setup for Windows

---

## Next Steps

Congratulations! Your air quality monitor is now running!

- [Set up the dashboard](HOME_ASSISTANT_SETUP.md)
- [Understand sensor data](SENSOR_INTERPRETATION.md)
- [Configure a Fire tablet display](FIRE_TABLET_SETUP.md)
- [Access your dashboard remotely](REMOTE_ACCESS.md) - View your air quality data from anywhere
- [Secure your installation](SECURITY.md) - Protect your network (highly recommended)

---

## Quick Reference: Common Commands

**SSH Connection:**
```bash
# From Windows PowerShell or Mac/Linux Terminal
ssh pi@192.168.1.100
```

**Activate Virtual Environment:**
```bash
cd ~/Air-quality-sensors
source venv/bin/activate
```

**Check Sensor Service:**
```bash
# Check if running
sudo systemctl status utsensing

# View live logs
journalctl -u utsensing -f

# Restart service
sudo systemctl restart utsensing
```

**View Sensor Data:**
```bash
# List data folders
ls -la /home/pi/utData/raw/

# View latest readings (JSON format)
cat /home/pi/utData/raw/*/BME680.json
cat /home/pi/utData/raw/*/SCD30.json
```

**Security Checks:**
```bash
# Firewall status
sudo ufw status

# Fail2ban status
sudo fail2ban-client status sshd

# Check for unauthorized cron jobs
sudo crontab -u pi -l 2>/dev/null || echo "No crontab"
```

**Update Repository:**
```bash
cd ~/Air-quality-sensors
git pull origin main
```

**Home Assistant:**
```bash
# Access dashboard
http://192.168.1.100:8123

# Check container status
docker ps

# View logs
docker logs homeassistant
```

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the logs: `journalctl -u utsensing -n 100`
3. Run security verification checklist (Step 8.5)
4. Verify virtual environment is activated: `which python3` should show path with `venv`
5. Open an issue on GitHub with:
   - Your error message
   - Output of `sudo systemctl status utsensing`
   - Output of `ls /dev/ttyUSB*`
   - Output of security verification commands
