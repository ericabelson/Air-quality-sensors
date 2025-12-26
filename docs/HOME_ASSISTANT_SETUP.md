# Home Assistant Dashboard Setup Guide

Configure a real-time air quality dashboard in Home Assistant, viewable on any device including Amazon Fire tablets.

**Time Required:** 45 minutes
**Prerequisites:** Raspberry Pi with UTSensing running (see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md))

---

## Table of Contents

1. [Overview](#overview)
2. [Install Home Assistant](#install-home-assistant)
3. [Configure MQTT](#configure-mqtt)
4. [Add Sensor Entities](#add-sensor-entities)
5. [Create the Dashboard](#create-the-dashboard)
6. [Configure History Graphs](#configure-history-graphs)
7. [Set Up Alerts](#set-up-alerts)
8. [Access from Fire Tablet](#access-from-fire-tablet)
9. [Multi-Sensor Setup](#multi-sensor-setup)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The dashboard provides:

- **Real-time readings** from all sensors
- **Color-coded status indicators** (green/yellow/red)
- **3-day history graphs** for trend analysis
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

Wait 5-10 minutes, then access: `http://[YOUR_PI_IP]:8123`

---

## Configure MQTT

Follow the [MQTT Setup](setup/MQTT_SETUP.md) module to install Mosquitto and connect it to Home Assistant.

**Quick version:**

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

**Enable MQTT in UTSensing:**

```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
# Set: mqttOn = True, mqttBroker = "localhost"

sudo systemctl restart utsensing
```

**Add MQTT to Home Assistant:**

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search "MQTT"
3. Broker: `localhost`, Port: `1883`

---

## Add Sensor Entities

### Option A: Use Package Files (Recommended)

Copy the pre-configured sensor files:

```bash
mkdir -p ~/homeassistant/packages
cp ~/Air-quality-sensors/homeassistant/packages/utsensing_sensors.yaml ~/homeassistant/packages/
```

Edit Home Assistant configuration:

```bash
nano ~/homeassistant/configuration.yaml
```

Add at the top:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Restart Home Assistant:

```bash
docker restart homeassistant
```

### Option B: Manual Configuration

Add sensors directly to `configuration.yaml`:

```yaml
mqtt:
  sensor:
    # SCD30 - CO2 Sensor
    - name: "Air Quality CO2"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "ppm"
      device_class: carbon_dioxide

    - name: "Air Quality Temperature"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "Air Quality Humidity"
      state_topic: "utsensing/SCD30"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # PMSA003I - Particulate Matter
    - name: "Air Quality PM2.5"
      state_topic: "utsensing/PMSA003I"
      value_template: "{{ value_json.pm2p5Env }}"
      unit_of_measurement: "μg/m³"

    - name: "Air Quality PM10"
      state_topic: "utsensing/PMSA003I"
      value_template: "{{ value_json.pm10Env }}"
      unit_of_measurement: "μg/m³"

    # SGP30 - VOC Sensor
    - name: "Air Quality TVOC"
      state_topic: "utsensing/SGP30"
      value_template: "{{ value_json.TVOC }}"
      unit_of_measurement: "ppb"

    # SEN0321 - Ozone
    - name: "Air Quality Ozone"
      state_topic: "utsensing/SEN0321"
      value_template: "{{ value_json.Ozone }}"
      unit_of_measurement: "ppb"

    # BME680 - Environmental
    - name: "Air Quality Pressure"
      state_topic: "utsensing/BME680"
      value_template: "{{ (value_json.pressure | float * 10) | round(1) }}"
      unit_of_measurement: "hPa"
      device_class: pressure

    # MGSV2 - Multi-Gas
    - name: "Air Quality CO"
      state_topic: "utsensing/MGSV2"
      value_template: "{{ value_json.CO }}"
      unit_of_measurement: "ppm"

    - name: "Air Quality NO2"
      state_topic: "utsensing/MGSV2"
      value_template: "{{ value_json.NO2 }}"
      unit_of_measurement: "ppm"
```

Restart Home Assistant after adding.

---

## Create the Dashboard

### Step 1: Create Dashboard

1. **Settings** → **Dashboards** → **+ Add Dashboard**
2. Name: "Air Quality"
3. Enable "Show in sidebar"

### Step 2: Add Dashboard Configuration

1. Open the dashboard
2. Click ⋮ → **Edit Dashboard** → ⋮ → **Raw configuration editor**
3. Replace with:

```yaml
views:
  - title: Air Quality Monitor
    path: air-quality
    icon: mdi:air-filter
    cards:
      # Header
      - type: markdown
        content: |
          # Air Quality Monitor
          Last updated: {{ now().strftime('%H:%M:%S') }}

      # Main Gauges
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

      # Environmental
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.air_quality_temperature
            name: Temperature
          - type: entity
            entity: sensor.air_quality_humidity
            name: Humidity
          - type: entity
            entity: sensor.air_quality_pressure
            name: Pressure

      # Other Gases
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.air_quality_ozone
            name: Ozone
          - type: entity
            entity: sensor.air_quality_co
            name: CO
          - type: entity
            entity: sensor.air_quality_no2
            name: NO₂

      # History
      - type: history-graph
        title: CO₂ (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_co2

      - type: history-graph
        title: PM2.5 & PM10 (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_pm2_5
          - entity: sensor.air_quality_pm10

      - type: history-graph
        title: Temperature & Humidity (3 Days)
        hours_to_show: 72
        entities:
          - entity: sensor.air_quality_temperature
          - entity: sensor.air_quality_humidity
```

Click **Save**.

---

## Configure History Graphs

To retain data for 3-day graphs, edit `configuration.yaml`:

```yaml
recorder:
  purge_keep_days: 7
  commit_interval: 30
  include:
    entity_globs:
      - sensor.air_quality_*
```

Restart Home Assistant.

---

## Set Up Alerts

Add to `automations.yaml` or create via UI:

```yaml
automation:
  - id: 'co2_high_alert'
    alias: High CO2 Alert
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
          message: "CO2 is {{ states('sensor.air_quality_co2') }} ppm. Please ventilate."

  - id: 'pm25_high_alert'
    alias: High PM2.5 Alert
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
          message: "PM2.5 is {{ states('sensor.air_quality_pm2_5') }} μg/m³."
```

---

## Access from Fire Tablet

See [Fire Tablet Setup](FIRE_TABLET_SETUP.md) for detailed instructions.

**Quick summary:**
1. Get a Fire HD 8 or HD 10
2. Sideload Fully Kiosk Browser from [fully-kiosk.com](https://www.fully-kiosk.com)
3. Set URL to: `http://[PI_IP]:8123/lovelace/air-quality`
4. Enable kiosk mode

---

## Multi-Sensor Setup

For multiple UTSensing units in different rooms:

### Step 1: Use MAC Address in Topic

On each sensor Pi, update `mintsDefinitions.py`:

```python
mqttTopicPrefix = macAddress + "/"
```

### Step 2: Create Sensor Groups

```yaml
mqtt:
  sensor:
    - name: "Living Room CO2"
      state_topic: "aa:bb:cc:dd:ee:ff/SCD30"
      value_template: "{{ value_json.co2 }}"

    - name: "Bedroom CO2"
      state_topic: "11:22:33:44:55:66/SCD30"
      value_template: "{{ value_json.co2 }}"
```

### Step 3: Multi-Room Dashboard

```yaml
- type: horizontal-stack
  cards:
    - type: gauge
      entity: sensor.living_room_co2
      name: Living Room
    - type: gauge
      entity: sensor.bedroom_co2
      name: Bedroom
```

---

## Troubleshooting

### Sensors Show "Unavailable"

1. Check MQTT is receiving data:
   ```bash
   mosquitto_sub -h localhost -t "utsensing/#" -v
   ```

2. Verify UTSensing service:
   ```bash
   sudo systemctl status utsensing
   ```

3. Check Home Assistant logs: **Developer Tools** → **Logs**

### Graphs Not Showing Data

1. Verify recorder configuration
2. Wait for data to accumulate (history starts fresh)
3. Check entity names match exactly

### Dashboard Not Loading

```bash
docker logs homeassistant
```

### MQTT Connection Failed

```bash
sudo systemctl status mosquitto
mosquitto_pub -h localhost -t "test" -m "hello"
```

---

## Next Steps

- [Fire Tablet Setup](FIRE_TABLET_SETUP.md) - Dedicated display
- [Sensor Interpretation](SENSOR_INTERPRETATION.md) - Understanding readings
- [Security Guide](SECURITY.md) - Hardening your installation
- [Remote Access](REMOTE_ACCESS.md) - Access from outside your network
