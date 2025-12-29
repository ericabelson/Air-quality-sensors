# Home Assistant Setup Guide for UTSensing Air Quality Monitor

This guide walks you through setting up the UTSensing air quality sensors in Home Assistant with automatic sensor discovery and a comprehensive dashboard.

## Overview

The UTSensing integration includes:
- **7 Sensors**: SCD30, BME680, SGP30, PMSA003I, SEN0321, MGSV2, MQ136
- **30+ MQTT Sensor Entities** with proper units and device classes
- **Calculated Metrics**: AQI, CO₂ Status, H₂S PPM conversion
- **Multi-View Dashboard**: Overview, History, Details, Settings views

## Prerequisites

- Home Assistant 2023.9+ (for package support)
- MQTT Broker integration configured (Mosquitto or similar)
- Air quality sensor Odroid running and publishing MQTT data
- Network connectivity: `192.168.68.116` (HA) ↔ `192.168.68.109` (Odroid) ↔ `192.168.68.116:1883` (MQTT)

## Step 1: Verify MQTT Broker Connection

Before deploying the sensors, ensure Home Assistant can connect to your MQTT broker:

1. Go to **Settings > Devices & Services > MQTT**
2. Verify the broker is connected (should show "Connected")
3. In Settings > Developer Tools > **MQTT** tab, subscribe to `utsensing/#` and verify you see sensor data being published

**Expected output:**
```
utsensing/SCD30 → {"co2": 450.5, "temperature": 22.3, "humidity": 45.2, ...}
utsensing/BME680 → {"temperature": 22.1, "pressure": 1013.25, "humidity": 45.1, ...}
```

If no data appears:
- Verify Odroid is running: `ssh cerberus@192.168.68.109 "ps aux | grep nanoReader"`
- Check MQTT broker is accessible: `ssh cerberus@192.168.68.109 "mosquitto_sub -h 192.168.68.116 -t 'utsensing/#' -C 1"`
- Ensure TLS is disabled in mintsLatest.py (lines 53-56 should be commented)

## Step 2: Deploy Configuration Files

The configuration files are already present in this repository:

```
homeassistant/
├── configuration.yaml           # Main HA config (updated with packages)
├── packages/
│   └── utsensing_sensors.yaml   # 30+ MQTT sensors + calculated metrics
└── dashboards/
    └── air_quality_dashboard.yaml  # Multi-view dashboard
```

### Option A: Direct File Copy (Recommended for Testing)

If you're running Home Assistant locally or have file access:

```bash
# Copy the packages file to your Home Assistant config directory
cp homeassistant/packages/utsensing_sensors.yaml ~/.homeassistant/packages/

# Restart Home Assistant to load the new package
# Settings > System > Restart Home Assistant
```

### Option B: Manual Configuration Entry (If No File Access)

If you don't have direct file access to your HA config:

1. Go to **Settings > Developer Tools > YAML**
2. Create new file → name it `packages/utsensing_sensors.yaml`
3. Copy the entire content from `homeassistant/packages/utsensing_sensors.yaml`
4. Save and restart Home Assistant

## Step 3: Verify Sensors Are Loading

After restarting Home Assistant:

1. Go to **Settings > Devices & Services**
2. Look for devices under each integration:
   - **MQTT** → Should show 30+ new sensors starting with "Air Quality"
3. Click each sensor to verify it has data

**Key sensors to check:**
- `sensor.air_quality_co2` (should show ~400-500 ppm)
- `sensor.air_quality_pm2_5` (particulate matter)
- `sensor.air_quality_temperature` (room temperature)
- `sensor.air_quality_aqi` (calculated Air Quality Index)

**If sensors show "unavailable":**
- Check MQTT is still publishing: `mosquitto_sub -h 192.168.68.116 -t "utsensing/#" -v`
- Wait 1-2 minutes for first data (sensors need to publish)
- Go to **Settings > System > Restart** and try again

## Step 4: Add Dashboard

### Option A: Raw Configuration Upload (Recommended)

1. Go to **Settings > Dashboards > Create Dashboard**
2. Name it: `Air Quality Monitor`
3. Click the **⋯** (three dots) → **Edit Dashboard**
4. Click **⋯** again → **Raw configuration editor**
5. Copy entire content from `homeassistant/dashboards/air_quality_dashboard.yaml`
6. Paste into the editor
7. Click **Save**

### Option B: Manual Card Addition

Create the dashboard by adding cards manually:

1. **Settings > Dashboards > Create Dashboard** named "Air Quality Monitor"
2. Add the following cards:
   - **Markdown**: Add header with title and timestamp
   - **Gauge**: CO₂ (min: 400, max: 2500)
   - **Gauge**: PM2.5 (min: 0, max: 150)
   - **Gauge**: TVOC (min: 0, max: 2200)
   - **Entity**: Air Quality AQI
   - **Entities**: Environmental Conditions (Temp, Humidity, Pressure, Ozone)
   - **History Graph**: 72-hour trends for CO₂, PM, Temperature, VOC

### Option C: Via Home Assistant Community Store (HACS)

For advanced customization with custom cards:

1. Install HACS if not already installed
2. Download required custom cards:
   - `mushroom-template-card` (for styled AQI display)
   - `layout-card` (for grid layouts on tablet view)
3. Update configuration.yaml:
```yaml
frontend:
  extra_module_url:
    - /local/community/mushroom/mushroom.js
```

## Step 5: Verify Dashboard is Working

1. Open the **Air Quality Monitor** dashboard
2. Check the following:
   - ✅ Gauges show real-time values (CO₂, PM2.5, TVOC)
   - ✅ AQI updates with correct category
   - ✅ History graphs show 72-hour trends
   - ✅ Environmental data displays (temp, humidity, pressure)
   - ✅ Calculations work (CO₂ status, H₂S PPM, AQI category with color)

**Troubleshooting:**
- **Graphs show no data**: Wait 24+ hours for history to accumulate
- **Gauges show 0 or unknown**: Check MQTT is publishing (Step 1)
- **Colors not showing**: Install custom cards or use standard cards (see Option B)

## Step 6: Configure Automation/Alerts (Optional)

The configuration includes threshold input numbers for alerts:

1. Go to **Dashboard > Air Quality > Settings tab**
2. Adjust thresholds:
   - **CO₂ Warning**: 800 ppm (default)
   - **CO₂ Danger**: 1500 ppm (default)
   - **PM2.5 Warning**: 12 μg/m³ (default)
   - **PM2.5 Danger**: 35 μg/m³ (default)

To create automation alerts, add this to `automations.yaml`:

```yaml
- alias: "CO2 High Alert"
  trigger:
    platform: numeric_state
    entity_id: sensor.air_quality_co2
    above: 1500
  action:
    service: notify.mobile_app_your_phone
    data:
      message: "⚠️ CO₂ Level: {{ states('sensor.air_quality_co2') }} ppm"
      title: "Air Quality Alert"
```

## Step 7: 24-Hour Monitoring Setup

For continuous monitoring of sensor reliability:

1. **Monitor JSON Files** on Odroid:
   ```bash
   # SSH into Odroid
   ssh cerberus@192.168.68.109

   # Check sensors are updating
   watch -n 5 "ls -la ~/utData/raw/001e06122a5a/*.json | tail -10"
   ```

2. **Check HA Logs** for errors:
   - Go to **Settings > System > Logs**
   - Search for "mqtt" or "utsensing"
   - Look for connection errors or parsing issues

3. **Verify Database Recording**:
   - Go to **Developer Tools > Statistics**
   - Check "Air Quality" sensors are recording data points

## MQTT Topic Reference

| Topic | Content | Update Frequency |
|-------|---------|------------------|
| `utsensing/SCD30` | CO₂, Temperature, Humidity | 2 Hz |
| `utsensing/BME680` | Pressure, Temperature, Humidity, Gas | 0.5 Hz |
| `utsensing/SGP30` | TVOC, eCO2 | 1 Hz |
| `utsensing/PMSA003I` | PM1/2.5/10, Particle Counts | 1 Hz |
| `utsensing/SEN0321` | Ozone | 0.2 Hz |
| `utsensing/MGSV2` | CO, NO₂, VOC, Ethanol | 0.2 Hz |
| `utsensing/MQ136` | H₂S Raw ADC | 0.2 Hz |

## Sensor Field Names

When accessing data in templates, use these exact field names:

**SCD30**: `co2`, `temperature`, `humidity`
**BME680**: `temperature`, `pressure`, `humidity`, `gas`
**SGP30**: `TVOC`, `eCO2`
**PMSA003I**: `pm1Env`, `pm2p5Env`, `pm10Env`, `binCount0p3um`, `binCount0p5um`, `binCount1um`, `binCount2p5um`
**SEN0321**: `Ozone`
**MGSV2**: `CO`, `NO2`, `C2H5OH`, `VOC`
**MQ136**: `rawH2s`

## Troubleshooting

### Sensors show "unavailable"
1. Verify MQTT broker is connected
2. Check Odroid is publishing: `mosquitto_sub -h 192.168.68.116 -t "utsensing/#" -C 2`
3. Check Home Assistant logs for MQTT errors
4. Restart Home Assistant: Settings > System > Restart

### History graphs show no data
1. Wait 24+ hours for data to accumulate (HA starts recording after first message)
2. Verify sensors are receiving data: Check entity details in Settings > Devices & Services
3. Clear browser cache and refresh dashboard

### Dashboard cards show errors
1. Verify all custom cards are installed (if using mushroom/layout cards)
2. Check for YAML syntax errors in raw editor
3. Use simple entity cards instead of custom cards during troubleshooting

### MQTT connection drops
1. Verify firewall allows access to port 1883
2. Check broker logs: `sudo journalctl -u mosquitto -f`
3. Increase HA MQTT retry settings in configuration.yaml:
```yaml
mqtt:
  broker: 192.168.68.116
  port: 1883
  keepalive: 60
  protocol: 3.1.1
```

## Performance Notes

- **Dashboard Loading**: Initial load takes 2-3 seconds (30+ sensors)
- **History Graphs**: 72-hour view is recommended (less data = faster)
- **Database Size**: Expect ~2-3 MB per day for all sensors (with 10s granularity)
- **CPU Usage**: Minimal (<2%) on Home Assistant with these sensors

## File Structure Summary

```
homeassistant/
├── configuration.yaml                           # Main config (packages enabled)
├── HA_SETUP_GUIDE.md                           # This file
├── packages/
│   └── utsensing_sensors.yaml                  # 30+ MQTT sensors + templates
├── dashboards/
│   ├── air_quality_dashboard.yaml              # Main 6-view dashboard
│   ├── humidity_graph.yaml                     # WS3000 humidity trends
│   └── dew_point_graph.yaml                    # WS3000 dew point trends
└── automations/
    └── air_quality_alerts.yaml                 # Alert automation templates
```

## Next Steps

1. **Complete Step 1-7** above to fully deploy the integration
2. **Monitor** the dashboard for 24 hours to verify data continuity
3. **Fine-tune** thresholds based on your environment
4. **Create** custom automations for alerts (see Optional Alerts section)
5. **Archive** historical data for long-term analysis

## Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review **Settings > System > Logs** in Home Assistant
3. Verify Odroid is still running sensors: `ps aux | grep nanoReader`
4. Check MQTT is accessible: `mosquitto_sub -h 192.168.68.116 -t "utsensing/#"`

---

**Last Updated**: December 29, 2025
**Version**: 1.0
**Sensors**: 7 (SCD30, BME680, SGP30, PMSA003I, SEN0321, MGSV2, MQ136)
**Entities**: 30+ MQTT sensors + calculated metrics
