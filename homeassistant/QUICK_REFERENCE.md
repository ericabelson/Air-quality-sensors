# UTSensing Home Assistant - Quick Reference

## Sensor Entity IDs

### CO₂ & Climate (SCD30)
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_co2` | ppm | 300-5000 | 400-600 |
| `sensor.air_quality_temperature` | °C | -10-50 | 18-25 |
| `sensor.air_quality_humidity_scd30` | % | 0-100 | 30-60 |

### Environmental (BME680)
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_temperature_bme680` | °C | -10-50 | 18-25 |
| `sensor.air_quality_humidity` | % | 0-100 | 30-60 |
| `sensor.air_quality_pressure` | hPa | 850-1050 | 1013 |
| `sensor.air_quality_gas_resistance` | kΩ | 1000-100k | 10k-50k |

### Volatile Organic Compounds (SGP30)
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_tvoc` | ppb | 0-2200 | 0-100 |
| `sensor.air_quality_eco2` | ppm | 400-8192 | 400-600 |

### Particulate Matter (PMSA003I)
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_pm1` | μg/m³ | 0-500 | 0-35 |
| `sensor.air_quality_pm2_5` | μg/m³ | 0-500 | 0-50 |
| `sensor.air_quality_pm10` | μg/m³ | 0-500 | 0-100 |
| `sensor.air_quality_particles_0_3um` | count/dL | 0-65535 | 1000-10000 |
| `sensor.air_quality_particles_0_5um` | count/dL | 0-65535 | 500-5000 |
| `sensor.air_quality_particles_1um` | count/dL | 0-65535 | 100-1000 |
| `sensor.air_quality_particles_2_5um` | count/dL | 0-65535 | 50-500 |

### Toxic Gases (MGSV2)
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_co` | ppm | 0-1000 | <1 |
| `sensor.air_quality_no2` | ppm | 0-10 | <0.1 |
| `sensor.air_quality_ethanol` | ppm | 0-500 | <5 |
| `sensor.air_quality_voc_mgsv2` | ppm | 0-500 | 0-50 |

### Hazardous Gases
| Entity | Unit | Range | Normal |
|--------|------|-------|--------|
| `sensor.air_quality_ozone` | ppb | 0-500 | 0-50 |
| `sensor.air_quality_h2s_raw` | ADC | 0-1023 | 0-200 |
| `sensor.air_quality_h2s` | ppm | 0-100 | <0.01 |

## Calculated Metrics

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.air_quality_aqi` | AQI | Air Quality Index (0-500+) |
| `sensor.air_quality_co2_status` | text | CO₂ status (Excellent/Good/Fair/Poor/Bad) |

## Dashboard Views

### Overview Tab
- Real-time AQI with color coding
- Gauges: CO₂, PM2.5, TVOC
- Environmental conditions (temp, humidity, pressure, ozone)
- Gas levels (CO, NO₂, ethanol, H₂S)
- Particulate matter details

### History Tab (72-hour trends)
- CO₂ levels
- Particulate matter
- Temperature & humidity
- VOC & gases
- Air Quality Index

### Details Tab
- All 30+ sensors in organized sections
- Raw values for each sensor
- Particle count bins

### Settings Tab
- Configurable thresholds for CO₂ and PM2.5
- Reference tables for interpretation
- Quick access to alert settings

### Tablet Tab
- Optimized for Fire Tablet display
- Large AQI display
- Essential gauges (CO₂, PM2.5, TVOC)
- Compact environmental info

## Service Calls (Automations)

### Trigger on High Values

```yaml
# High CO₂ Alert
trigger:
  platform: numeric_state
  entity_id: sensor.air_quality_co2
  above: 1500
```

```yaml
# High PM2.5 Alert
trigger:
  platform: numeric_state
  entity_id: sensor.air_quality_pm2_5
  above: 35
```

```yaml
# High TVOC Alert
trigger:
  platform: numeric_state
  entity_id: sensor.air_quality_tvoc
  above: 660
```

## Template Examples

Get sensor data in automations:

```jinja
# Current values
{{ states('sensor.air_quality_co2') }}
{{ states('sensor.air_quality_pm2_5') | float }}

# With attributes
{{ states('sensor.air_quality_aqi') }}
{{ state_attr('sensor.air_quality_aqi', 'category') }}

# Conditions
{% if states('sensor.air_quality_co2') | float > 1000 %}
  CO₂ is high!
{% endif %}
```

## MQTT Topics

Subscribe to raw MQTT data (for debugging):

```bash
# All sensors
mosquitto_sub -h 192.168.68.116 -t "utsensing/#" -v

# Specific sensor
mosquitto_sub -h 192.168.68.116 -t "utsensing/SCD30"
```

## Troubleshooting Checklist

- [ ] MQTT broker shows "Connected" in Home Assistant
- [ ] `utsensing/#` topics visible in MQTT debug subscribe
- [ ] At least 5 sensors show data (not "unavailable")
- [ ] History tab shows data points (wait 24h for graphs)
- [ ] AQI calculation shows category and color
- [ ] CO₂ and PM2.5 gauges show realistic values
- [ ] Thresholds in Settings tab are visible

## Reference Values

### Air Quality Index (AQI)
| AQI Range | Category |
|-----------|----------|
| 0-50 | Good |
| 51-100 | Moderate |
| 101-150 | Unhealthy for Sensitive Groups |
| 151-200 | Unhealthy |
| 201-300 | Very Unhealthy |
| 301+ | Hazardous |

### CO₂ Levels
| Level | Status | Action |
|-------|--------|--------|
| <600 ppm | Excellent | No action |
| 600-800 ppm | Good | Good ventilation |
| 800-1000 ppm | Fair | Consider ventilation |
| 1000-1500 ppm | Poor | Open windows |
| >1500 ppm | Bad | Ventilate immediately |

### Particulate Matter Health Standards
| Size | Standard | Caution |
|------|----------|--------|
| PM1.0 | <10 μg/m³ | >20 μg/m³ |
| PM2.5 | <12 μg/m³ | >35 μg/m³ |
| PM10 | <20 μg/m³ | >50 μg/m³ |

## System Status

**Odroid IP**: 192.168.68.109
**Home Assistant IP**: 192.168.68.116
**MQTT Broker**: 192.168.68.116:1883
**Data Directory**: /home/cerberus/utData/raw/
**Sensor Count**: 7
**Entity Count**: 30+

---

**Quick Setup Time**: 5 minutes
**Full Monitoring Setup**: 15 minutes
**Data Available After**: 1 minute (first values)
**Graphs Available After**: 24 hours (history)
