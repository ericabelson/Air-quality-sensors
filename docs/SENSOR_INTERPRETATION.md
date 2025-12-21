# Sensor Data Interpretation Guide

This document explains how to interpret raw sensor data and convert it into meaningful, human-readable values. Each sensor is covered with its formulas, calibration notes, and health reference tables.

---

## Table of Contents

1. [Understanding Air Quality](#understanding-air-quality)
2. [SCD30 - CO2, Temperature, Humidity](#scd30---co2-temperature-humidity)
3. [BME680 - Environmental Sensor](#bme680---environmental-sensor)
4. [SGP30 - VOC and eCO2](#sgp30---voc-and-eco2)
5. [PMSA003I - Particulate Matter](#pmsa003i---particulate-matter)
6. [SEN0321 - Ozone](#sen0321---ozone)
7. [MGSV2 - Multi-Gas Sensor](#mgsv2---multi-gas-sensor)
8. [MQ136 - Hydrogen Sulfide](#mq136---hydrogen-sulfide)
9. [Air Quality Index Calculations](#air-quality-index-calculations)
10. [Sensor Accuracy and Limitations](#sensor-accuracy-and-limitations)

---

## Understanding Air Quality

### What Makes Air "Good" or "Bad"?

Air quality is determined by the concentration of various pollutants:

| Pollutant | Sources | Health Effects |
|-----------|---------|----------------|
| **PM2.5** | Smoke, exhaust, dust | Respiratory issues, heart disease |
| **CO2** | Breathing, combustion | Drowsiness, headaches at high levels |
| **VOCs** | Paints, cleaning products | Eye/throat irritation, long-term effects |
| **CO** | Incomplete combustion | Poisoning, oxygen deprivation |
| **O3** | Sunlight + pollution | Lung damage, asthma triggers |
| **NO2** | Vehicle exhaust | Respiratory inflammation |
| **H2S** | Sewage, decay | Toxic at high levels |

---

## SCD30 - CO2, Temperature, Humidity

### What It Measures

The SCD30 uses **Non-Dispersive Infrared (NDIR)** technology to measure CO2 directly. This is highly accurate and doesn't drift like chemical sensors.

### Raw Data Format

| Field | Type | Unit | Range |
|-------|------|------|-------|
| co2 | Integer | ppm | 400-10000 |
| temperature | Float | °C | -40 to 70 |
| humidity | Float | %RH | 0-100 |

### Interpretation

The SCD30 outputs already-calibrated values. No conversion needed!

**CO2 Level Interpretation:**

```
400-600 ppm   → EXCELLENT  (Outdoor air level)
600-800 ppm   → GOOD       (Well-ventilated indoor space)
800-1000 ppm  → FAIR       (Slightly stuffy, consider ventilation)
1000-1500 ppm → POOR       (Stuffy, ventilation recommended)
1500-2500 ppm → BAD        (Drowsiness, headaches likely)
2500+ ppm     → DANGEROUS  (Cognitive impairment, immediate ventilation needed)
```

**Why 400 ppm minimum?**
Outdoor atmospheric CO2 is approximately 410-420 ppm (as of 2024). Levels below this indoors are physically impossible without active CO2 removal.

### Temperature Compensation

The SCD30 has built-in temperature compensation. However, it can read 2-3°C higher than ambient due to self-heating. For accurate temperature, use the BME680.

### Code Example

```python
def interpret_co2(co2_ppm):
    """Convert CO2 reading to human-readable status."""
    if co2_ppm < 600:
        return {"level": "Excellent", "color": "green", "action": "None needed"}
    elif co2_ppm < 800:
        return {"level": "Good", "color": "green", "action": "None needed"}
    elif co2_ppm < 1000:
        return {"level": "Fair", "color": "yellow", "action": "Consider ventilation"}
    elif co2_ppm < 1500:
        return {"level": "Poor", "color": "orange", "action": "Open windows"}
    elif co2_ppm < 2500:
        return {"level": "Bad", "color": "red", "action": "Ventilate immediately"}
    else:
        return {"level": "Dangerous", "color": "purple", "action": "Leave area"}
```

---

## BME680 - Environmental Sensor

### What It Measures

The BME680 is a 4-in-1 sensor measuring:
- Temperature
- Barometric Pressure
- Relative Humidity
- Gas Resistance (VOC indicator)

### Raw Data Format

| Field | Type | Unit | Raw Range |
|-------|------|------|-----------|
| temperature | Float | °C | -40 to 85 |
| pressure | Float | kPa | 30 to 110 |
| humidity | Float | %RH | 0-100 |
| gas | Float | kΩ | 1-500 |

### Conversion Formulas

**Pressure:** Already in kPa. For hPa (hectopascals/millibars):
```
pressure_hPa = pressure_kPa × 10
```

**Altitude Estimation (from pressure):**
```
altitude_m = 44330 × (1 - (pressure_kPa / 101.325)^0.1903)
```

### Gas Resistance Interpretation

The gas resistance value is inversely related to VOC concentration. Higher resistance = cleaner air.

**However**, this is a relative measurement. The absolute value depends on:
- Temperature
- Humidity
- Sensor age
- Baseline conditions

**Gas Resistance Guidelines:**

```
> 300 kΩ  → EXCELLENT (Very clean air)
200-300 kΩ → GOOD     (Clean indoor air)
100-200 kΩ → FAIR     (Some VOCs present)
50-100 kΩ  → POOR     (Moderate VOC levels)
< 50 kΩ   → BAD      (High VOC levels)
```

### Calculating Indoor Air Quality (IAQ) Index

Bosch provides a proprietary algorithm, but a simplified calculation:

```python
def calculate_iaq(gas_resistance, humidity, temperature):
    """
    Simplified IAQ calculation.
    Returns value 0-500 where lower is better.
    """
    # Humidity contributes to perceived air quality
    # Optimal humidity is 40-60%
    humidity_score = 0
    if humidity < 40:
        humidity_score = (40 - humidity) * 1.5
    elif humidity > 60:
        humidity_score = (humidity - 60) * 1.5

    # Gas resistance contribution (log scale)
    # Baseline of 250 kΩ for clean air
    import math
    if gas_resistance > 0:
        gas_score = max(0, 250 - (math.log10(gas_resistance) * 100))
    else:
        gas_score = 500

    # Combined score
    iaq = gas_score + humidity_score
    return min(500, max(0, iaq))
```

---

## SGP30 - VOC and eCO2

### What It Measures

The SGP30 uses metal oxide semiconductor (MOX) technology to detect:
- **TVOC**: Total Volatile Organic Compounds
- **eCO2**: Equivalent CO2 (calculated from TVOC)
- **Raw H2**: Hydrogen signal (used internally)
- **Raw Ethanol**: Ethanol signal (used internally)

### Raw Data Format

| Field | Type | Unit | Range |
|-------|------|------|-------|
| TVOC | Integer | ppb | 0-60000 |
| eCO2 | Integer | ppm | 400-60000 |
| rawH2 | Integer | Raw ADC | 0-65535 |
| rawEthanol | Integer | Raw ADC | 0-65535 |

### Understanding eCO2 vs Real CO2

**Important:** eCO2 is NOT real CO2!

eCO2 is calculated from VOC levels using a correlation. It assumes that CO2 and VOC levels rise together (which happens when humans are the source).

```
eCO2 = f(TVOC)
```

For actual CO2 measurement, use the SCD30.

### TVOC Interpretation

```
0-65 ppb      → EXCELLENT (Pristine air)
65-220 ppb    → GOOD     (Normal indoor air)
220-660 ppb   → FAIR     (Elevated, identify sources)
660-2200 ppb  → POOR     (Reduce exposure time)
2200+ ppb     → BAD      (Ventilate immediately)
```

### Baseline Calibration

The SGP30 requires baseline calibration for accurate readings:

1. Run in clean air for 12 hours
2. Save the baseline values
3. Restore baseline on startup

```python
def get_baseline(sgp30):
    """Get baseline values after 12h warmup."""
    eco2_base, tvoc_base = sgp30.get_iaq_baseline()
    return {"eco2_base": eco2_base, "tvoc_base": tvoc_base}

def set_baseline(sgp30, eco2_base, tvoc_base):
    """Restore baseline values on startup."""
    sgp30.set_iaq_baseline(eco2_base, tvoc_base)
```

---

## PMSA003I - Particulate Matter

### What It Measures

The PMSA003I uses laser scattering to count particles by size and calculate mass concentration.

### Raw Data Format

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| pm1Standard | Integer | μg/m³ | PM1.0 (standard conditions) |
| pm2p5Standard | Integer | μg/m³ | PM2.5 (standard conditions) |
| pm10_standard | Integer | μg/m³ | PM10 (standard conditions) |
| pm1Env | Integer | μg/m³ | PM1.0 (environmental) |
| pm2p5Env | Integer | μg/m³ | PM2.5 (environmental) |
| pm10Env | Integer | μg/m³ | PM10 (environmental) |
| binCount0p3um | Integer | count/dL | Particles ≥0.3μm |
| binCount0p5um | Integer | count/dL | Particles ≥0.5μm |
| binCount1um | Integer | count/dL | Particles ≥1.0μm |
| binCount2p5um | Integer | count/dL | Particles ≥2.5μm |
| binCount5um | Integer | count/dL | Particles ≥5.0μm |
| binCount10um | Integer | count/dL | Particles ≥10μm |

### Standard vs Environmental Values

- **Standard**: Corrected to standard temperature (20°C) and pressure (1013 hPa)
- **Environmental**: Actual atmospheric conditions

For health assessments, **use environmental values** (pmXEnv).

### PM2.5 Health Guidelines (WHO 2021)

```
0-5 μg/m³     → EXCELLENT (WHO 24h guideline)
5-15 μg/m³    → GOOD     (Below EPA standard)
15-35 μg/m³   → MODERATE (EPA 24h standard)
35-55 μg/m³   → UNHEALTHY FOR SENSITIVE
55-150 μg/m³  → UNHEALTHY
150-250 μg/m³ → VERY UNHEALTHY
250+ μg/m³    → HAZARDOUS
```

### Converting PM2.5 to AQI

The US EPA uses this formula for PM2.5 → AQI conversion:

```python
def pm25_to_aqi(pm25):
    """
    Convert PM2.5 concentration to US EPA AQI.

    Args:
        pm25: PM2.5 concentration in μg/m³

    Returns:
        AQI value (0-500)
    """
    # Breakpoints: (C_low, C_high, I_low, I_high)
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm25 <= c_high:
            # Linear interpolation
            aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low
            return round(aqi)

    return 500 if pm25 > 500.4 else 0
```

### Particle Size Reference

| Size | What It Represents |
|------|-------------------|
| 0.3 μm | Bacteria, viruses, smoke |
| 0.5 μm | Bacteria, combustion particles |
| 1.0 μm | Bacteria, mold spores |
| 2.5 μm | Fine dust, allergens |
| 5.0 μm | Pollen, coarse dust |
| 10 μm | Visible dust, sand |

---

## SEN0321 - Ozone

### What It Measures

The SEN0321 uses electrochemical sensing to measure ground-level ozone (O3).

### Raw Data Format

| Field | Type | Unit | Range |
|-------|------|------|-------|
| Ozone | Integer | ppb | 0-10000 |

### No Conversion Needed

The SEN0321 outputs ppb directly. The sensor is factory calibrated.

### Ozone Health Guidelines

```
0-50 ppb    → GOOD       (Normal outdoor levels)
50-70 ppb   → MODERATE   (Sensitive groups may be affected)
70-85 ppb   → UNHEALTHY FOR SENSITIVE (Limit outdoor exertion)
85-105 ppb  → UNHEALTHY  (Everyone affected)
105-200 ppb → VERY UNHEALTHY
200+ ppb    → HAZARDOUS
```

### Understanding Ozone

- **Ground-level ozone** is harmful (smog component)
- **Stratospheric ozone** (ozone layer) is beneficial
- Ozone forms when NOx and VOCs react with sunlight
- Highest levels typically occur in afternoon on sunny days
- Indoor levels are usually much lower than outdoor

---

## MGSV2 - Multi-Gas Sensor

### What It Measures

The MGSV2 (Seeed Multichannel Gas Sensor v2) uses four MOX sensors:
- NO2 (Nitrogen Dioxide)
- C2H5OH (Ethanol)
- VOC (Volatile Organic Compounds)
- CO (Carbon Monoxide)

### Raw Data Format

| Field | Type | Unit | Typical Range |
|-------|------|------|---------------|
| NO2 | Float | ppm | 0.05-10 |
| C2H5OH | Float | ppm | 10-500 |
| VOC | Float | ppm | 1-1000 |
| CO | Float | ppm | 1-1000 |

### Calibration Notes

MOX sensors require:
- 24-48 hour burn-in period
- Temperature/humidity compensation
- Periodic recalibration

The sensor library performs internal compensation, but values should be considered approximate.

### Health Guidelines

**Carbon Monoxide (CO):**
```
0-9 ppm     → GOOD       (Normal indoor level)
9-35 ppm    → MODERATE   (EPA 8-hour limit is 9 ppm)
35-100 ppm  → UNHEALTHY  (Headaches within hours)
100-400 ppm → DANGEROUS  (Headaches within 1-2 hours)
400+ ppm    → LIFE THREATENING
```

**Nitrogen Dioxide (NO2):**
```
0-0.053 ppm → GOOD       (EPA annual standard)
0.053-0.1 ppm → MODERATE
0.1-0.36 ppm → UNHEALTHY FOR SENSITIVE
0.36-0.65 ppm → UNHEALTHY
0.65+ ppm   → VERY UNHEALTHY
```

---

## MQ136 - Hydrogen Sulfide

### What It Measures

The MQ136 is an electrochemical sensor for H2S (hydrogen sulfide) - the "rotten egg" smell gas.

### Raw Data Format

| Field | Type | Unit | Range |
|-------|------|------|-------|
| rawH2s | Integer | ADC | 0-1023 |

### Conversion Formula

The MQ136 requires conversion from raw ADC to ppm. This involves:

1. **Calculate sensor resistance (Rs):**
```python
# Circuit parameters (adjust based on your setup)
LOAD_RESISTANCE = 10000  # 10kΩ load resistor
ADC_MAX = 1023           # 10-bit ADC
VCC = 5.0                # Supply voltage

def raw_to_resistance(raw_value):
    if raw_value == 0:
        return float('inf')
    voltage = (raw_value / ADC_MAX) * VCC
    rs = LOAD_RESISTANCE * (VCC - voltage) / voltage
    return rs
```

2. **Calculate Rs/R0 ratio:**
```python
# R0 must be calibrated in clean air
# Typical R0 is the sensor resistance at 10 ppm H2S
R0 = 10000  # This value must be calibrated!

def get_ratio(raw_value):
    rs = raw_to_resistance(raw_value)
    return rs / R0
```

3. **Convert ratio to ppm:**
```python
def h2s_ppm(raw_value):
    """
    Convert raw ADC reading to H2S ppm.
    Based on MQ136 characteristic curve.

    The relationship is approximately:
    log(ppm) = (log(Rs/R0) - b) / m

    Where m and b are curve-fit constants from datasheet.
    """
    import math

    ratio = get_ratio(raw_value)

    # Curve fit constants (approximate from datasheet)
    m = -0.48  # Slope
    b = 0.62   # Intercept

    if ratio <= 0:
        return 0

    ppm = 10 ** ((math.log10(ratio) - b) / m)
    return max(0, ppm)
```

### Calibration Procedure

1. Place sensor in clean air (0 ppm H2S)
2. Wait 48 hours for burn-in
3. Measure raw ADC value
4. Calculate R0 = Rs (at clean air)

### H2S Health Guidelines

```
0-0.5 ppm    → NORMAL    (Detection threshold ~0.02 ppm)
0.5-10 ppm   → CAUTION   (Eye irritation)
10-50 ppm    → WARNING   (Prolonged exposure harmful)
50-100 ppm   → DANGEROUS (Olfactory fatigue - can't smell it!)
100-300 ppm  → LIFE THREATENING (1 hour exposure)
500+ ppm     → IMMEDIATELY DANGEROUS
```

**Warning:** At high concentrations (>100 ppm), you lose the ability to smell H2S!

---

## Air Quality Index Calculations

### Combined AQI Calculation

The overall AQI is the **maximum** of individual pollutant indices:

```python
def calculate_overall_aqi(pm25, ozone_ppb, co_ppm, no2_ppm):
    """
    Calculate overall AQI from multiple pollutants.
    Returns the highest (worst) individual AQI.
    """
    aqi_pm25 = pm25_to_aqi(pm25)
    aqi_ozone = ozone_to_aqi(ozone_ppb)
    aqi_co = co_to_aqi(co_ppm)
    aqi_no2 = no2_to_aqi(no2_ppm)

    return max(aqi_pm25, aqi_ozone, aqi_co, aqi_no2)
```

### AQI Color Coding

| AQI Range | Category | Color (Hex) |
|-----------|----------|-------------|
| 0-50 | Good | #00E400 |
| 51-100 | Moderate | #FFFF00 |
| 101-150 | Unhealthy for Sensitive | #FF7E00 |
| 151-200 | Unhealthy | #FF0000 |
| 201-300 | Very Unhealthy | #8F3F97 |
| 301-500 | Hazardous | #7E0023 |

---

## Sensor Accuracy and Limitations

### Accuracy Specifications

| Sensor | Parameter | Accuracy |
|--------|-----------|----------|
| SCD30 | CO2 | ±30 ppm + 3% |
| SCD30 | Temperature | ±0.4°C |
| SCD30 | Humidity | ±3% RH |
| BME680 | Temperature | ±1.0°C |
| BME680 | Pressure | ±1 hPa |
| BME680 | Humidity | ±3% RH |
| PMSA003I | PM2.5 | ±10% @ 100-500 μg/m³ |
| SEN0321 | Ozone | ±10% |
| SGP30 | TVOC | ±15% |

### Known Limitations

1. **Cross-sensitivity**: MOX sensors (SGP30, BME680, MGSV2) respond to multiple gases
2. **Temperature effects**: All sensors are affected by temperature. Allow 10-15 minutes warmup
3. **Humidity effects**: High humidity can affect PM sensors and MOX sensors
4. **Drift**: Some sensors drift over time and need periodic recalibration
5. **Response time**: PM sensors are fastest (~1 second), gas sensors slower (~30 seconds)

### Best Practices

1. **Position sensors away from direct airflow** (AC vents, windows)
2. **Mount at breathing height** (1-1.5m from ground)
3. **Keep sensors dry** (not in bathrooms)
4. **Allow warmup time** after power-on
5. **Compare with reference stations** periodically
6. **Log data for 24+ hours** before trusting trends

---

## Quick Reference Card

### Healthy Indoor Air

| Parameter | Good | Acceptable | Take Action |
|-----------|------|------------|-------------|
| CO2 | <800 ppm | <1000 ppm | >1000 ppm |
| PM2.5 | <12 μg/m³ | <35 μg/m³ | >35 μg/m³ |
| TVOC | <220 ppb | <660 ppb | >660 ppb |
| CO | <9 ppm | <35 ppm | >35 ppm |
| Humidity | 40-60% | 30-70% | <30% or >70% |
| Temperature | 20-24°C | 18-26°C | <18°C or >26°C |

### Color Coding System

```
GREEN  = Good, no action needed
YELLOW = Moderate, consider improving
ORANGE = Unhealthy for some, take action
RED    = Unhealthy for all, act immediately
PURPLE = Very unhealthy, evacuate if possible
MAROON = Hazardous, emergency
```
