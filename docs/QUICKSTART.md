# Quick Start Guide

Get your air quality monitor running as fast as possible. This guide covers only the essential steps.

**Time:** 2 hours | **For:** Users comfortable with command line

**Need more detail?** Use the [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) instead.

---

## Prerequisites

- [ ] Raspberry Pi 4 with power supply
- [ ] 32GB+ MicroSD card
- [ ] Arduino Nano with sensors connected
- [ ] Computer with SD card reader

---

## Step 1: Flash Pi (10 min)

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (64-bit)**
3. Click gear icon, configure:
   - Hostname: `utsensing`
   - Enable SSH
   - Set username/password
   - Configure WiFi
4. Write to SD card

---

## Step 2: First Boot (5 min)

1. Insert SD card, connect Arduino via USB, power on
2. Wait 2-3 minutes
3. SSH in: `ssh pi@utsensing.local` (or use IP address)

---

## Step 3: Install Software (15 min)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install packages
sudo apt install -y python3-pip python3-venv git i2c-tools

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Clone repository
cd ~
git clone https://github.com/ericabelson/Air-quality-sensors.git
cd Air-quality-sensors

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# Install PlatformIO
pip3 install platformio
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Step 4: Flash Arduino (5 min)

```bash
# Set permissions
sudo chmod 666 /dev/ttyUSB0
sudo usermod -a -G dialout $USER

# Flash firmware
cd ~/Air-quality-sensors/firmware/airNano
pio run -t upload
```

---

## Step 5: Configure & Test (5 min)

```bash
# Create data directories
sudo mkdir -p /home/pi/utData/raw
sudo chown -R pi:pi /home/pi

# Test sensors
cd ~/Air-quality-sensors/firmware/xu4Mqqt
python3 nanoReader.py
```

You should see sensor data. Press Ctrl+C to stop.

---

## Step 6: Auto-Start Service (5 min)

```bash
sudo tee /etc/systemd/system/utsensing.service > /dev/null <<EOF
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
EOF

sudo systemctl daemon-reload
sudo systemctl enable utsensing
sudo systemctl start utsensing
```

---

## Step 7: Install Dashboard (20 min)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
logout
```

SSH back in, then:

```bash
# Start Home Assistant
mkdir -p ~/homeassistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v ~/homeassistant:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Wait 5-10 minutes, then open: `http://[YOUR_PI_IP]:8123`

---

## Step 8: Add MQTT (10 min)

```bash
# Install Mosquitto
sudo apt install -y mosquitto mosquitto-clients

# Configure
sudo tee /etc/mosquitto/conf.d/utsensing.conf > /dev/null <<EOF
listener 1883
allow_anonymous true
EOF

sudo systemctl restart mosquitto
```

In Home Assistant:
1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search "MQTT" → Broker: `localhost`, Port: `1883`

Enable MQTT in UTSensing:
```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
# Set: mqttOn = True

sudo systemctl restart utsensing
```

---

## Done!

Your sensor data is now:
- Saved to CSV files in `/home/pi/utData/raw/`
- Published via MQTT to Home Assistant
- Viewable at `http://[YOUR_PI_IP]:8123`

---

## Next Steps

| Task | Guide |
|------|-------|
| Configure dashboard | [Home Assistant Setup](HOME_ASSISTANT_SETUP.md) |
| Add Fire tablet display | [Fire Tablet Setup](FIRE_TABLET_SETUP.md) |
| Understand readings | [Sensor Interpretation](SENSOR_INTERPRETATION.md) |
| Secure your Pi | [Security Guide](SECURITY.md) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Arduino not detected | Check USB cable, run `ls /dev/ttyUSB*` |
| Permission denied | Run `sudo chmod 666 /dev/ttyUSB0` |
| No sensor data | Check `sudo systemctl status utsensing` |
| MQTT not working | Check `mosquitto_sub -h localhost -t "utsensing/#" -v` |

For detailed troubleshooting, see [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md#troubleshooting).
