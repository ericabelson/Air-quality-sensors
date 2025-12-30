# Home Assistant Air Quality Sensor Gauges Reference

## Overview

This document defines the threshold ranges and color zones for all air quality sensors integrated into Home Assistant. Each sensor has severity thresholds that determine the color coding in gauge displays:

- **Green (#00E400)**: Excellent/Safe
- **Yellow (#FFFF00)**: Fair/Caution
- **Orange (#FF7E00)**: Poor/Alert
- **Red (#FF0000)**: Unhealthy/Danger
- **Purple (#8F3F97)**: Very Unhealthy/Severe
- **Maroon (#7E0023)**: Hazardous/Critical

---

## Sensor Thresholds

### CO₂ (SCD30) - Parts Per Million (ppm)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 600 | Excellent | Green | No action needed |
| 600-800 | Good | Green | No action needed |
| 800-1000 | Fair | Yellow | Consider opening a window |
| 1000-1500 | Moderate | Yellow | Open windows or increase ventilation |
| 1500-2500 | Poor | Orange | Ventilate immediately |
| > 2500 | Unhealthy | Red | Leave area and ventilate |

**Gauge Settings:**
```yaml
min: 400
max: 3000
severity:
  green: 400
  yellow: 1000
  orange: 1500
  red: 2500
```

---

### PM2.5 (PMSA003I) - Micrograms per cubic meter (μg/m³)

Uses Air Quality Index (AQI) for interpretation:

| PM2.5 (μg/m³) | AQI | Level | Color | Action |
|---|---|-------|-------|--------|
| 0-12 | 0-50 | Good | Green | No action needed |
| 12-35 | 51-100 | Moderate | Yellow | Sensitive individuals should limit outdoor exertion |
| 35-55 | 101-150 | Poor | Orange | Sensitive groups should limit outdoor exertion |
| 55-150 | 151-200 | Unhealthy | Red | Everyone should limit outdoor exertion |
| 150-250 | 201-300 | Very Unhealthy | Purple | Avoid outdoor activities |
| > 250 | > 300 | Hazardous | Maroon | Stay indoors with air filtration |

**Gauge Settings:**
```yaml
min: 0
max: 300
severity:
  green: 0
  yellow: 50
  orange: 100
  red: 150
```

---

### PM10 (PMSA003I) - Micrograms per cubic meter (μg/m³)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| 0-54 | Good | Green | No action needed |
| 54-154 | Moderate | Yellow | Monitor levels |
| 154-254 | Poor | Orange | Sensitive groups should limit exposure |
| 254-354 | Unhealthy | Red | Everyone should limit outdoor activity |
| 354-424 | Very Unhealthy | Purple | Avoid outdoor activities |
| > 424 | Hazardous | Maroon | Stay indoors |

**Gauge Settings:**
```yaml
min: 0
max: 500
severity:
  green: 0
  yellow: 54
  orange: 154
  red: 254
```

---

### TVOC (SGP30) - Parts Per Billion (ppb)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 65 | Excellent | Green | No action needed |
| 65-220 | Good | Green | No action needed |
| 220-660 | Fair | Yellow | Identify and reduce VOC sources |
| 660-2200 | Poor | Orange | Ventilate and remove VOC sources |
| > 2200 | Unhealthy | Red | Ventilate immediately |

**Gauge Settings:**
```yaml
min: 0
max: 2500
severity:
  green: 0
  yellow: 220
  orange: 660
  red: 2200
```

---

### Ozone (SEN0321) - Parts Per Billion (ppb)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 50 | Good | Green | No action needed |
| 50-70 | Moderate | Yellow | Sensitive groups should limit outdoor exertion |
| 70-85 | Poor | Orange | Limit prolonged outdoor exertion |
| 85-105 | Unhealthy | Red | Avoid prolonged outdoor exertion |
| 105-200 | Very Unhealthy | Purple | Stay indoors |
| > 200 | Hazardous | Maroon | Emergency conditions - seek shelter |

**Gauge Settings:**
```yaml
min: 0
max: 250
severity:
  green: 0
  yellow: 50
  orange: 70
  red: 85
```

---

### Carbon Monoxide (MGSV2) - Parts Per Million (ppm)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 9 | Good | Green | No action needed |
| 9-35 | Moderate | Yellow | Investigate source, ensure ventilation |
| 35-100 | Unhealthy | Orange | Ventilate and find source |
| 100-400 | Very Unhealthy | Red | Leave area immediately |
| > 400 | Hazardous | Maroon | EVACUATE - Call emergency services |

**Gauge Settings:**
```yaml
min: 0
max: 500
severity:
  green: 0
  yellow: 9
  orange: 35
  red: 100
```

---

### Nitrogen Dioxide (MGSV2) - Parts Per Million (ppm)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 0.053 | Good | Green | No action needed |
| 0.053-0.1 | Moderate | Yellow | Monitor levels |
| 0.1-0.36 | Poor | Orange | Sensitive groups should limit exposure |
| 0.36-0.65 | Unhealthy | Red | Everyone should limit exposure |
| > 0.65 | Very Unhealthy | Purple | Limit outdoor exposure |

**Gauge Settings:**
```yaml
min: 0
max: 1.0
severity:
  green: 0
  yellow: 0.053
  orange: 0.1
  red: 0.36
```

---

### H2S (MQ136) - Raw Sensor Value

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| < 0.5 ppm | Good | Green | No action needed |
| 0.5-15 ppm | Moderate | Yellow | Monitor and investigate source |
| 15-100 ppm | Poor | Orange | Ventilate immediately |
| 100-200 ppm | Unhealthy | Red | Leave area |
| > 200 ppm | Hazardous | Maroon | EVACUATE immediately |

**Note:** MQ136 provides raw sensor value. Conversion to ppm requires calibration.

**Gauge Settings:**
```yaml
min: 0
max: 200
severity:
  green: 0
  yellow: 0.5
  orange: 15
  red: 100
```

---

### Temperature (SCD30 & BME680) - Degrees Celsius (°C)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| 20-24 | Excellent | Green | No action needed |
| 18-26 | Good | Green | No action needed |
| 15-28 | Fair | Yellow | Consider adjusting heating/cooling |
| < 15 or > 28 | Moderate | Orange | Adjust heating/cooling |

**Gauge Settings (Celsius):**
```yaml
min: 5
max: 35
severity:
  green: 15
  yellow: 28
  orange: 35
```

**Gauge Settings (Fahrenheit - if converting):**
```yaml
min: 40
max: 95
severity:
  green: 59
  yellow: 82
  orange: 95
```

---

### Humidity (SCD30 & BME680) - Relative Humidity (%)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| 40-60 | Excellent | Green | No action needed |
| 30-70 | Good | Green | No action needed |
| 20-80 | Fair | Yellow | Consider humidifier or dehumidifier |
| < 20 | Poor | Orange | Use a humidifier |
| > 80 | Poor | Orange | Use a dehumidifier |

**Gauge Settings:**
```yaml
min: 0
max: 100
severity:
  green: 20
  yellow: 80
  orange: 90
```

---

### Pressure (BME680) - Hectopascals (hPa)

Standard atmospheric pressure reference:

| Range | Level | Color | Meaning |
|-------|-------|-------|---------|
| 950-1050 | Normal | Green | Standard atmospheric conditions |
| 900-950 | Low | Yellow | Low pressure, storm possible |
| 1050-1100 | High | Yellow | High pressure, fair weather |
| < 900 | Very Low | Orange | Extreme low pressure |
| > 1100 | Very High | Orange | Extreme high pressure |

**Gauge Settings:**
```yaml
min: 800
max: 1100
severity:
  green: 950
  yellow: 1050
  orange: 1100
```

---

### Gas Resistance (BME680) - Kilohms (kΩ)

Lower values indicate more pollutants. Higher values indicate cleaner air.

| Range | Level | Color | Meaning |
|-------|-------|-------|---------|
| > 50 kΩ | Excellent | Green | Clean air |
| 30-50 kΩ | Good | Green | Good air quality |
| 10-30 kΩ | Fair | Yellow | Fair air quality |
| 5-10 kΩ | Poor | Orange | Degraded air quality |
| < 5 kΩ | Very Poor | Red | Very poor air quality |

**Gauge Settings:**
```yaml
min: 0
max: 100
severity:
  green: 30
  yellow: 50
  orange: 10
  red: 5
```

---

### eCO2 (SGP30) - Parts Per Million (ppm)

| Range | Level | Color | Action |
|-------|-------|-------|--------|
| 400-440 | Good | Green | No action needed |
| 440-600 | Fair | Yellow | Consider ventilation |
| 600-1000 | Poor | Orange | Ventilate |
| > 1000 | Unhealthy | Red | Immediate ventilation needed |

**Gauge Settings:**
```yaml
min: 400
max: 1500
severity:
  green: 400
  yellow: 600
  orange: 1000
```

---

## Implementation Notes

### Creating Gauge Cards in Home Assistant

Use these severity thresholds when creating gauge cards in your dashboard YAML:

```yaml
- type: gauge
  entity: sensor.air_quality_co2
  name: CO₂ Level
  min: 400
  max: 3000
  severity:
    green: 400
    yellow: 1000
    orange: 1500
    red: 2500
  needle: true
  unit: ppm
```

### Color Scale Rules

- **Green**: Safe level - no action needed
- **Yellow**: Caution level - monitor and consider action
- **Orange**: Alert level - take action to reduce exposure
- **Red**: Danger level - limit exposure, ventilate
- **Purple/Maroon**: Hazardous - emergency action needed

### Data Sources

All thresholds are derived from:
- EPA Air Quality Index (AQI) standards
- WHO air quality guidelines
- Sensor manufacturer specifications (Sensirion, Adafruit, DFRobot)
- Industry standards for indoor air quality

---

## References

- [EPA AQI Index](https://www.epa.gov/air-quality/air-quality-index-aqi)
- [WHO Air Quality Guidelines](https://www.who.int/publications/i/item/9789240034228)
- [Sensirion CO2 Reference Values](https://sensirion.com/air-quality-sensing/)
- [DFRobot Ozone Sensor (SEN0321)](https://www.dfrobot.com/product-2014.html)
