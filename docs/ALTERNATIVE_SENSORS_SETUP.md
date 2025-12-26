# Alternative Sensors Setup Guide

Get started with Home Assistant and the Fire tablet display **without** the Arduino Nano sensor kit. This guide covers setting up Bluetooth sensors (like Aranet 4) and door/window switches while you wait for the full sensor kit.

**Time Required:** 1-2 hours
**Prerequisites:** Raspberry Pi 4 with Raspberry Pi OS installed

---

## Table of Contents

1. [Overview](#overview)
2. [What You Can Set Up Now](#what-you-can-set-up-now)
3. [Part 1: Raspberry Pi Base Setup](#part-1-raspberry-pi-base-setup)
4. [Part 2: Home Assistant Installation](#part-2-home-assistant-installation)
5. [Part 3: Aranet 4 Bluetooth Setup](#part-3-aranet-4-bluetooth-setup)
6. [Part 4: Door and Window Sensors](#part-4-door-and-window-sensors)
7. [Part 5: Combined Dashboard](#part-5-combined-dashboard)
8. [Part 6: Fire Tablet Display](#part-6-fire-tablet-display)
9. [Adding Arduino Sensors Later](#adding-arduino-sensors-later)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The UTSensing system uses Home Assistant as its display layer. This means you can start building your monitoring dashboard with **any** sensors that Home Assistant supports - you don't need the Arduino kit to get started.

### What This Guide Covers

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
│   │    │  (Aranet + Door/Window + More)  │      │           │
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

### Comparison: Arduino Sensors vs Alternatives

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

---

## What You Can Set Up Now

### With Just a Raspberry Pi

- Home Assistant dashboard (the foundation)
- Network-based integrations (weather, air quality APIs)
- Any WiFi-based sensors

### With Aranet 4 + Raspberry Pi

- CO2 monitoring (the most important indoor metric)
- Temperature and humidity
- Atmospheric pressure
- Battery-powered, portable readings

### With Door/Window Sensors

- Track which doors/windows are open
- Calculate ventilation status
- Get alerts when doors are left open
- Automate HVAC based on window state

---

## Part 1: Raspberry Pi Base Setup

If you haven't set up your Raspberry Pi yet, follow these steps.

### Step 1.1: Install Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your microSD card
3. Select **Raspberry Pi OS (64-bit)** - Desktop version recommended
4. Click the gear icon to set:
   - Hostname: `airquality` (or your preference)
   - Enable SSH
   - Set username and password
   - Configure WiFi
5. Write to SD card

### Step 1.2: First Boot

1. Insert SD card into Pi and power on
2. Wait 2-3 minutes for first boot
3. Connect via SSH or directly with monitor/keyboard:

```bash
ssh pi@airquality.local
# Or use the IP address: ssh pi@192.168.x.x
```

### Step 1.3: Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

### Step 1.4: Enable Bluetooth (for Aranet 4)

Bluetooth should be enabled by default on Pi 4, but verify:

```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# If not running, enable it
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Install Bluetooth tools
sudo apt install -y bluez bluetooth
```

---

## Part 2: Home Assistant Installation

### Step 2.1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in for group changes
logout
```

Log back in via SSH.

### Step 2.2: Start Home Assistant

```bash
# Create config directory
mkdir -p ~/homeassistant

# Run Home Assistant with Bluetooth access
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

**Note:** The `-v /run/dbus:/run/dbus:ro` line is essential for Bluetooth support.

### Step 2.3: Initial Setup

1. Wait 5-10 minutes for Home Assistant to start
2. Open a browser and go to: `http://airquality.local:8123`
   - Or use your Pi's IP: `http://192.168.x.x:8123`
3. Create your account
4. Set your home location
5. Complete the setup wizard

---

## Part 3: Aranet 4 Bluetooth Setup

The Aranet 4 is an excellent standalone CO2 monitor that broadcasts readings via Bluetooth. Home Assistant can read these automatically.

### What is Aranet 4?

- **Measures:** CO2 (0-9999 ppm), Temperature, Humidity, Pressure
- **Display:** Built-in e-ink screen
- **Battery:** ~2 years on 2x AA batteries
- **Range:** ~10 meters Bluetooth
- **Cost:** ~$200-250

### Step 3.1: Prepare Your Aranet 4

1. Insert batteries into your Aranet 4
2. Wait for it to start up (takes ~30 seconds)
3. Verify readings appear on its screen
4. Place within 10 meters of your Raspberry Pi

### Step 3.2: Enable Bluetooth Integration in Home Assistant

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "**Bluetooth**"
4. Click on **Bluetooth** and follow the prompts
5. Home Assistant will scan for Bluetooth devices

### Step 3.3: Add Aranet 4

Home Assistant should automatically discover your Aranet 4:

1. Go to **Settings** → **Devices & Services**
2. Look for a notification about discovered devices
3. Click **Configure** next to "Aranet4"
4. Follow the prompts to add it

**If not auto-discovered:**

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "**Aranet**" or "**Aranet4**"
4. The integration will scan for nearby devices
5. Select your Aranet 4 from the list

### Step 3.4: Verify Sensors

After adding, go to **Settings** → **Devices & Services** → **Aranet4**:

You should see these entities:
- `sensor.aranet4_xxxx_co2` - CO2 in ppm
- `sensor.aranet4_xxxx_temperature` - Temperature
- `sensor.aranet4_xxxx_humidity` - Humidity
- `sensor.aranet4_xxxx_pressure` - Pressure
- `sensor.aranet4_xxxx_battery` - Battery level

### Step 3.5: Rename for Clarity (Optional)

1. Click on each sensor entity
2. Click the gear icon
3. Change the name to something friendly:
   - "Living Room CO2"
   - "Living Room Temperature"
   - etc.

### Aranet 4 Reading Intervals

The Aranet 4 updates readings every 1-10 minutes (configurable in the Aranet app). Home Assistant will display the latest reading received via Bluetooth.

---

## Part 4: Door and Window Sensors

Door and window sensors help you understand ventilation and security. There are several options depending on your setup.

### Option A: Zigbee Sensors (Recommended)

**Best for:** Most users, especially those new to smart home

**What you need:**
- Zigbee USB coordinator (like Sonoff Zigbee 3.0 USB Dongle Plus - ~$25)
- Zigbee door/window sensors (like Aqara Door Sensor - ~$15 each)

#### Step A.1: Install Zigbee Coordinator

1. Plug the Zigbee USB dongle into your Raspberry Pi
2. Find the device path:
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   ```
   Note the path (usually `/dev/ttyUSB0` or `/dev/ttyACM0`)

#### Step A.2: Install ZHA Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "**ZHA**" (Zigbee Home Automation)
4. Select your USB device path
5. Follow the setup wizard

#### Step A.3: Pair Door Sensors

1. Go to **Settings** → **Devices & Services** → **ZHA**
2. Click **Add Device**
3. Put your door sensor in pairing mode:
   - **Aqara:** Hold the reset button for 5 seconds until LED blinks
   - **Other brands:** Check manual for pairing instructions
4. The sensor should appear in Home Assistant
5. Name it based on location (e.g., "Front Door", "Bedroom Window")

### Option B: Z-Wave Sensors

**Best for:** Users who want longer range and more reliable connections

**What you need:**
- Z-Wave USB stick (like Aeotec Z-Stick Gen5+ or Zooz ZST10 700 - ~$35-45)
- Z-Wave door sensors (~$30-40 each)

**Important:** Z-Wave setup for Docker-based Home Assistant requires running a separate Z-Wave JS server. This is different from Home Assistant OS where it's handled by an add-on.

#### Step B.1: Identify Your Z-Wave USB Stick

1. Plug the Z-Wave USB stick into your Raspberry Pi

2. Find the device path:
   ```bash
   # List USB serial devices
   ls -la /dev/ttyUSB* /dev/ttyACM* 2>/dev/null

   # Or check dmesg for the device
   dmesg | grep -i "tty" | tail -10
   ```

   Common paths:
   - `/dev/ttyUSB0` - Most common for FTDI-based sticks
   - `/dev/ttyACM0` - Common for newer sticks (Aeotec Gen5+, Zooz)

3. Get the device ID for a stable path (recommended):
   ```bash
   ls -la /dev/serial/by-id/
   ```

   You'll see something like:
   ```
   usb-Silicon_Labs_Zooz_ZST10_700_0001-if00-port0 -> ../../ttyUSB0
   ```

   Use `/dev/serial/by-id/usb-Silicon_Labs_...` as your device path - this won't change if you plug in other USB devices.

#### Step B.2: Stop Home Assistant and Add USB Device Access

1. Stop the current Home Assistant container:
   ```bash
   docker stop homeassistant
   docker rm homeassistant
   ```

2. Restart Home Assistant with the Z-Wave USB device:
   ```bash
   docker run -d \
     --name homeassistant \
     --privileged \
     --restart=unless-stopped \
     -e TZ=America/Chicago \
     -v ~/homeassistant:/config \
     -v /run/dbus:/run/dbus:ro \
     --device=/dev/ttyUSB0:/dev/ttyUSB0 \
     --network=host \
     ghcr.io/home-assistant/home-assistant:stable
   ```

   **Note:** Replace `/dev/ttyUSB0` with your actual device path from Step B.1.

#### Step B.3: Install Z-Wave JS UI (Recommended Method)

Z-Wave JS UI (formerly zwavejs2mqtt) provides both the Z-Wave JS server and a management interface.

1. Create a directory for Z-Wave JS configuration:
   ```bash
   mkdir -p ~/zwavejs
   ```

2. Start the Z-Wave JS UI container:
   ```bash
   docker run -d \
     --name zwavejs \
     --restart=unless-stopped \
     -p 8091:8091 \
     -p 3000:3000 \
     -v ~/zwavejs:/usr/src/app/store \
     --device=/dev/ttyUSB0:/dev/zwave \
     -e TZ=America/Chicago \
     zwavejs/zwave-js-ui:latest
   ```

   **Note:** Replace `/dev/ttyUSB0` with your actual device path.

3. Wait 1-2 minutes for the container to start, then open the Z-Wave JS UI:
   ```
   http://airquality.local:8091
   ```
   Or use your Pi's IP: `http://192.168.x.x:8091`

4. Configure Z-Wave JS UI:
   - Go to **Settings** → **Z-Wave**
   - Set **Serial Port** to `/dev/zwave`
   - Leave other settings at defaults
   - Click **Save** at the bottom
   - The status should change to "Driver: Ready"

#### Step B.4: Connect Home Assistant to Z-Wave JS

1. In Home Assistant, go to **Settings** → **Devices & Services**

2. Click **+ Add Integration**

3. Search for "**Z-Wave**" - you should see:
   - ✅ **Z-Wave** (this is the correct one - it connects to Z-Wave JS)

   **Note:** Do NOT look for "Z-Wave JS" - the integration is simply called "Z-Wave"

4. When prompted for the server URL, enter:
   ```
   ws://localhost:3000
   ```

   (This connects to the Z-Wave JS UI websocket server you started in Step B.3)

5. Click **Submit** - Home Assistant will connect to your Z-Wave network

6. You should see your Z-Wave USB stick appear as a device (the controller)

#### Step B.5: Pair Z-Wave Door/Window Sensors

1. In Home Assistant, go to **Settings** → **Devices & Services** → **Z-Wave**

2. Click on the Z-Wave integration, then click **Configure**

3. Click **Add Device** (this puts the controller in inclusion mode)

4. Put your door sensor in pairing mode:

   **Aeotec Door/Window Sensor:**
   - Remove the cover
   - Press the button inside once
   - LED will blink rapidly when in pairing mode

   **Ecolink Door/Window Sensor:**
   - Remove the battery
   - Reinsert the battery while holding the button
   - Release button after 1 second

   **Zooz ZSE41 Open/Close Sensor:**
   - Press the button on the sensor 3 times quickly

   **Generic Z-Wave Sensors:**
   - Usually: press the button 3 times quickly, or hold for 3 seconds
   - Check your sensor's manual for specific instructions

5. Home Assistant will discover the sensor (may take 10-30 seconds)

6. Once discovered, give it a meaningful name like "Front Door" or "Kitchen Window"

#### Step B.6: Verify Sensors are Working

1. Go to **Settings** → **Devices & Services** → **Z-Wave**

2. Click on your newly added sensor device

3. You should see entities like:
   - `binary_sensor.front_door_access_control_door_state` - Open/Closed status
   - `sensor.front_door_battery` - Battery level
   - Possibly temperature if your sensor has that feature

4. Test by opening and closing the door/window - the state should update within 1-2 seconds

#### Troubleshooting Z-Wave

**"Z-Wave" integration not found:**
- Make sure you're searching for just "Z-Wave", not "Z-Wave JS"
- Restart Home Assistant if you just added the USB device

**Can't connect to Z-Wave JS server:**
- Check Z-Wave JS UI container is running: `docker ps | grep zwavejs`
- Check logs: `docker logs zwavejs`
- Verify port 3000 is accessible: `curl http://localhost:3000`

**USB device not found in container:**
- Verify device exists: `ls -la /dev/ttyUSB0`
- Check device permissions: `sudo chmod 666 /dev/ttyUSB0`
- Try using the `/dev/serial/by-id/` path instead

**Sensor won't pair:**
- Factory reset the sensor (usually hold button 10+ seconds)
- Move sensor closer to the USB stick during pairing
- Try excluding then re-including (in Z-Wave JS UI: Settings → Actions → Exclude)
- Some sensors need to be awake during pairing - keep pressing button

**Z-Wave JS UI shows "Driver: Not Ready":**
- Wrong serial port - check Settings → Z-Wave → Serial Port
- USB stick not properly passed to container
- Try unplugging and replugging the USB stick, then restart the container

**Entities show "Unavailable":**
- Battery-powered devices sleep to save power
- Wake the device by pressing its button
- Wait for the device to report (can take a few minutes)

### Option C: WiFi Sensors (ESP-based)

**Best for:** DIY enthusiasts

You can build your own with:
- ESP8266 or ESP32 board (~$5)
- Reed switch (~$1)
- ESPHome firmware (integrates directly with Home Assistant)

This is more advanced but very flexible and cheap.

### Option D: GPIO Direct Connection

**Best for:** Hardwired installations, no wireless needed

You can connect simple reed switches directly to Raspberry Pi GPIO pins.

#### Step D.1: Hardware Connection

Connect a reed switch between:
- GPIO pin (e.g., GPIO17 = physical pin 11)
- Ground (e.g., physical pin 9)

#### Step D.2: Install GPIO Integration

Add to `configuration.yaml`:

```yaml
binary_sensor:
  - platform: rpi_gpio
    ports:
      17: Front Door
      27: Back Door
      22: Kitchen Window
    pull_mode: UP
    invert_logic: true
```

Restart Home Assistant.

### Recommended Door Sensor Products

| Product | Protocol | Battery Life | Price | Notes |
|---------|----------|--------------|-------|-------|
| Aqara Door Sensor | Zigbee | 2 years | ~$15 | Compact, reliable |
| Sonoff SNZB-04 | Zigbee | 3 years | ~$10 | Budget option |
| Ecolink Z-Wave | Z-Wave | 3 years | ~$30 | Long range |
| Eve Door | Bluetooth | 1 year | ~$40 | Apple HomeKit |

---

## Part 5: Combined Dashboard

Now let's create a dashboard that shows all your sensors together.

### Step 5.1: Create a New Dashboard

1. In Home Assistant, go to **Settings** → **Dashboards**
2. Click **+ Add Dashboard**
3. Name it "Home Monitor"
4. Enable "Show in sidebar"
5. Click **Create**

### Step 5.2: Add Dashboard Cards

1. Open your new dashboard
2. Click the three dots (⋮) → **Edit Dashboard**
3. Click **Create Section** to add a section for your cards
4. Within that section, click the **+** icon to add cards

**Note:** In Home Assistant, cards are added within sections. If you see options for "add title", "badge", "view", or "create section", you're in the right place. Select **"Create Section"** first, then add cards inside that section.

#### Aranet 4 CO2 Gauge

To add a gauge card:
1. In your section, click the **+** button
2. Select **Gauge** card type
3. Configure the following:
   - Entity: `sensor.aranet4_xxxx_co2`
   - Title: "CO2 Level"
   - Min: 400
   - Max: 2500
   - Severity thresholds:
     - Green: 400
     - Yellow: 800
     - Red: 1000

Or paste this YAML if your dashboard supports YAML editing:

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

#### Environmental Summary (Temperature, Humidity, Pressure)

Add three cards in a row by creating a "Horizontal Stack" section:

1. Click **Create Section** and select **"Horizontal Stack"** layout
2. Add three **Entity** cards inside:
   - Card 1: Entity = `sensor.aranet4_xxxx_temperature`, Title = "Temperature"
   - Card 2: Entity = `sensor.aranet4_xxxx_humidity`, Title = "Humidity"
   - Card 3: Entity = `sensor.aranet4_xxxx_pressure`, Title = "Pressure"

Or use YAML:
```yaml
type: horizontal-stack
cards:
  - type: entity
    entity: sensor.aranet4_xxxx_temperature
    name: Temperature
    icon: mdi:thermometer
  - type: entity
    entity: sensor.aranet4_xxxx_humidity
    name: Humidity
    icon: mdi:water-percent
  - type: entity
    entity: sensor.aranet4_xxxx_pressure
    name: Pressure
    icon: mdi:gauge
```

#### Door Status Card

Add an **Entities** card:

1. Click **Create Section**, then add an **Entities** card type
2. Set Title: "Doors & Windows"
3. Add your door/window sensors:
   - `binary_sensor.front_door` (Front Door)
   - `binary_sensor.back_door` (Back Door)
   - `binary_sensor.kitchen_window` (Kitchen Window)

Or use YAML:
```yaml
type: entities
title: Doors & Windows
entities:
  - entity: binary_sensor.front_door
    name: Front Door
    icon: mdi:door
  - entity: binary_sensor.back_door
    name: Back Door
    icon: mdi:door
  - entity: binary_sensor.kitchen_window
    name: Kitchen Window
    icon: mdi:window-closed-variant
```

#### Ventilation Status (Template Sensor)

Add this to `configuration.yaml` to track if any windows are open:

```yaml
template:
  - binary_sensor:
      - name: "Windows Open"
        state: >
          {{ is_state('binary_sensor.kitchen_window', 'on')
             or is_state('binary_sensor.bedroom_window', 'on') }}
        icon: >
          {% if this.state == 'on' %}
            mdi:window-open-variant
          {% else %}
            mdi:window-closed-variant
          {% endif %}
```

### Step 5.3: Complete Dashboard YAML

Here's a complete dashboard configuration:

```yaml
views:
  - title: Home Monitor
    path: home
    icon: mdi:home
    cards:
      # Header
      - type: markdown
        content: |
          # Home Environment Monitor
          Last updated: {{ now().strftime('%H:%M:%S') }}

      # CO2 Gauge
      - type: gauge
        entity: sensor.aranet4_xxxx_co2
        name: CO2
        min: 400
        max: 2500
        severity:
          green: 400
          yellow: 800
          red: 1000
        needle: true

      # Temperature & Humidity
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.aranet4_xxxx_temperature
            name: Temp
          - type: entity
            entity: sensor.aranet4_xxxx_humidity
            name: Humidity
          - type: entity
            entity: sensor.aranet4_xxxx_battery
            name: Battery

      # Doors & Windows
      - type: entities
        title: Doors & Windows
        show_header_toggle: false
        entities:
          - entity: binary_sensor.front_door
          - entity: binary_sensor.back_door
          - entity: binary_sensor.kitchen_window

      # CO2 History
      - type: history-graph
        title: CO2 History (24 Hours)
        hours_to_show: 24
        entities:
          - entity: sensor.aranet4_xxxx_co2
            name: CO2

      # Temperature History
      - type: history-graph
        title: Temperature & Humidity (24 Hours)
        hours_to_show: 24
        entities:
          - entity: sensor.aranet4_xxxx_temperature
            name: Temp
          - entity: sensor.aranet4_xxxx_humidity
            name: Humidity
```

### Step 5.4: Add Automations

#### Alert: High CO2

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
          message: "CO2 is at {{ states('sensor.aranet4_xxxx_co2') }} ppm. Consider opening a window."
```

#### Alert: Door Left Open

```yaml
  - id: 'door_left_open'
    alias: Door Left Open Alert
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: 'on'
        for:
          minutes: 10
    action:
      - service: persistent_notification.create
        data:
          title: "Door Left Open"
          message: "Front door has been open for 10 minutes."
```

---

## Part 6: Fire Tablet Display

Once your dashboard is working, you can display it on a Fire tablet.

See [FIRE_TABLET_SETUP.md](FIRE_TABLET_SETUP.md) for detailed instructions.

**Quick Summary:**

1. Get a Fire HD 8 or HD 10 tablet
2. Install Fully Kiosk Browser (sideload from fully-kiosk.com)
3. Set the URL to: `http://[PI_IP]:8123/lovelace/home`
4. Enable kiosk mode
5. Mount the tablet

The same Fire tablet can display data from:
- Aranet 4 (Bluetooth)
- Door sensors (Zigbee/Z-Wave)
- Arduino sensors (when you add them later)
- Any other Home Assistant integration

---

## Adding Arduino Sensors Later

When you get your Arduino Nano and sensors, the system is designed to expand:

### Step 1: Set Up Arduino Hardware

Follow [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for hardware assembly.

### Step 2: Install UTSensing Software

```bash
cd ~/Air-quality-sensors
pip3 install -r requirements.txt
cd firmware/airNano
pio run -t upload
```

### Step 3: Start Data Collection

```bash
cd firmware/xu4Mqqt
./runAll.sh
```

### Step 4: Add MQTT to Home Assistant

Follow [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md) to add the Arduino sensors to your existing dashboard.

### Your Dashboard Will Show Everything

```
┌─────────────────────────────────────────────────────────────┐
│                    COMBINED DASHBOARD                        │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │   CO2      │  │   PM2.5    │  │   TVOC     │             │
│  │  (Aranet)  │  │ (Arduino)  │  │ (Arduino)  │             │
│  │   523 ppm  │  │  12 μg/m³  │  │   45 ppb   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │  Doors & Windows                           │             │
│  │  🚪 Front Door: Closed                     │             │
│  │  🚪 Back Door: Open                        │             │
│  │  🪟 Kitchen Window: Open (ventilating!)   │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │  📈 CO2 History (24 hours)                 │             │
│  │  [graph showing CO2 levels over time]      │             │
│  └────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Aranet 4 Not Discovered

1. **Check Bluetooth is working:**
   ```bash
   sudo bluetoothctl
   power on
   scan on
   # Look for "Aranet4" in the list
   quit
   ```

2. **Ensure Docker has Bluetooth access:**
   ```bash
   docker stop homeassistant
   docker rm homeassistant

   # Restart with Bluetooth access
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

3. **Check distance:** Aranet 4 Bluetooth range is ~10 meters. Move closer to Pi.

### Zigbee Devices Not Pairing

1. **Check USB device is detected:**
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   dmesg | tail -20
   ```

2. **Reset the coordinator:**
   - Unplug and replug the USB stick
   - Restart Home Assistant

3. **Factory reset the sensor:**
   - Usually hold reset button 10+ seconds
   - Try pairing again immediately after reset

### Door Sensor Shows Wrong State

1. **Check magnet alignment:**
   - Magnet should be within 1-2cm of sensor
   - Align arrows on both pieces

2. **Invert the logic:**
   - In Home Assistant, edit the entity
   - Toggle "Invert" option if available
   - Or add to configuration:
     ```yaml
     binary_sensor:
       - platform: template
         sensors:
           front_door_fixed:
             value_template: "{{ is_state('binary_sensor.front_door', 'off') }}"
     ```

### Dashboard Not Updating

1. **Check entity names:** Make sure your YAML uses the correct entity IDs
2. **Refresh the page:** Sometimes the browser caches old data
3. **Check Home Assistant logs:** Settings → System → Logs

### Bluetooth Interference

If Bluetooth is unreliable:

1. **Check for interference:**
   - WiFi routers on 2.4GHz
   - USB 3.0 ports (can interfere with Bluetooth)
   - Other Bluetooth devices

2. **Use USB extension:**
   - Place USB Bluetooth adapter away from Pi using a short USB extension cable

3. **Disable WiFi power management:**
   ```bash
   sudo nano /etc/rc.local
   # Add before "exit 0":
   iwconfig wlan0 power off
   ```

---

## Hardware Shopping List

### Minimum Setup (Aranet 4 Only)

| Item | Price | Notes |
|------|-------|-------|
| Raspberry Pi 4 (4GB) | ~$55 | 2GB works too |
| 32GB microSD Card | ~$10 | Class 10 or better |
| USB-C Power Supply | ~$15 | Official Pi supply recommended |
| Aranet 4 | ~$250 | Standalone CO2 monitor |
| **Total** | **~$330** | |

### Adding Door Sensors

| Item | Price | Notes |
|------|-------|-------|
| Sonoff Zigbee 3.0 USB Dongle | ~$25 | Coordinator |
| Aqara Door Sensor (x3) | ~$45 | One per door/window |
| **Additional Total** | **~$70** | |

### Fire Tablet Display

| Item | Price | Notes |
|------|-------|-------|
| Fire HD 8 | ~$50-100 | Wait for sales |
| Tablet Stand or Mount | ~$15 | Optional |
| **Additional Total** | **~$65-115** | |

---

## Next Steps

Once you're comfortable with this setup:

1. **Add more sensors** - Weather stations, motion sensors, etc.
2. **Create automations** - Turn on fans when CO2 is high
3. **Add notifications** - Send alerts to your phone
4. **Get the Arduino kit** - Add PM2.5, VOCs, and more
5. **Explore integrations** - Weather, air quality APIs, smart devices

---

## Related Documentation

- [WS 3000 X5 Setup](WS3000_SETUP.md) - Ambient Weather wireless thermo-hygrometer via USB
- [Door Sensors & Speaker Setup](DOOR_SENSORS_AND_SPEAKER_SETUP.md) - Zooz Z-Wave door sensors and Dome speaker with alarm modes
- [Home Assistant Setup](HOME_ASSISTANT_SETUP.md) - Full MQTT integration for Arduino sensors
- [Fire Tablet Setup](FIRE_TABLET_SETUP.md) - Detailed tablet configuration
- [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md) - Hardware assembly for Arduino kit
- [Sensor Interpretation](SENSOR_INTERPRETATION.md) - Understanding readings
