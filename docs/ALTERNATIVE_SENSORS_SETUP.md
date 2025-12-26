# Alternative Sensors Setup Guide

Get started with Home Assistant and a dashboard display **without** the Arduino Nano sensor kit. Use Bluetooth sensors (like Aranet 4), door/window switches, or any Home Assistant-compatible device.

**Time Required:** 1-2 hours
**Prerequisites:** Raspberry Pi 4 with Raspberry Pi OS installed

---

## Table of Contents

1. [Overview](#overview)
2. [What You Can Monitor](#what-you-can-monitor)
3. [Part 1: Base Setup](#part-1-base-setup)
4. [Part 2: Aranet 4 Bluetooth Setup](#part-2-aranet-4-bluetooth-setup)
5. [Part 3: Door and Window Sensors](#part-3-door-and-window-sensors)
6. [Part 4: Create Your Dashboard](#part-4-create-your-dashboard)
7. [Part 5: Add Fire Tablet Display](#part-5-add-fire-tablet-display)
8. [Adding Arduino Sensors Later](#adding-arduino-sensors-later)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The UTSensing system uses Home Assistant as its display layer. This means you can start building your monitoring dashboard with **any** sensors that Home Assistant supports - you don't need the Arduino kit to get started.

```
┌─────────────────────────────────────────────────────────────┐
│                    ALTERNATIVE SENSORS                       │
│                                                              │
│   ┌───────────────┐          ┌───────────────┐              │
│   │   Aranet 4    │          │  Door/Window  │              │
│   │  (Bluetooth)  │          │   Switches    │              │
│   └───────┬───────┘          └───────┬───────┘              │
│           │                          │                       │
│           │ Bluetooth                │ Zigbee/Z-Wave/GPIO   │
│           │                          │                       │
│           ▼                          ▼                       │
│   ┌─────────────────────────────────────────────┐           │
│   │           Raspberry Pi 4                     │           │
│   │    ┌─────────────────────────────────┐      │           │
│   │    │        Home Assistant           │      │           │
│   │    └──────────────┬──────────────────┘      │           │
│   └──────────────────┼──────────────────────────┘           │
│                      │                                       │
│                      ▼                                       │
│              ┌──────────────┐                               │
│              │ Fire Tablet  │                               │
│              │  (Display)   │                               │
│              └──────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## What You Can Monitor

### Comparison: Arduino Kit vs Alternatives

| Feature | Arduino Kit | Aranet 4 | Door Sensors |
|---------|-------------|----------|--------------|
| CO2 | Yes (SCD30) | Yes | No |
| Temperature | Yes | Yes | Some models |
| Humidity | Yes | Yes | Some models |
| Pressure | Yes (BME680) | Yes | No |
| PM2.5/PM10 | Yes (PMSA003I) | No | No |
| VOCs | Yes (SGP30) | No | No |
| Ozone | Yes (SEN0321) | No | No |
| Door Open/Close | No | No | Yes |
| Battery Powered | No | Yes | Yes |
| Wireless | No (wired) | Bluetooth | Zigbee/Z-Wave |

### What You Can Set Up Now

**With just a Raspberry Pi:**
- Home Assistant dashboard (the foundation)
- Network-based integrations (weather, air quality APIs)
- Any WiFi-based sensors

**With Aranet 4:**
- CO2 monitoring (the most important indoor metric)
- Temperature, humidity, and pressure
- Battery-powered, portable readings

**With door/window sensors:**
- Track which doors/windows are open
- Calculate ventilation status
- Get alerts when doors are left open

---

## Part 1: Base Setup

### Step 1.1: Prepare Raspberry Pi

If you haven't set up your Raspberry Pi yet:

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (64-bit)** - Desktop version recommended
3. Configure: hostname, SSH, username/password, WiFi
4. Boot the Pi and SSH in

### Step 1.2: Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

### Step 1.3: Enable Bluetooth

Bluetooth should be enabled by default, but verify:

```bash
sudo systemctl status bluetooth

# If not running:
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo apt install -y bluez bluetooth
```

### Step 1.4: Install Home Assistant

Follow the [Docker & Home Assistant Setup](setup/DOCKER_HOME_ASSISTANT.md) module.

**Quick version:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
logout
```

SSH back in:
```bash
# Start Home Assistant with Bluetooth support
mkdir -p ~/homeassistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v ~/homeassistant:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Wait 5-10 minutes, then access: `http://[YOUR_PI_IP]:8123`

---

## Part 2: Aranet 4 Bluetooth Setup

The Aranet 4 is an excellent standalone CO2 monitor that broadcasts readings via Bluetooth.

### About Aranet 4

- **Measures:** CO2 (0-9999 ppm), Temperature, Humidity, Pressure
- **Display:** Built-in e-ink screen
- **Battery:** ~2 years on 2x AA batteries
- **Range:** ~10 meters Bluetooth
- **Cost:** ~$200-250

### Step 2.1: Prepare Your Aranet 4

1. Insert batteries
2. Wait for startup (~30 seconds)
3. Verify readings appear on its screen
4. Place within 10 meters of your Raspberry Pi

### Step 2.2: Enable Bluetooth Integration

1. In Home Assistant: **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "**Bluetooth**"
4. Follow the prompts

### Step 2.3: Add Aranet 4

Home Assistant should automatically discover your Aranet 4:

1. Go to **Settings** → **Devices & Services**
2. Look for discovered devices notification
3. Click **Configure** next to "Aranet4"

**If not auto-discovered:**
1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for "**Aranet**" or "**Aranet4**"
3. Select your device from the scan results

### Step 2.4: Verify Sensors

After adding, check **Settings** → **Devices & Services** → **Aranet4**:

You should see:
- `sensor.aranet4_xxxx_co2` - CO2 in ppm
- `sensor.aranet4_xxxx_temperature` - Temperature
- `sensor.aranet4_xxxx_humidity` - Humidity
- `sensor.aranet4_xxxx_pressure` - Pressure
- `sensor.aranet4_xxxx_battery` - Battery level

---

## Part 3: Door and Window Sensors

### Option A: Zigbee Sensors (Recommended)

**What you need:**
- Zigbee USB coordinator (Sonoff Zigbee 3.0 USB Dongle Plus, ~$25)
- Zigbee door sensors (Aqara Door Sensor, ~$15 each)

**Setup:**
1. Plug Zigbee USB dongle into Raspberry Pi
2. In Home Assistant: **Settings** → **Devices & Services** → **+ Add Integration**
3. Search for "**ZHA**" (Zigbee Home Automation)
4. Select your USB device path (`/dev/ttyUSB0` or `/dev/ttyACM0`)
5. To pair sensors: **ZHA** → **Add Device** → put sensor in pairing mode

### Option B: Z-Wave Sensors

**What you need:**
- Z-Wave USB stick (Aeotec Z-Stick Gen5+, ~$35-45)
- Z-Wave door sensors (~$30-40 each)

**Setup:**
1. Plug Z-Wave USB stick into Raspberry Pi
2. Install Z-Wave JS UI container:
   ```bash
   mkdir -p ~/zwavejs
   docker run -d \
     --name zwavejs \
     --restart=unless-stopped \
     -p 8091:8091 \
     -p 3000:3000 \
     -v ~/zwavejs:/usr/src/app/store \
     --device=/dev/ttyUSB0:/dev/zwave \
     zwavejs/zwave-js-ui:latest
   ```
3. Configure at `http://[YOUR_PI_IP]:8091`
4. In Home Assistant: **Settings** → **Devices & Services** → **+ Add Integration** → "**Z-Wave**"
5. Server URL: `ws://localhost:3000`

### Option C: GPIO Direct Connection

Connect reed switches directly to Raspberry Pi GPIO pins:

```yaml
# Add to configuration.yaml
binary_sensor:
  - platform: rpi_gpio
    ports:
      17: Front Door
      27: Back Door
    pull_mode: UP
    invert_logic: true
```

---

## Part 4: Create Your Dashboard

### Step 4.1: Create New Dashboard

1. **Settings** → **Dashboards** → **+ Add Dashboard**
2. Name: "Home Monitor"
3. Enable "Show in sidebar"

### Step 4.2: Add Cards

Open your dashboard, click ⋮ → **Edit Dashboard** → **+ Add Card**

**CO2 Gauge:**
```yaml
type: gauge
entity: sensor.aranet4_xxxx_co2
name: CO2 Level
min: 400
max: 2500
severity:
  green: 400
  yellow: 800
  red: 1000
needle: true
```

**Environment Summary:**
```yaml
type: horizontal-stack
cards:
  - type: entity
    entity: sensor.aranet4_xxxx_temperature
    name: Temperature
  - type: entity
    entity: sensor.aranet4_xxxx_humidity
    name: Humidity
  - type: entity
    entity: sensor.aranet4_xxxx_battery
    name: Battery
```

**Door Status:**
```yaml
type: entities
title: Doors & Windows
entities:
  - entity: binary_sensor.front_door
    name: Front Door
  - entity: binary_sensor.back_door
    name: Back Door
```

**History Graph:**
```yaml
type: history-graph
title: CO2 History (24 Hours)
hours_to_show: 24
entities:
  - entity: sensor.aranet4_xxxx_co2
    name: CO2
```

### Step 4.3: Add Automations

**High CO2 Alert:**
```yaml
automation:
  - id: 'high_co2_alert'
    alias: High CO2 Alert
    trigger:
      - platform: numeric_state
        entity_id: sensor.aranet4_xxxx_co2
        above: 1000
        for:
          minutes: 5
    action:
      - service: persistent_notification.create
        data:
          title: "High CO2 Detected!"
          message: "CO2 is {{ states('sensor.aranet4_xxxx_co2') }} ppm. Open a window."
```

---

## Part 5: Add Fire Tablet Display

See [Fire Tablet Setup](FIRE_TABLET_SETUP.md) for detailed instructions.

**Quick summary:**
1. Get a Fire HD 8 or HD 10 tablet
2. Sideload Fully Kiosk Browser from [fully-kiosk.com](https://www.fully-kiosk.com)
3. Set URL to: `http://[PI_IP]:8123/lovelace/home`
4. Enable kiosk mode

---

## Adding Arduino Sensors Later

When you get the Arduino Nano and sensors:

1. Follow [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md) for hardware assembly
2. Follow [MQTT Setup](setup/MQTT_SETUP.md) for sensor data
3. Add Arduino sensors to your existing dashboard

The system is designed to expand - your existing sensors will continue working alongside the Arduino sensors.

---

## Troubleshooting

### Aranet 4 Not Discovered

1. Check Bluetooth is working:
   ```bash
   sudo bluetoothctl
   power on
   scan on
   # Look for "Aranet4" in the list
   quit
   ```

2. Verify Docker has Bluetooth access:
   ```bash
   docker stop homeassistant
   docker rm homeassistant
   # Restart with -v /run/dbus:/run/dbus:ro flag
   ```

3. Move Aranet 4 closer (within 10 meters)

### Zigbee Devices Not Pairing

1. Check USB device detected: `ls /dev/ttyUSB* /dev/ttyACM*`
2. Factory reset the sensor (usually hold button 10+ seconds)
3. Try pairing immediately after reset

### Door Sensor Shows Wrong State

1. Check magnet alignment (within 1-2cm)
2. Invert logic in Home Assistant entity settings

### Bluetooth Interference

If Bluetooth is unreliable:
1. Use a USB extension cable for the Bluetooth adapter
2. Disable WiFi power management:
   ```bash
   sudo nano /etc/rc.local
   # Add before "exit 0":
   iwconfig wlan0 power off
   ```

---

## Hardware Shopping List

### Minimum Setup (Aranet 4 Only)

| Item | Price |
|------|-------|
| Raspberry Pi 4 (4GB) | ~$55 |
| 32GB microSD Card | ~$10 |
| USB-C Power Supply | ~$15 |
| Aranet 4 | ~$250 |
| **Total** | **~$330** |

### Adding Door Sensors

| Item | Price |
|------|-------|
| Sonoff Zigbee 3.0 USB Dongle | ~$25 |
| Aqara Door Sensor (x3) | ~$45 |
| **Additional Total** | **~$70** |

### Fire Tablet Display

| Item | Price |
|------|-------|
| Fire HD 8 | ~$50-100 |
| Tablet Stand | ~$15 |
| **Additional Total** | **~$65-115** |

---

## Next Steps

- [Fire Tablet Setup](FIRE_TABLET_SETUP.md) - Dedicated display
- [WS 3000 X5 Setup](WS3000_SETUP.md) - Weather station via USB
- [Sensor Interpretation](SENSOR_INTERPRETATION.md) - Understanding readings
- [Security Guide](SECURITY.md) - Securing your installation
