# WS3000 Weather Station Dashboard Setup

This guide explains how to set up temperature, humidity, and dew point graphs for the Ambient Weather WS3000 wireless sensors in Home Assistant.

**Time Required:** 30-60 minutes
**Prerequisites:**
- Home Assistant installed (see [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md))
- WS3000 sensors configured and publishing to MQTT (see [WS3000_SETUP.md](WS3000_SETUP.md))

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration File Setup](#configuration-file-setup)
3. [Understanding the Sensors](#understanding-the-sensors)
4. [Creating the Dashboard Graphs](#creating-the-dashboard-graphs)
5. [Color Coding Explained](#color-coding-explained)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The WS3000 weather station system can track up to 8 wireless sensors. This setup provides:

- **Temperature graphs** with color-coded readings
- **Humidity graphs** with color-coded readings
- **Calculated dew point graphs** with color-coded readings
- **72-hour (3-day) history** for trend analysis
- **Automatic color coding** based on comfort levels

### What is Dew Point?

Dew point is the temperature at which water vapor in the air begins to condense. It's a better indicator of human comfort than humidity alone:

| Dew Point (°F) | Comfort Level | Description |
|----------------|---------------|-------------|
| < 30 | Very Dry | Can cause dry skin/static |
| 30-40 | Dry | Comfortable for most |
| 40-50 | Comfortable | Ideal indoor range |
| 50-60 | Slightly Humid | Still comfortable |
| 60-65 | Humid | Feels sticky outdoors |
| 65-70 | Very Humid | Uncomfortable for most |
| > 70 | Oppressive | Very uncomfortable |

The dew point is calculated automatically from temperature and humidity using the Magnus formula.

---

## Configuration File Setup

### Step 1: Copy Configuration to Home Assistant

The `configuration.yaml` file in this repository (`homeassistant/configuration.yaml`) includes:

1. **MQTT sensors** - Raw temperature and humidity from each WS3000 sensor
2. **Temperature colored sensors** - Template sensors with color attributes
3. **Humidity colored sensors** - Template sensors with color attributes
4. **Dew point sensors** - Calculated and color-coded template sensors

Copy or merge this file into your Home Assistant configuration directory:

```bash
# If you're using Docker Home Assistant
cp ~/Air-quality-sensors/homeassistant/configuration.yaml ~/homeassistant/configuration.yaml

# Or for Home Assistant OS
# Use the File Editor add-on or Samba share to copy the file
```

### Step 2: Verify MQTT Topics

The configuration assumes your WS3000 sensors publish to topics:
- `ws3000/sensor_1`
- `ws3000/sensor_2`
- `ws3000/sensor_3`
- `ws3000/sensor_4`
- `ws3000/sensor_5`
- `ws3000/sensor_6`

Each topic should publish JSON data with `temperature` and `humidity` fields:
```json
{
  "temperature": 72.5,
  "humidity": 45.2
}
```

### Step 3: Restart Home Assistant

After copying the configuration file:

```bash
# For Docker installation
docker restart homeassistant

# Or use the UI
# Go to Developer Tools → YAML → Check Configuration → Restart
```

---

## Understanding the Sensors

The configuration creates three types of sensors for each WS3000 unit:

### 1. MQTT Sensors (Raw Data)
These receive data directly from the MQTT broker:
- `sensor.ws3000_sensor_1_temperature` - Raw temperature in °F
- `sensor.ws3000_sensor_1_humidity` - Raw humidity in %

### 2. Colored Template Sensors
These add color attributes for visual display:
- `sensor.ws3000_sensor_1_temperature_colored`
- `sensor.ws3000_sensor_1_humidity_colored`

### 3. Calculated Dew Point Sensors
These calculate dew point from temperature and humidity:
- `sensor.ws3000_sensor_1_dew_point`

**Example sensor mapping:**
- Sensor 1: Outside
- Sensor 2: Under House
- Sensor 3: Attic
- Sensor 4: Inside

(Customize the names in your dashboard to match your sensor locations)

---

## Creating the Dashboard Graphs

### Option 1: Use the Pre-Made Graph Files

The repository includes ready-to-use graph configurations:

1. **Temperature Graph**: `homeassistant/dashboards/temperature_graph.yaml`
2. **Humidity Graph**: `homeassistant/dashboards/humidity_graph.yaml`
3. **Dew Point Graph**: `homeassistant/dashboards/dew_point_graph.yaml`

**To add these to your dashboard:**

1. Open Home Assistant
2. Go to your dashboard
3. Click the three dots (⋮) → **Edit Dashboard**
4. Click **+ Add Card**
5. Click **Manual** at the bottom
6. Copy and paste the contents of one of the YAML files
7. Click **Save**

### Temperature Graph YAML

```yaml
type: history-graph
title: Temp
hours_to_show: 72
refresh_interval: 60
entities:
  - entity: sensor.ws3000_sensor_1_temperature_colored
    name: Outside
  - entity: sensor.ws3000_sensor_4_temperature_colored
    name: Inside
  - entity: sensor.ws3000_sensor_2_temperature_colored
    name: UnderHouse
  - entity: sensor.ws3000_sensor_3_temperature_colored
    name: Attic
```

### Humidity Graph YAML

```yaml
type: history-graph
title: Humidity
hours_to_show: 72
refresh_interval: 60
entities:
  - entity: sensor.ws3000_sensor_1_humidity_colored
    name: Outside
  - entity: sensor.ws3000_sensor_4_humidity_colored
    name: Inside
  - entity: sensor.ws3000_sensor_2_humidity_colored
    name: UnderHouse
  - entity: sensor.ws3000_sensor_3_humidity_colored
    name: Attic
```

### Dew Point Graph YAML

```yaml
type: history-graph
title: Dew Point
hours_to_show: 72
refresh_interval: 60
entities:
  - entity: sensor.ws3000_sensor_1_dew_point
    name: Outside
  - entity: sensor.ws3000_sensor_4_dew_point
    name: Inside
  - entity: sensor.ws3000_sensor_2_dew_point
    name: UnderHouse
  - entity: sensor.ws3000_sensor_3_dew_point
    name: Attic
```

### Option 2: Create a Combined Weather Dashboard

Create a single view with all three graphs:

```yaml
views:
  - title: Weather Monitor
    path: weather
    icon: mdi:weather-partly-cloudy
    cards:
      # Header
      - type: markdown
        content: |
          # WS3000 Weather Station
          Real-time monitoring of 4 sensor locations

      # Current Conditions
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.ws3000_sensor_1_temperature_colored
            name: Outside Temp
          - type: entity
            entity: sensor.ws3000_sensor_1_humidity_colored
            name: Outside Humidity
          - type: entity
            entity: sensor.ws3000_sensor_1_dew_point
            name: Outside Dew Point

      # Temperature Graph
      - type: history-graph
        title: Temperature (72 Hours)
        hours_to_show: 72
        refresh_interval: 60
        entities:
          - entity: sensor.ws3000_sensor_1_temperature_colored
            name: Outside
          - entity: sensor.ws3000_sensor_4_temperature_colored
            name: Inside
          - entity: sensor.ws3000_sensor_2_temperature_colored
            name: UnderHouse
          - entity: sensor.ws3000_sensor_3_temperature_colored
            name: Attic

      # Humidity Graph
      - type: history-graph
        title: Humidity (72 Hours)
        hours_to_show: 72
        refresh_interval: 60
        entities:
          - entity: sensor.ws3000_sensor_1_humidity_colored
            name: Outside
          - entity: sensor.ws3000_sensor_4_humidity_colored
            name: Inside
          - entity: sensor.ws3000_sensor_2_humidity_colored
            name: UnderHouse
          - entity: sensor.ws3000_sensor_3_humidity_colored
            name: Attic

      # Dew Point Graph
      - type: history-graph
        title: Dew Point (72 Hours)
        hours_to_show: 72
        refresh_interval: 60
        entities:
          - entity: sensor.ws3000_sensor_1_dew_point
            name: Outside
          - entity: sensor.ws3000_sensor_4_dew_point
            name: Inside
          - entity: sensor.ws3000_sensor_2_dew_point
            name: UnderHouse
          - entity: sensor.ws3000_sensor_3_dew_point
            name: Attic
```

---

## Color Coding Explained

The color attributes make graphs visually intuitive. Here are the color schemes:

### Temperature Colors

| Temperature (°F) | Color | Hex Code | Meaning |
|------------------|-------|----------|---------|
| < 50 | Dark Blue | #0D47A1 | Very Cold |
| 50-60 | Blue | #1976D2 | Cold |
| 60-65 | Light Blue | #42A5F5 | Cool |
| 65-75 | Yellow | #FFEB3B | Comfortable |
| 75-85 | Orange | #FF9800 | Warm |
| > 85 | Red | #D32F2F | Hot |

### Humidity Colors

| Humidity (%) | Color | Hex Code | Meaning |
|--------------|-------|----------|---------|
| < 30 | Red | #D32F2F | Too Dry |
| 30-40 | Orange | #FF9800 | Dry |
| 40-50 | Yellow | #FFEB3B | Slightly Dry |
| 50-60 | Green | #8BC34A | Ideal |
| 60-70 | Light Blue | #42A5F5 | Humid |
| > 70 | Blue | #1976D2 | Very Humid |

### Dew Point Colors

| Dew Point (°F) | Color | Hex Code | Comfort Level |
|----------------|-------|----------|---------------|
| < 30 | Dark Blue | #0D47A1 | Very Dry |
| 30-40 | Blue | #1976D2 | Dry |
| 40-50 | Light Blue | #42A5F5 | Comfortable |
| 50-60 | Green | #8BC34A | Pleasant |
| 60-65 | Yellow | #FFEB3B | Slightly Humid |
| 65-70 | Orange | #FF9800 | Humid |
| > 70 | Red | #D32F2F | Oppressive |

---

## Troubleshooting

### Sensors Show "Unavailable"

**Check MQTT connection:**
```bash
# Subscribe to WS3000 topics
mosquitto_sub -h localhost -t "ws3000/#" -v
```

You should see data flowing like:
```
ws3000/sensor_1 {"temperature":72.5,"humidity":45.2}
ws3000/sensor_2 {"temperature":68.3,"humidity":52.1}
```

**If no data appears:**
1. Verify the WS3000 data collector is running
2. Check MQTT broker is running: `sudo systemctl status mosquitto`
3. Verify sensor topic names match configuration

### Dew Point Shows "Unknown" or Error

The dew point calculation requires both temperature and humidity. If one is unavailable, dew point will fail.

**Check both sensors are working:**
```bash
# In Home Assistant Developer Tools → States
# Look for:
sensor.ws3000_sensor_1_temperature
sensor.ws3000_sensor_1_humidity
```

Both should have valid numeric values.

### Graphs Not Showing History

**Enable recorder for WS3000 sensors:**

Add to `configuration.yaml`:
```yaml
recorder:
  purge_keep_days: 7
  include:
    entity_globs:
      - sensor.ws3000_*
```

Restart Home Assistant after adding this.

### Colors Not Displaying

The history-graph card uses the `color` attribute automatically. If colors aren't showing:

1. Verify you're using the `_colored` or `_dew_point` sensors (not the raw MQTT sensors)
2. Check Developer Tools → States to verify the color attribute exists
3. Try clearing your browser cache

### Wrong Sensor Names

To customize sensor names, edit the dashboard YAML:

```yaml
entities:
  - entity: sensor.ws3000_sensor_1_temperature_colored
    name: "Front Yard"  # Change this to your location
  - entity: sensor.ws3000_sensor_2_temperature_colored
    name: "Back Yard"   # Change this to your location
```

---

## Next Steps

- **Add alerts**: Set up automations for temperature/humidity thresholds
- **Mobile app**: View your dashboard on your phone with the Home Assistant Companion app
- **Expand monitoring**: Add more WS3000 sensors (system supports up to 8)
- **Historical analysis**: Export data to CSV for long-term tracking

**Related Documentation:**
- [WS3000 Hardware Setup](WS3000_SETUP.md)
- [Home Assistant Setup](HOME_ASSISTANT_SETUP.md)
- [Fire Tablet Display](FIRE_TABLET_SETUP.md)
- [Remote Access Setup](REMOTE_ACCESS.md)
