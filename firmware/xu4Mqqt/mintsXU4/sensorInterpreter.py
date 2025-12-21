"""
Sensor Data Interpreter for UTSensing Air Quality Monitoring System

This module converts raw sensor readings into human-interpretable values
with health assessments, AQI calculations, and color coding.

Author: UTSensing Project
License: MIT
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum


class AirQualityLevel(Enum):
    """Air quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    MODERATE = "moderate"
    POOR = "poor"
    UNHEALTHY = "unhealthy"
    VERY_UNHEALTHY = "very_unhealthy"
    HAZARDOUS = "hazardous"


@dataclass
class SensorReading:
    """Container for interpreted sensor data."""
    raw_value: float
    interpreted_value: float
    unit: str
    level: AirQualityLevel
    level_name: str
    color: str
    color_hex: str
    action: str
    description: str


# ============================================================================
# Color Definitions
# ============================================================================

LEVEL_COLORS = {
    AirQualityLevel.EXCELLENT: {"name": "green", "hex": "#00E400"},
    AirQualityLevel.GOOD: {"name": "green", "hex": "#00E400"},
    AirQualityLevel.FAIR: {"name": "yellow", "hex": "#FFFF00"},
    AirQualityLevel.MODERATE: {"name": "yellow", "hex": "#FFFF00"},
    AirQualityLevel.POOR: {"name": "orange", "hex": "#FF7E00"},
    AirQualityLevel.UNHEALTHY: {"name": "red", "hex": "#FF0000"},
    AirQualityLevel.VERY_UNHEALTHY: {"name": "purple", "hex": "#8F3F97"},
    AirQualityLevel.HAZARDOUS: {"name": "maroon", "hex": "#7E0023"},
}


# ============================================================================
# CO2 Interpretation (SCD30)
# ============================================================================

def interpret_co2(co2_ppm: float) -> SensorReading:
    """
    Interpret CO2 reading from SCD30 sensor.

    Args:
        co2_ppm: CO2 concentration in parts per million

    Returns:
        SensorReading with interpreted values
    """
    if co2_ppm < 600:
        level = AirQualityLevel.EXCELLENT
        action = "No action needed"
        description = "Fresh, outdoor-quality air"
    elif co2_ppm < 800:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Well-ventilated indoor space"
    elif co2_ppm < 1000:
        level = AirQualityLevel.FAIR
        action = "Consider opening a window"
        description = "Acceptable, but could use ventilation"
    elif co2_ppm < 1500:
        level = AirQualityLevel.MODERATE
        action = "Open windows or increase ventilation"
        description = "Stuffy air, ventilation recommended"
    elif co2_ppm < 2500:
        level = AirQualityLevel.POOR
        action = "Ventilate immediately"
        description = "May cause drowsiness and headaches"
    else:
        level = AirQualityLevel.UNHEALTHY
        action = "Leave area and ventilate"
        description = "Cognitive impairment likely"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=co2_ppm,
        interpreted_value=co2_ppm,
        unit="ppm",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Temperature Interpretation
# ============================================================================

def interpret_temperature(temp_celsius: float) -> SensorReading:
    """
    Interpret temperature reading.

    Args:
        temp_celsius: Temperature in degrees Celsius

    Returns:
        SensorReading with interpreted values
    """
    if 20 <= temp_celsius <= 24:
        level = AirQualityLevel.EXCELLENT
        action = "No action needed"
        description = "Ideal comfort range"
    elif 18 <= temp_celsius <= 26:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Comfortable temperature"
    elif 15 <= temp_celsius <= 28:
        level = AirQualityLevel.FAIR
        action = "Consider adjusting heating/cooling"
        description = "Slightly outside comfort zone"
    else:
        level = AirQualityLevel.MODERATE
        action = "Adjust heating/cooling"
        description = "Uncomfortable temperature"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=temp_celsius,
        interpreted_value=temp_celsius,
        unit="°C",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Humidity Interpretation
# ============================================================================

def interpret_humidity(humidity_percent: float) -> SensorReading:
    """
    Interpret relative humidity reading.

    Args:
        humidity_percent: Relative humidity in percent

    Returns:
        SensorReading with interpreted values
    """
    if 40 <= humidity_percent <= 60:
        level = AirQualityLevel.EXCELLENT
        action = "No action needed"
        description = "Ideal humidity range"
    elif 30 <= humidity_percent <= 70:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Acceptable humidity"
    elif 20 <= humidity_percent <= 80:
        level = AirQualityLevel.FAIR
        action = "Consider humidifier or dehumidifier"
        description = "Slightly outside ideal range"
    else:
        level = AirQualityLevel.MODERATE
        if humidity_percent < 20:
            action = "Use a humidifier"
            description = "Very dry air - may cause irritation"
        else:
            action = "Use a dehumidifier"
            description = "Very humid - may cause mold"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=humidity_percent,
        interpreted_value=humidity_percent,
        unit="%RH",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# PM2.5 Interpretation (PMSA003I)
# ============================================================================

def pm25_to_aqi(pm25: float) -> int:
    """
    Convert PM2.5 concentration to US EPA AQI.

    Formula:
        AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low

    Where:
        C = PM2.5 concentration
        C_low, C_high = Concentration breakpoints
        I_low, I_high = AQI breakpoints

    Args:
        pm25: PM2.5 concentration in μg/m³

    Returns:
        AQI value (0-500)
    """
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
            aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low
            return round(aqi)

    return 500 if pm25 > 500.4 else 0


def interpret_pm25(pm25_ugm3: float) -> SensorReading:
    """
    Interpret PM2.5 reading from PMSA003I sensor.

    Args:
        pm25_ugm3: PM2.5 concentration in μg/m³

    Returns:
        SensorReading with interpreted values including AQI
    """
    aqi = pm25_to_aqi(pm25_ugm3)

    if aqi <= 50:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Air quality is satisfactory"
    elif aqi <= 100:
        level = AirQualityLevel.MODERATE
        action = "Sensitive individuals should limit outdoor exertion"
        description = "Acceptable; some pollutants may be a concern"
    elif aqi <= 150:
        level = AirQualityLevel.POOR
        action = "Sensitive groups should limit outdoor exertion"
        description = "May affect sensitive groups"
    elif aqi <= 200:
        level = AirQualityLevel.UNHEALTHY
        action = "Everyone should limit outdoor exertion"
        description = "Everyone may experience health effects"
    elif aqi <= 300:
        level = AirQualityLevel.VERY_UNHEALTHY
        action = "Avoid outdoor activities"
        description = "Health alert: serious effects possible"
    else:
        level = AirQualityLevel.HAZARDOUS
        action = "Stay indoors with air filtration"
        description = "Emergency conditions"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=pm25_ugm3,
        interpreted_value=aqi,
        unit="AQI",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=f"PM2.5: {pm25_ugm3:.1f} μg/m³ = AQI {aqi}"
    )


def interpret_pm10(pm10_ugm3: float) -> SensorReading:
    """
    Interpret PM10 reading.

    Args:
        pm10_ugm3: PM10 concentration in μg/m³

    Returns:
        SensorReading with interpreted values
    """
    # PM10 AQI breakpoints
    if pm10_ugm3 <= 54:
        level = AirQualityLevel.GOOD
        aqi = round((50 / 54) * pm10_ugm3)
    elif pm10_ugm3 <= 154:
        level = AirQualityLevel.MODERATE
        aqi = round(((100 - 51) / (154 - 55)) * (pm10_ugm3 - 55) + 51)
    elif pm10_ugm3 <= 254:
        level = AirQualityLevel.POOR
        aqi = round(((150 - 101) / (254 - 155)) * (pm10_ugm3 - 155) + 101)
    elif pm10_ugm3 <= 354:
        level = AirQualityLevel.UNHEALTHY
        aqi = round(((200 - 151) / (354 - 255)) * (pm10_ugm3 - 255) + 151)
    elif pm10_ugm3 <= 424:
        level = AirQualityLevel.VERY_UNHEALTHY
        aqi = round(((300 - 201) / (424 - 355)) * (pm10_ugm3 - 355) + 201)
    else:
        level = AirQualityLevel.HAZARDOUS
        aqi = min(500, round(((500 - 301) / (604 - 425)) * (pm10_ugm3 - 425) + 301))

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=pm10_ugm3,
        interpreted_value=aqi,
        unit="AQI",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action="See PM2.5 recommendations",
        description=f"PM10: {pm10_ugm3:.1f} μg/m³ = AQI {aqi}"
    )


# ============================================================================
# TVOC Interpretation (SGP30)
# ============================================================================

def interpret_tvoc(tvoc_ppb: float) -> SensorReading:
    """
    Interpret TVOC reading from SGP30 sensor.

    Args:
        tvoc_ppb: Total VOC concentration in parts per billion

    Returns:
        SensorReading with interpreted values
    """
    if tvoc_ppb < 65:
        level = AirQualityLevel.EXCELLENT
        action = "No action needed"
        description = "Pristine air quality"
    elif tvoc_ppb < 220:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Normal indoor VOC levels"
    elif tvoc_ppb < 660:
        level = AirQualityLevel.FAIR
        action = "Identify and reduce VOC sources"
        description = "Elevated VOCs, investigate sources"
    elif tvoc_ppb < 2200:
        level = AirQualityLevel.POOR
        action = "Ventilate and remove VOC sources"
        description = "High VOC levels, reduce exposure"
    else:
        level = AirQualityLevel.UNHEALTHY
        action = "Ventilate immediately"
        description = "Very high VOC levels"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=tvoc_ppb,
        interpreted_value=tvoc_ppb,
        unit="ppb",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Ozone Interpretation (SEN0321)
# ============================================================================

def interpret_ozone(ozone_ppb: float) -> SensorReading:
    """
    Interpret ozone reading from SEN0321 sensor.

    Args:
        ozone_ppb: Ozone concentration in parts per billion

    Returns:
        SensorReading with interpreted values
    """
    if ozone_ppb < 50:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Normal ozone levels"
    elif ozone_ppb < 70:
        level = AirQualityLevel.MODERATE
        action = "Sensitive groups should limit outdoor exertion"
        description = "Moderate ozone levels"
    elif ozone_ppb < 85:
        level = AirQualityLevel.POOR
        action = "Limit prolonged outdoor exertion"
        description = "Unhealthy for sensitive groups"
    elif ozone_ppb < 105:
        level = AirQualityLevel.UNHEALTHY
        action = "Avoid prolonged outdoor exertion"
        description = "Unhealthy for everyone"
    elif ozone_ppb < 200:
        level = AirQualityLevel.VERY_UNHEALTHY
        action = "Stay indoors"
        description = "Very unhealthy ozone levels"
    else:
        level = AirQualityLevel.HAZARDOUS
        action = "Avoid all outdoor activity"
        description = "Hazardous ozone levels"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=ozone_ppb,
        interpreted_value=ozone_ppb,
        unit="ppb",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Carbon Monoxide Interpretation (MGSV2)
# ============================================================================

def interpret_co(co_ppm: float) -> SensorReading:
    """
    Interpret carbon monoxide reading from MGSV2 sensor.

    Args:
        co_ppm: CO concentration in parts per million

    Returns:
        SensorReading with interpreted values
    """
    if co_ppm < 9:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Normal CO levels"
    elif co_ppm < 35:
        level = AirQualityLevel.MODERATE
        action = "Investigate source, ensure ventilation"
        description = "Elevated CO, monitor closely"
    elif co_ppm < 100:
        level = AirQualityLevel.UNHEALTHY
        action = "Ventilate and find source"
        description = "Headaches possible within hours"
    elif co_ppm < 400:
        level = AirQualityLevel.VERY_UNHEALTHY
        action = "Leave area immediately"
        description = "Dangerous CO levels"
    else:
        level = AirQualityLevel.HAZARDOUS
        action = "EVACUATE - Call emergency services"
        description = "Life-threatening CO levels"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=co_ppm,
        interpreted_value=co_ppm,
        unit="ppm",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Nitrogen Dioxide Interpretation (MGSV2)
# ============================================================================

def interpret_no2(no2_ppm: float) -> SensorReading:
    """
    Interpret nitrogen dioxide reading from MGSV2 sensor.

    Args:
        no2_ppm: NO2 concentration in parts per million

    Returns:
        SensorReading with interpreted values
    """
    if no2_ppm < 0.053:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Normal NO2 levels"
    elif no2_ppm < 0.1:
        level = AirQualityLevel.MODERATE
        action = "Monitor levels"
        description = "Slightly elevated NO2"
    elif no2_ppm < 0.36:
        level = AirQualityLevel.POOR
        action = "Sensitive groups should limit exposure"
        description = "Unhealthy for sensitive groups"
    elif no2_ppm < 0.65:
        level = AirQualityLevel.UNHEALTHY
        action = "Limit outdoor exertion"
        description = "Unhealthy NO2 levels"
    else:
        level = AirQualityLevel.VERY_UNHEALTHY
        action = "Stay indoors"
        description = "Very unhealthy NO2 levels"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=no2_ppm,
        interpreted_value=no2_ppm * 1000,  # Convert to ppb for display
        unit="ppb",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# H2S Interpretation (MQ136)
# ============================================================================

# MQ136 calibration constants
MQ136_LOAD_RESISTANCE = 10000  # 10kΩ load resistor
MQ136_ADC_MAX = 1023           # 10-bit ADC
MQ136_VCC = 5.0                # Supply voltage
MQ136_R0 = 10000               # Calibrated resistance in clean air


def mq136_raw_to_ppm(raw_value: int, r0: float = MQ136_R0) -> float:
    """
    Convert MQ136 raw ADC reading to H2S concentration in ppm.

    The MQ136 sensor resistance changes with H2S concentration.
    The relationship follows a power law on a log-log scale.

    Formula:
        Rs = RL * (Vcc - Vout) / Vout
        ratio = Rs / R0
        ppm = 10^((log10(ratio) - b) / m)

    Where:
        Rs = Sensor resistance
        RL = Load resistance (10kΩ)
        R0 = Calibrated resistance in clean air
        m, b = Curve fit constants from datasheet

    Args:
        raw_value: ADC reading (0-1023)
        r0: Calibrated R0 value

    Returns:
        H2S concentration in ppm
    """
    if raw_value <= 0:
        return 0.0

    # Calculate sensor resistance
    voltage = (raw_value / MQ136_ADC_MAX) * MQ136_VCC
    if voltage >= MQ136_VCC:
        return 0.0

    rs = MQ136_LOAD_RESISTANCE * (MQ136_VCC - voltage) / voltage
    ratio = rs / r0

    if ratio <= 0:
        return 0.0

    # Curve fit constants (from MQ136 datasheet)
    m = -0.48  # Slope on log-log scale
    b = 0.62   # Y-intercept

    try:
        ppm = 10 ** ((math.log10(ratio) - b) / m)
        return max(0.0, ppm)
    except (ValueError, ZeroDivisionError):
        return 0.0


def interpret_h2s(raw_value: int) -> SensorReading:
    """
    Interpret H2S reading from MQ136 sensor.

    Args:
        raw_value: Raw ADC reading (0-1023)

    Returns:
        SensorReading with interpreted values
    """
    h2s_ppm = mq136_raw_to_ppm(raw_value)

    if h2s_ppm < 0.5:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Normal H2S levels"
    elif h2s_ppm < 10:
        level = AirQualityLevel.MODERATE
        action = "Investigate odor source"
        description = "Detectable H2S, may cause eye irritation"
    elif h2s_ppm < 50:
        level = AirQualityLevel.POOR
        action = "Ventilate and leave area"
        description = "Prolonged exposure harmful"
    elif h2s_ppm < 100:
        level = AirQualityLevel.UNHEALTHY
        action = "Evacuate area"
        description = "Dangerous - olfactory fatigue possible"
    else:
        level = AirQualityLevel.HAZARDOUS
        action = "EVACUATE IMMEDIATELY - Call emergency services"
        description = "Life-threatening H2S levels"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=raw_value,
        interpreted_value=h2s_ppm,
        unit="ppm",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# BME680 Gas Resistance Interpretation
# ============================================================================

def interpret_gas_resistance(gas_kohm: float, humidity: float = 50.0) -> SensorReading:
    """
    Interpret BME680 gas resistance reading.

    Higher resistance generally indicates cleaner air.
    The absolute value depends on environmental conditions.

    Args:
        gas_kohm: Gas resistance in kΩ
        humidity: Current humidity for compensation

    Returns:
        SensorReading with interpreted values
    """
    # Humidity compensation (simplified)
    # Optimal humidity for sensor is around 40%
    humidity_factor = 1.0 + (humidity - 40) * 0.01

    # Compensated resistance
    compensated = gas_kohm / humidity_factor

    if compensated > 300:
        level = AirQualityLevel.EXCELLENT
        action = "No action needed"
        description = "Very clean air"
    elif compensated > 200:
        level = AirQualityLevel.GOOD
        action = "No action needed"
        description = "Clean indoor air"
    elif compensated > 100:
        level = AirQualityLevel.FAIR
        action = "Consider ventilation"
        description = "Some VOCs present"
    elif compensated > 50:
        level = AirQualityLevel.MODERATE
        action = "Ventilate room"
        description = "Moderate VOC levels"
    else:
        level = AirQualityLevel.POOR
        action = "Ventilate immediately"
        description = "High VOC levels detected"

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=gas_kohm,
        interpreted_value=compensated,
        unit="kΩ",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action=action,
        description=description
    )


# ============================================================================
# Pressure Interpretation (BME680)
# ============================================================================

def interpret_pressure(pressure_kpa: float) -> SensorReading:
    """
    Interpret barometric pressure reading.

    Args:
        pressure_kpa: Pressure in kilopascals

    Returns:
        SensorReading with interpreted values
    """
    # Convert to hPa for weather interpretation
    pressure_hpa = pressure_kpa * 10

    if pressure_hpa > 1022:
        description = "High pressure - fair weather likely"
        level = AirQualityLevel.GOOD
    elif pressure_hpa > 1009:
        description = "Normal pressure - stable weather"
        level = AirQualityLevel.GOOD
    elif pressure_hpa > 1000:
        description = "Low pressure - weather change possible"
        level = AirQualityLevel.FAIR
    else:
        description = "Very low pressure - storm possible"
        level = AirQualityLevel.MODERATE

    colors = LEVEL_COLORS[level]
    return SensorReading(
        raw_value=pressure_kpa,
        interpreted_value=pressure_hpa,
        unit="hPa",
        level=level,
        level_name=level.value.replace("_", " ").title(),
        color=colors["name"],
        color_hex=colors["hex"],
        action="Informational only",
        description=description
    )


# ============================================================================
# Combined AQI Calculation
# ============================================================================

def calculate_overall_aqi(
    pm25: Optional[float] = None,
    pm10: Optional[float] = None,
    ozone_ppb: Optional[float] = None,
    co_ppm: Optional[float] = None,
) -> Tuple[int, AirQualityLevel, str]:
    """
    Calculate overall Air Quality Index from multiple pollutants.

    The overall AQI is the maximum (worst) of individual pollutant AQIs.

    Args:
        pm25: PM2.5 concentration in μg/m³
        pm10: PM10 concentration in μg/m³
        ozone_ppb: Ozone concentration in ppb
        co_ppm: CO concentration in ppm

    Returns:
        Tuple of (AQI value, AirQualityLevel, dominant pollutant name)
    """
    aqis = {}

    if pm25 is not None:
        aqis["PM2.5"] = pm25_to_aqi(pm25)

    if pm10 is not None:
        reading = interpret_pm10(pm10)
        aqis["PM10"] = int(reading.interpreted_value)

    if ozone_ppb is not None:
        # Simplified ozone AQI
        aqis["Ozone"] = min(500, int(ozone_ppb * 2))

    if co_ppm is not None:
        # Simplified CO AQI
        aqis["CO"] = min(500, int(co_ppm * 5))

    if not aqis:
        return (0, AirQualityLevel.GOOD, "None")

    max_aqi = max(aqis.values())
    dominant = max(aqis, key=aqis.get)

    if max_aqi <= 50:
        level = AirQualityLevel.GOOD
    elif max_aqi <= 100:
        level = AirQualityLevel.MODERATE
    elif max_aqi <= 150:
        level = AirQualityLevel.POOR
    elif max_aqi <= 200:
        level = AirQualityLevel.UNHEALTHY
    elif max_aqi <= 300:
        level = AirQualityLevel.VERY_UNHEALTHY
    else:
        level = AirQualityLevel.HAZARDOUS

    return (max_aqi, level, dominant)


# ============================================================================
# Convenience Functions
# ============================================================================

def interpret_all_sensors(sensor_data: Dict) -> Dict[str, SensorReading]:
    """
    Interpret all sensor readings from a data dictionary.

    Args:
        sensor_data: Dictionary with sensor readings

    Returns:
        Dictionary of SensorReading objects
    """
    results = {}

    # SCD30
    if "co2" in sensor_data:
        results["co2"] = interpret_co2(float(sensor_data["co2"]))
    if "temperature" in sensor_data:
        results["temperature"] = interpret_temperature(float(sensor_data["temperature"]))
    if "humidity" in sensor_data:
        results["humidity"] = interpret_humidity(float(sensor_data["humidity"]))

    # PMSA003I
    if "pm2p5Env" in sensor_data:
        results["pm25"] = interpret_pm25(float(sensor_data["pm2p5Env"]))
    if "pm10Env" in sensor_data:
        results["pm10"] = interpret_pm10(float(sensor_data["pm10Env"]))

    # SGP30
    if "TVOC" in sensor_data:
        results["tvoc"] = interpret_tvoc(float(sensor_data["TVOC"]))

    # SEN0321
    if "Ozone" in sensor_data:
        results["ozone"] = interpret_ozone(float(sensor_data["Ozone"]))

    # MGSV2
    if "CO" in sensor_data:
        results["co"] = interpret_co(float(sensor_data["CO"]))
    if "NO2" in sensor_data:
        results["no2"] = interpret_no2(float(sensor_data["NO2"]))

    # MQ136
    if "rawH2s" in sensor_data:
        results["h2s"] = interpret_h2s(int(sensor_data["rawH2s"]))

    # BME680
    if "gas" in sensor_data:
        humidity = float(sensor_data.get("humidity", 50))
        results["gas_resistance"] = interpret_gas_resistance(
            float(sensor_data["gas"]), humidity
        )
    if "pressure" in sensor_data:
        results["pressure"] = interpret_pressure(float(sensor_data["pressure"]))

    return results


def get_color_for_value(param: str, value: float) -> str:
    """
    Get color hex code for a sensor value.

    Useful for dashboard coloring.

    Args:
        param: Parameter name (co2, pm25, tvoc, etc.)
        value: Sensor reading value

    Returns:
        Hex color code string
    """
    interpreters = {
        "co2": interpret_co2,
        "temperature": interpret_temperature,
        "humidity": interpret_humidity,
        "pm25": interpret_pm25,
        "pm10": interpret_pm10,
        "tvoc": interpret_tvoc,
        "ozone": interpret_ozone,
        "co": interpret_co,
        "no2": interpret_no2,
    }

    if param in interpreters:
        reading = interpreters[param](value)
        return reading.color_hex

    return "#808080"  # Gray for unknown


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    # Test with sample data
    test_data = {
        "co2": "850",
        "temperature": "23.5",
        "humidity": "55",
        "pm2p5Env": "15",
        "pm10Env": "25",
        "TVOC": "150",
        "Ozone": "45",
        "CO": "2",
        "NO2": "0.05",
        "rawH2s": "200",
        "gas": "150",
        "pressure": "101.3",
    }

    print("=" * 60)
    print("UTSensing Sensor Interpreter - Test Output")
    print("=" * 60)

    results = interpret_all_sensors(test_data)

    for name, reading in results.items():
        print(f"\n{name.upper()}:")
        print(f"  Raw: {reading.raw_value}")
        print(f"  Interpreted: {reading.interpreted_value} {reading.unit}")
        print(f"  Level: {reading.level_name} ({reading.color})")
        print(f"  Action: {reading.action}")
        print(f"  Description: {reading.description}")

    # Test overall AQI
    aqi, level, dominant = calculate_overall_aqi(
        pm25=15, pm10=25, ozone_ppb=45, co_ppm=2
    )
    print(f"\n{'=' * 60}")
    print(f"Overall AQI: {aqi} ({level.value})")
    print(f"Dominant pollutant: {dominant}")
