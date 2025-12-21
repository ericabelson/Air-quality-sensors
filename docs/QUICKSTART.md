# Quick Start Guide

Get your UTSensing air quality monitor up and running in under 2 hours.

---

## Before You Start

### You Need

- [ ] Raspberry Pi 4 (with power supply)
- [ ] 32GB+ MicroSD card
- [ ] Arduino Nano with sensors connected
- [ ] Computer with SD card reader
- [ ] WiFi password

### Optional (for display)

- [ ] Amazon Fire HD tablet

---

## Step 1: Flash Raspberry Pi OS (15 min)

1. Download **Raspberry Pi Imager** from: https://www.raspberrypi.com/software/
2. Insert SD card into your computer
3. Open Raspberry Pi Imager
4. Click **Choose OS** → **Raspberry Pi OS (64-bit)**
5. Click **Choose Storage** → Select your SD card
6. Click the **gear icon** and configure:
   ```
   Hostname: utsensing
   Enable SSH: Yes
   Username: pi
   Password: [your choice]
   WiFi: [your network name and password]
   Timezone: [your timezone]
   ```
7. Click **Save** then **Write**
8. Wait for completion, then remove SD card

---

## Step 2: Boot and Connect (5 min)

1. Insert SD card into Raspberry Pi
2. Connect Arduino Nano to Pi via USB
3. Power on the Raspberry Pi
4. Wait 2-3 minutes for boot
5. Find Pi's IP address:
   - Check your router's connected devices, OR
   - Use an IP scanner app on your phone
6. SSH into the Pi:
   ```bash
   ssh pi@[YOUR_PI_IP]
   ```
   Enter your password when prompted.

---

## Step 3: Install Software (20 min)

Run these commands one by one:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git i2c-tools

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Install PlatformIO for Arduino
pip3 install platformio
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Clone the repository
cd ~
git clone https://github.com/mi3nts/UTSensing.git

# Install Python dependencies
cd UTSensing
pip3 install -r requirements.txt
```

---

## Step 4: Flash Arduino (5 min)

```bash
# Navigate to Arduino firmware
cd ~/UTSensing/firmware/airNano

# Set permissions for serial port
sudo chmod 666 /dev/ttyUSB0
sudo usermod -a -G dialout $USER

# Flash the Arduino
pio run -t upload
```

If you get permission errors, log out and back in:
```bash
exit
# SSH back in
ssh pi@[YOUR_PI_IP]
```

---

## Step 5: Configure Data Collection (5 min)

```bash
# Create data directories
sudo mkdir -p /home/utsensing/utData/raw
sudo chown -R pi:pi /home/utsensing

# Test the sensor reader
cd ~/UTSensing/firmware/xu4Mqqt
python3 nanoReader.py
```

You should see output like:
```
-----------------------------------
BME680
OrderedDict([('dateTime', '...'), ('temperature', '25.3'), ...])
-----------------------------------
SCD30
OrderedDict([('dateTime', '...'), ('co2', '450'), ...])
```

Press `Ctrl+C` to stop.

---

## Step 6: Set Up Auto-Start (5 min)

```bash
# Create service file
sudo tee /etc/systemd/system/utsensing.service > /dev/null <<EOF
[Unit]
Description=UTSensing Air Quality Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/UTSensing/firmware/xu4Mqqt
ExecStart=/usr/bin/python3 /home/pi/UTSensing/firmware/xu4Mqqt/nanoReader.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable utsensing
sudo systemctl start utsensing

# Verify it's running
sudo systemctl status utsensing
```

---

## Step 7: Install Dashboard (30 min)

### Install Docker and Home Assistant

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in
exit
# SSH back in

# Create config directory and start Home Assistant
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

Wait 5-10 minutes for Home Assistant to initialize.

### Access Home Assistant

1. Open browser: `http://[YOUR_PI_IP]:8123`
2. Create your account
3. Complete the setup wizard

### Install MQTT Broker

```bash
# Install Mosquitto
sudo apt install -y mosquitto mosquitto-clients

# Configure for local access
sudo tee /etc/mosquitto/conf.d/utsensing.conf > /dev/null <<EOF
listener 1883
allow_anonymous true
EOF

# Restart Mosquitto
sudo systemctl restart mosquitto
```

### Enable MQTT in UTSensing

```bash
# Edit configuration
nano ~/UTSensing/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py

# Change these lines:
#   mqttOn = True
#   mqttBroker = "localhost"
#   mqttPort = 1883

# Restart the service
sudo systemctl restart utsensing
```

### Add MQTT Integration to Home Assistant

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MQTT"
4. Set broker to `localhost`, port `1883`
5. Click **Submit**

### Add Sensors

```bash
# Copy sensor configuration
mkdir -p ~/homeassistant/packages
cp ~/UTSensing/homeassistant/packages/utsensing_sensors.yaml ~/homeassistant/packages/

# Add packages to configuration
echo 'homeassistant:' >> ~/homeassistant/configuration.yaml
echo '  packages: !include_dir_named packages' >> ~/homeassistant/configuration.yaml

# Restart Home Assistant
docker restart homeassistant
```

### Load Dashboard

1. Wait 1-2 minutes for restart
2. Go to **Settings** → **Dashboards** → **Add Dashboard**
3. Name it "Air Quality"
4. Open the dashboard, click ⋮ → **Edit Dashboard** → ⋮ → **Raw configuration editor**
5. Copy content from `~/UTSensing/homeassistant/dashboards/air_quality_dashboard.yaml`
6. Paste and save

---

## Step 8: Set Up Fire Tablet (Optional, 30 min)

### On the Fire Tablet

1. Complete initial setup, connect to WiFi
2. Install **Fully Kiosk Browser** from Amazon Appstore
3. Open Fully Kiosk, grant all permissions
4. Go to **Settings** → **Web Content Settings**
5. Set Start URL: `http://[YOUR_PI_IP]:8123/lovelace/tablet`
6. Go to **Settings** → **Kiosk Mode**
7. Enable **Enable Kiosk Mode**
8. Set an exit password
9. Enable **Disable Status Bar** and **Disable Navigation Bar**
10. Go to **Settings** → **Device Management**
11. Enable **Keep Screen On**
12. Tap Back until at main screen, tap Home icon

Your tablet now shows the air quality dashboard!

---

## Verification Checklist

- [ ] Sensors are reading data (check `sudo systemctl status utsensing`)
- [ ] CSV files are being created (check `/home/utsensing/utData/raw/`)
- [ ] MQTT is publishing (run `mosquitto_sub -h localhost -t "utsensing/#" -v`)
- [ ] Home Assistant shows sensor values
- [ ] Dashboard displays correctly
- [ ] Fire tablet shows dashboard (if using)

---

## What's Next?

### Understand Your Data

Read [SENSOR_INTERPRETATION.md](SENSOR_INTERPRETATION.md) to learn:
- What each sensor measures
- How to interpret readings
- Health reference values

### Customize Your Dashboard

- Add more graphs
- Create automations
- Set up notifications

### Add More Sensors

You can add multiple UTSensing units to monitor different rooms.

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| No sensor data | Check USB connection, run `ls /dev/ttyUSB*` |
| MQTT not working | Check `sudo systemctl status mosquitto` |
| Dashboard empty | Wait 1-2 minutes, check MQTT integration |
| Service not starting | Check `journalctl -u utsensing -f` |

For detailed help, see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md).

---

## Summary

You now have:

1. **Raspberry Pi 4** running UTSensing data collection
2. **Arduino Nano** reading 7 environmental sensors
3. **Home Assistant** displaying real-time dashboard
4. **Fire Tablet** (optional) as dedicated display

The system:
- Starts automatically on boot
- Logs data continuously to CSV files
- Publishes data via MQTT
- Displays on your tablet 24/7

**Total Setup Time:** ~2 hours
**Ongoing Maintenance:** Minimal (system is self-running)
