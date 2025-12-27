# Home Assistant Dashboard Setup Guide

This guide walks you through setting up a beautiful air quality dashboard in Home Assistant, viewable on any device including Amazon Fire tablets.

**Time Required:** 1-2 hours
**Prerequisites:** Raspberry Pi with UTSensing running (see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md))

**For technical details:** See [Technical Reference Appendix](TECHNICAL_REFERENCE.md) for Home Assistant installation guides, MQTT broker documentation, and official resources

---

## Table of Contents

1. [Overview](#overview)
2. [Install Home Assistant](#install-home-assistant)
3. [Configure MQTT Broker](#configure-mqtt-broker)
4. [Add Sensor Entities](#add-sensor-entities)
5. [Create the Dashboard](#create-the-dashboard)
6. [Set Up 3-Day History Graphs](#set-up-3-day-history-graphs)
7. [Configure Automations and Alerts](#configure-automations-and-alerts)
8. [Access from Fire Tablet](#access-from-fire-tablet)
9. [Multi-Sensor Setup](#multi-sensor-setup)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The dashboard provides:

- **Real-time readings** from all sensors
- **Color-coded status indicators** (green/yellow/orange/red)
- **3-day history graphs** for trend analysis
- **Overall Air Quality Index** calculation
- **Alerts** when values exceed thresholds
- **Mobile-friendly interface** for tablets and phones

### Architecture

```
┌──────────────┐    MQTT     ┌──────────────┐
│  UTSensing   │────────────►│    Mosquitto │
│   (Sensor)   │             │    Broker    │
└──────────────┘             └──────┬───────┘
                                    │
                             ┌──────▼───────┐
                             │Home Assistant│
                             │   (Dashboard)│
                             └──────┬───────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
        ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
        │   Phone   │         │Fire Tablet│         │ Computer  │
        └───────────┘         └───────────┘         └───────────┘
```

---

## Install Home Assistant

### Option A: Home Assistant Container (Recommended)

SSH into your Raspberry Pi and run:

```bash
# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
logout
```

Log back in, then:

```bash
# Create config directory
mkdir -p ~/homeassistant

# Start Home Assistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v ~/homeassistant:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Wait 5-10 minutes for initial startup.

### Option B: Home Assistant OS (Alternative)

For a dedicated Pi, use Home Assistant OS:
1. Download the image from https://www.home-assistant.io/installation/raspberrypi
2. Flash to SD card with Raspberry Pi Imager
3. Boot the Pi

### Access Home Assistant

Open a browser and go to:
```
http://[YOUR_PI_IP]:8123
```

Complete the onboarding wizard:
1. Create your user account
2. Set your home location
3. Finish initial setup

---

## Configure MQTT Broker

### Step 1: Install Mosquitto Broker

```bash
# Install Mosquitto MQTT Broker
sudo apt install -y mosquitto mosquitto-clients

# Enable and start the service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### Step 2: Configure Mosquitto

Create configuration file:

```bash
sudo nano /etc/mosquitto/conf.d/utsensing.conf
```

Add these lines:

```
listener 1883
allow_anonymous true
```

Restart Mosquitto:

```bash
sudo systemctl restart mosquitto
```

### Step 3: Configure UTSensing for MQTT

Edit the UTSensing configuration:

```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
```

Update these settings:

```python
mqttOn = True
mqttBroker = "localhost"  # or your Pi's IP
mqttPort = 1883
```

Restart UTSensing:

```bash
sudo systemctl restart utsensing
```

### Step 4: Add MQTT to Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MQTT"
4. Enter broker details:
   - Broker: `localhost` (or your Pi's IP)
   - Port: `1883`
   - Leave username/password blank

---

## Add Sensor Entities

### Step 1: Copy Configuration Files

Copy the Home Assistant configuration files from this repository:

```bash
# Copy sensor configuration
cp ~/Air-quality-sensors/homeassistant/packages/utsensing_sensors.yaml ~/homeassistant/packages/

# Create packages directory if it doesn't exist
mkdir -p ~/homeassistant/packages
```

### Step 2: Include Packages in Configuration

Edit Home Assistant configuration:

```bash
nano ~/homeassistant/configuration.yaml
```

Add this line at the top:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### Step 3: Sensor Configuration (Alternative - Manual)

If you prefer to add sensors manually, add this to your `configuration.yaml`:

```yaml
mqtt:
  sensor:
    # SCD30 - CO2 Sensor
    - name: "Air Quality CO2"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "ppm"
      icon: mdi:molecule-co2
      device_class: carbon_dioxide

    - name: "Air Quality Temperature"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      icon: mdi:thermometer
      device_class: temperature

    - name: "Air Quality Humidity"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      icon: mdi:water-percent
      device_class: humidity

    # PMSA003I - Particulate Matter
    - name: "Air Quality PM2.5"
      state_topic: "utsensing/PMSA003I"
      value_template: "{{ value_json.pm2p5Env }}"
      unit_of_measurement: "μg/m³"
      icon: mdi:blur

    - name: "Air Quality PM10"
      state_topic: "utsensing/PMSA003I"
      value_template: "{{ value_json.pm10Env }}"
      unit_of_measurement: "μg/m³"
      icon: mdi:blur-linear

    # SGP30 - VOC Sensor
    - name: "Air Quality TVOC"
      state_topic: "utsensing/SGP30"
      value_template: "{{ value_json.TVOC }}"
      unit_of_measurement: "ppb"
      icon: mdi:cloud

    - name: "Air Quality eCO2"
      state_topic: "utsensing/SGP30"
      value_template: "{{ value_json.eCO2 }}"
      unit_of_measurement: "ppm"
      icon: mdi:molecule-co2

    # SEN0321 - Ozone
    - name: "Air Quality Ozone"
      state_topic: "utsensing/SEN0321"
      value_template: "{{ value_json.Ozone }}"
      unit_of_measurement: "ppb"
      icon: mdi:cloud-outline

    # BME680 - Environmental
    - name: "Air Quality Pressure"
      state_topic: "utsensing/BME680"
      value_template: "{{ (value_json.pressure | float * 10) | round(1) }}"
      unit_of_measurement: "hPa"
      icon: mdi:gauge
      device_class: pressure

    - name: "Air Quality Gas Resistance"
      state_topic: "utsensing/BME680"
      value_template: "{{ value_json.gas }}"
      unit_of_measurement: "kΩ"
      icon: mdi:air-filter

    # MGSV2 - Multi-Gas
    - name: "Air Quality CO"
      state_topic: "utsensing/MGSV2"
      value_template: "{{ value_json.CO }}"
      unit_of_measurement: "ppm"
      icon: mdi:molecule

    - name: "Air Quality NO2"
      state_topic: "utsensing/MGSV2"
      value_template: "{{ value_json.NO2 }}"
      unit_of_measurement: "ppm"
      icon: mdi:molecule
```

### Step 4: Restart Home Assistant

```bash
docker restart homeassistant
```

Or go to **Developer Tools** → **YAML** → **Check Configuration** → **Restart**

---

## Create the Dashboard

### Step 1: Create a New Dashboard

1. Go to **Settings** → **Dashboards**
2. Click **+ Add Dashboard**
3. Name it "Air Quality"
4. Enable "Show in sidebar"

### Step 2: Add the Dashboard YAML

**Why use Raw Configuration Editor?** Home Assistant has two ways to edit dashboards:
- **Visual editor** (the UI with "Create Section", "Add Card" buttons) - Good for simple customization
- **Raw configuration editor** (YAML) - Required to paste a complete dashboard layout like the one below

We're using the raw editor because it's faster and ensures the dashboard layout is exactly right.

**Steps:**

1. Open the new dashboard
2. Click the three dots (⋮) → **Edit Dashboard**
3. Click the three dots again → **Raw configuration editor**
4. Replace the content with the dashboard YAML below:

```yaml
views:
  - title: Air Quality Monitor
    path: air-quality
    icon: mdi:air-filter
    badges: []
    cards:
      # Header Card
      - type: markdown
        content: |
          # Air Quality Monitor
          Last updated: {{ states('sensor.air_quality_co2') | default('Loading...') != 'unavailable' and now().strftime('%H:%M:%S') or 'Waiting for data...' }}

      # Main Gauges Row
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.air_quality_co2
            name: CO₂
            min: 400
            max: 2500
            severity:
              green: 400
              yellow: 800
              red: 1000
            needle: true

          - type: gauge
            entity: sensor.air_quality_pm2_5
            name: PM2.5
            min: 0
            max: 150
            severity:
              green: 0
              yellow: 12
              red: 35
            needle: true

          - type: gauge
            entity: sensor.air_quality_tvoc
            name: TVOC
            min: 0
            max: 2200
            severity:
              green: 0
              yellow: 220
              red: 660
            needle: true

      # Environmental Row
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.air_quality_temperature
            name: Temperature
            icon: mdi:thermometer

          - type: entity
            entity: sensor.air_quality_humidity
            name: Humidity
            icon: mdi:water-percent

          - type: entity
            entity: sensor.air_quality_pressure
            name: Pressure
            icon: mdi:gauge

      # Additional Gases Row
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.air_quality_ozone
            name: Ozone
            icon: mdi:cloud-outline

          - type: entity
            entity: sensor.air_quality_co
            name: CO
            icon: mdi:molecule

          - type: entity
            entity: sensor.air_quality_no2
            name: NO₂
            icon: mdi:molecule

      # PM Details
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.air_quality_pm2_5
            name: PM2.5
          - type: entity
            entity: sensor.air_quality_pm10
            name: PM10

      # History Graphs
      - type: history-graph
        title: CO₂ Levels (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_co2
            name: CO₂

      - type: history-graph
        title: Particulate Matter (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_pm2_5
            name: PM2.5
          - entity: sensor.air_quality_pm10
            name: PM10

      - type: history-graph
        title: Temperature & Humidity (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_temperature
            name: Temp
          - entity: sensor.air_quality_humidity
            name: Humidity

      - type: history-graph
        title: VOC & Other Gases (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_tvoc
            name: TVOC
          - entity: sensor.air_quality_ozone
            name: Ozone
```

### Step 3: Save the Dashboard

Click **Save** in the top right corner.

---

## Set Up 3-Day History Graphs

The dashboard above includes 72-hour (3-day) history graphs. To ensure data is retained:

### Configure Recorder

Edit `configuration.yaml`:

```yaml
recorder:
  purge_keep_days: 7
  commit_interval: 30
  include:
    entity_globs:
      - sensor.air_quality_*
```

This keeps 7 days of history for all air quality sensors.

---

## Configure Automations and Alerts

### CO2 Alert Automation

Go to **Settings** → **Automations** → **Create Automation** → **Create new automation**

Or add to `automations.yaml`:

```yaml
- id: 'co2_high_alert'
  alias: CO2 High Alert
  description: 'Alert when CO2 exceeds 1000 ppm'
  trigger:
    - platform: numeric_state
      entity_id: sensor.air_quality_co2
      above: 1000
      for:
        minutes: 5
  action:
    - service: persistent_notification.create
      data:
        title: "High CO2 Detected"
        message: "CO2 level is {{ states('sensor.air_quality_co2') }} ppm. Please ventilate."

- id: 'pm25_high_alert'
  alias: PM2.5 High Alert
  description: 'Alert when PM2.5 exceeds unhealthy levels'
  trigger:
    - platform: numeric_state
      entity_id: sensor.air_quality_pm2_5
      above: 35
      for:
        minutes: 10
  action:
    - service: persistent_notification.create
      data:
        title: "High PM2.5 Detected"
        message: "PM2.5 is {{ states('sensor.air_quality_pm2_5') }} μg/m³. Consider air filtration."
```

---

## Access from Fire Tablet

See [FIRE_TABLET_SETUP.md](FIRE_TABLET_SETUP.md) for detailed instructions on:

1. Installing Fully Kiosk Browser
2. Configuring kiosk mode
3. Setting up the dashboard URL
4. Keeping the tablet always on

Quick summary:
1. Install Fully Kiosk Browser from Amazon Appstore
2. Set start URL to: `http://[PI_IP]:8123/lovelace/air-quality`
3. Enable kiosk mode
4. Configure screen timeout settings

---

## Multi-Sensor Setup

If you have multiple UTSensing units:

### Step 1: Identify Each Sensor

Each sensor has a unique MAC address. Check with:

```bash
# On each sensor Pi
cat /sys/class/net/eth0/address
```

### Step 2: Use MAC Address in Topic

Update each sensor's MQTT topic to include the MAC:

```python
# In mintsDefinitions.py
mqttTopicPrefix = macAddress + "/"
```

### Step 3: Create Sensor Groups

In `configuration.yaml`:

```yaml
mqtt:
  sensor:
    # Living Room Sensor (example MAC: aa:bb:cc:dd:ee:ff)
    - name: "Living Room CO2"
      state_topic: "aa:bb:cc:dd:ee:ff/SCD30"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "ppm"

    # Bedroom Sensor (example MAC: 11:22:33:44:55:66)
    - name: "Bedroom CO2"
      state_topic: "11:22:33:44:55:66/SCD30"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "ppm"
```

### Step 4: Create Multi-Room Dashboard

```yaml
views:
  - title: All Rooms
    cards:
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.living_room_co2
            name: Living Room
          - type: gauge
            entity: sensor.bedroom_co2
            name: Bedroom
          - type: gauge
            entity: sensor.kitchen_co2
            name: Kitchen
```

---

## Troubleshooting

### Sensors Show "Unavailable"

1. Check MQTT connection:
   ```bash
   mosquitto_sub -h localhost -t "utsensing/#" -v
   ```

2. Verify UTSensing is publishing:
   ```bash
   sudo systemctl status utsensing
   ```

3. Check Home Assistant logs:
   **Developer Tools** → **Logs**

### Graphs Not Showing Data

1. Check recorder configuration
2. Wait for data to accumulate (history starts from sensor activation)
3. Verify entity names match exactly

### Dashboard Not Loading

1. Check Home Assistant is running:
   ```bash
   docker logs homeassistant
   ```

2. Verify network connectivity
3. Try accessing from the same device

### MQTT Connection Failed

1. Verify Mosquitto is running:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Test MQTT manually:
   ```bash
   mosquitto_pub -h localhost -t "test" -m "hello"
   mosquitto_sub -h localhost -t "test"
   ```

---

## Next Steps

- [Configure Fire tablet display](FIRE_TABLET_SETUP.md)
- [Understand sensor readings](SENSOR_INTERPRETATION.md)
- Add additional automations for your needs
- Consider adding notifications via mobile app
