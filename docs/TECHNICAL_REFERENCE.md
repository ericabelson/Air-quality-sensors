# Technical Reference Appendix

This document provides verified technical specifications, datasheets, and reference materials for all sensors and components used in the UTSensing air quality monitoring system.

**Last Updated:** 2025-12-27

---

## Table of Contents

1. [Sensor Datasheets](#sensor-datasheets)
2. [Official Manufacturer Documentation](#official-manufacturer-documentation)
3. [Software and Tools](#software-and-tools)
4. [Technical Glossary](#technical-glossary)
5. [Calibration Procedures](#calibration-procedures)
6. [Wiring Diagrams](#wiring-diagrams)
7. [Real-Time Clock (RTC) Battery Backup](#real-time-clock-rtc-battery-backup)
8. [Health and Safety References](#health-and-safety-references)

---

## Sensor Datasheets

### SCD30 - CO2, Temperature, and Humidity Sensor

**Manufacturer:** Sensirion AG

**Official Datasheet:**
- [Sensirion SCD30 Datasheet (PDF)](https://sensirion.com/media/documents/4EAF6AF8/61652C3C/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | NDIR (Non-Dispersive Infrared) |
| **CO2 Measurement Range** | 400 - 10,000 ppm |
| **CO2 Accuracy** | ±(30 ppm + 3% of reading) |
| **Temperature Range** | -40°C to +70°C |
| **Temperature Accuracy** | ±0.4°C (0°C to 50°C) |
| **Humidity Range** | 0 - 100% RH |
| **Humidity Accuracy** | ±3% RH (20°C to 60°C, 20% to 80% RH) |
| **Interface** | I2C (0x61) |
| **Supply Voltage** | 3.3 - 5.5V |
| **Current Consumption** | 19 mA @ 1 measurement per 2s |
| **Dimensions** | 35 x 23 x 7 mm |
| **Response Time** | ~20 seconds (τ63%) |

**Important Notes:**
- NDIR technology provides highly accurate CO2 measurements without drift
- Built-in temperature compensation
- Automatic Self-Calibration (ASC) can be enabled for long-term stability
- Sensor self-heats by approximately 2-3°C above ambient

**Purchase Links:**
- [Adafruit](https://www.adafruit.com/product/4867)
- [SparkFun](https://www.sparkfun.com/products/15112)
- [Seeed Studio](https://www.seeedstudio.com/Grove-CO2-Temperature-Humidity-Sensor-SCD30-p-2911.html)

---

### BME680 - Environmental Sensor (Gas, Pressure, Temperature, Humidity)

**Manufacturer:** Bosch Sensortec

**Official Datasheet:**
- [Bosch BME680 Datasheet (PDF)](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- [Adafruit Mirror (PDF)](https://cdn-shop.adafruit.com/product-files/3660/BME680.pdf)

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | Metal Oxide (MOX) gas sensor + MEMS pressure/temp/humidity |
| **Temperature Range** | -40°C to +85°C |
| **Temperature Accuracy** | ±1.0°C (0°C to 65°C) |
| **Humidity Range** | 0 - 100% RH |
| **Humidity Accuracy** | ±3% RH (20% to 80% RH) |
| **Pressure Range** | 300 - 1100 hPa |
| **Pressure Accuracy** | ±1.0 hPa (0°C to 65°C, 900-1100 hPa) |
| **Gas Sensor Response** | 1 - 500 kΩ (resistance output) |
| **Interface** | I2C (0x76 or 0x77) / SPI |
| **Supply Voltage** | 1.71 - 3.6V |
| **Current Consumption** | 2.1 μA @ 1 Hz (ultra-low power mode) |
| **Dimensions** | 3.0 x 3.0 x 1.0 mm (LGA package) |

**Important Notes:**
- Gas sensor detects VOCs (Volatile Organic Compounds) by measuring resistance
- Lower resistance = higher VOC concentration
- Requires warm-up period (5-10 minutes) for stable readings
- Gas sensor readings are relative, not absolute PPM values
- Bosch provides proprietary BSEC library for IAQ (Indoor Air Quality) index calculation

**Gas Sensor Characteristics:**
- Responds to: Ethanol, acetone, isoprene (breath), formaldehyde, and other VOCs
- Does NOT provide specific gas identification
- Complies with ISO 16000-29 standard for VOC detectors

**Purchase Links:**
- [Adafruit](https://www.adafruit.com/product/3660)
- [SparkFun](https://www.sparkfun.com/products/16466)
- [Pimoroni](https://shop.pimoroni.com/products/bme680-breakout)

---

### SGP30 - VOC and eCO2 Sensor

**Manufacturer:** Sensirion AG

**Datasheet Resources:**
- Official datasheet: Visit [sensirion.com](https://sensirion.com/products/catalog/SGP30/) and download from product page
- [Adafruit Learning Guide](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor)

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | Metal Oxide (MOX) multi-pixel gas sensor |
| **TVOC Range** | 0 - 60,000 ppb |
| **eCO2 Range** | 400 - 60,000 ppm |
| **TVOC Resolution** | 1 ppb |
| **eCO2 Resolution** | 1 ppm |
| **Interface** | I2C (0x58) |
| **Supply Voltage** | 1.62 - 1.98V (typical 1.8V) |
| **Sampling Rate** | 1 Hz (every second) |
| **Response Time** | <10 seconds (τ63%) |
| **Dimensions** | 2.45 x 2.45 x 0.9 mm (DFN package) |

**Important Notes:**
- **eCO2 is NOT real CO2!** It's calculated from TVOC levels assuming human occupancy correlation
- Requires 12-hour burn-in period in clean air for first use
- Baseline calibration values should be saved and restored on power-up
- Measures total VOCs, cannot identify specific compounds
- On-chip humidity compensation improves accuracy

**Baseline Calibration:**
- After 12 hours in clean air, save baseline values (eCO2_base, TVOC_base)
- Restore these values on every power-up for accurate readings
- Recalibrate every 6 months or if moved to different environment

**Purchase Links:**
- [Adafruit](https://www.adafruit.com/product/3709)
- [SparkFun](https://www.sparkfun.com/products/16531)

---

### PMSA003I - Particulate Matter Sensor

**Manufacturer:** Plantower

**Official Datasheet:**
- [Plantower PMSA003I Datasheet (Mouser)](https://www.mouser.com/datasheet/2/737/4505_PMSA003I_series_data_manual_English_V2_6-2489521.pdf)
- [Adafruit Learning Guide (PDF)](https://cdn-learn.adafruit.com/downloads/pdf/pmsa003i.pdf)

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | Laser scattering |
| **Particle Size Detection** | 0.3 μm minimum |
| **Measurement Range (PM2.5)** | 0 - 1,000 μg/m³ |
| **PM Data Outputs** | PM1.0, PM2.5, PM10 (standard & environmental) |
| **Particle Count Bins** | 0.3, 0.5, 1.0, 2.5, 5.0, 10.0 μm |
| **Resolution** | 1 μg/m³ |
| **Interface** | I2C (0x12) |
| **Supply Voltage** | 5V (requires 5V for internal fan) |
| **Current Consumption** | ~100 mA (fan running) |
| **Update Rate** | 1 second |
| **Warm-up Time** | 30 seconds |
| **Operating Temperature** | -10°C to +60°C |
| **Dimensions** | 38 x 35 x 12 mm |

**Important Notes:**
- Internal fan required for air circulation (5V supply needed)
- **Environmental values** should be used for health assessments (not Standard values)
- Standard values are normalized to 20°C, 1013 hPa
- Laser scattering method is optical, not gravimetric
- Accuracy decreases at very high concentrations (>500 μg/m³)
- Keep away from water and condensation

**Data Format:**
- Provides both Standard Particle (CF=1) and Atmospheric Environment data
- Use **Atmospheric Environment** (pmXEnv) values for real-world air quality assessment

**Purchase Links:**
- [Adafruit](https://www.adafruit.com/product/4632)
- [Smart Prototyping](https://www.smart-prototyping.com/PM-Sensor-Air-Quality-Sensor-PMSA003I)

---

### SEN0321 - Ozone (O3) Sensor

**Manufacturer:** DFRobot

**Datasheet Resources:**
- [DFRobot Product Page](https://www.dfrobot.com/product-1982.html)
- Download datasheet from product page above

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | Electrochemical |
| **Measurement Range** | 0 - 10 ppm (0 - 10,000 ppb) |
| **Resolution** | 10 ppb |
| **Accuracy** | ±10% of reading |
| **Interface** | I2C (0x73) |
| **Supply Voltage** | 3.3 - 5.5V |
| **Operating Temperature** | -20°C to +50°C |
| **Response Time** | <90 seconds |
| **Lifespan** | 2+ years (typical) |

**Important Notes:**
- Electrochemical sensors have limited lifespan (consumable component)
- Cross-sensitivity to NO2 and Cl2 may affect readings
- Requires 48-hour stabilization period after first power-on
- Temperature and humidity compensation recommended
- Factory calibrated, outputs ppb directly

**Calibration:**
- Factory calibrated - no user calibration typically needed
- If accuracy degrades, recalibrate in known clean air (0 ppb O3)

**Purchase Links:**
- [DFRobot](https://www.dfrobot.com/product-1982.html)
- [RobotShop](https://www.robotshop.com/products/gravity-i2c-ozone-sensor)

---

### Grove Multichannel Gas Sensor V2 (MGSV2)

**Manufacturer:** Seeed Studio

**Datasheet Resources:**
- [Seeed Studio Wiki](https://wiki.seeedstudio.com/Grove-Multichannel-Gas-Sensor-V2/)
- Download datasheet and schematics from wiki above

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | 4x Metal Oxide (MOX) sensors |
| **Gases Detected** | NO2, C2H5OH (Ethanol), VOC, CO |
| **NO2 Range** | 0.05 - 10 ppm |
| **C2H5OH Range** | 10 - 500 ppm |
| **VOC Range** | 0 - 1000 ppm |
| **CO Range** | 1 - 1000 ppm |
| **Interface** | I2C (0x08) |
| **Supply Voltage** | 3.3 - 5V |
| **Warm-up Time** | 3-5 minutes |
| **Operating Temperature** | -20°C to +50°C |

**Important Notes:**
- Uses GM-102B (NO2), GM-302B (Ethanol), GM-502B (VOC), GM-702B (CO) sensors
- Requires 24-48 hour burn-in period for stable readings
- Cross-sensitivity between sensors is common
- Temperature/humidity compensation built into firmware
- Values should be considered approximate for consumer applications

**Onboard MCU:**
- STM32F030F4P6 microcontroller handles sensor reading and I2C communication
- Firmware is factory-programmed
- Outputs compensated ppm values

**Purchase Links:**
- [Seeed Studio](https://www.seeedstudio.com/Grove-Multichannel-Gas-Sensor-v2-p-4569.html)

---

### MQ136 - Hydrogen Sulfide (H2S) Sensor

**Manufacturer:** Zhengzhou Winsen Electronics Technology Co., Ltd

**Datasheet Resources:**
- Search "MQ136 datasheet PDF" for manufacturer datasheet
- [SparkFun Guide](https://www.sparkfun.com/datasheets/Sensors/Biometric/MQ-136.pdf)

**Key Specifications:**
| Parameter | Specification |
|-----------|---------------|
| **Technology** | Tin Dioxide (SnO2) semiconductor |
| **Target Gas** | Hydrogen Sulfide (H2S) |
| **Detection Range** | 1 - 200 ppm H2S |
| **Interface** | Analog output (resistance-based) |
| **Supply Voltage** | 5V ± 0.1V |
| **Heater Voltage** | 5V ± 0.1V |
| **Load Resistance** | Adjustable (typically 10 kΩ) |
| **Preheat Time** | 48 hours minimum |
| **Operating Temperature** | -20°C to +50°C |
| **Operating Humidity** | <95% RH |

**Important Notes:**
- **CRITICAL:** Requires 48-hour burn-in period for first use
- Analog output requires ADC (Analog-to-Digital Converter)
- Resistance decreases with increasing H2S concentration
- Must calibrate R0 (sensor resistance in clean air) before use
- Cross-sensitive to other sulfur compounds
- Heater element runs hot (~200°C) - ensure proper ventilation

**Calibration Procedure:**
1. Place sensor in clean air (0 ppm H2S) after 48-hour burn-in
2. Wait 24 hours in clean air
3. Measure sensor resistance (Rs)
4. Record this as R0 (baseline resistance)
5. Use Rs/R0 ratio and characteristic curve to calculate ppm

**Characteristic Curve:**
- Logarithmic relationship: ppm = f(Rs/R0)
- Slope (m) ≈ -0.48
- Y-intercept (b) ≈ 0.62
- Formula: `ppm = 10^((log(Rs/R0) - b) / m)`

**Safety Warning:**
- H2S is extremely toxic (IDLH: 100 ppm)
- Above 100 ppm, olfactory paralysis occurs (cannot smell it!)
- Never rely solely on this sensor for life-safety applications
- Use proper gas detection equipment for safety-critical applications

**Purchase Links:**
- [SparkFun](https://www.sparkfun.com/products/9405)
- [Various Chinese suppliers on AliExpress/Banggood](https://www.aliexpress.com/wholesale?SearchText=MQ136)

---

## Official Manufacturer Documentation

### Sensirion (SCD30, SGP30)
- **Website:** [sensirion.com](https://sensirion.com)
- **Product Catalogs:** [CO2 Sensors](https://sensirion.com/products/catalog/?category=carbon-dioxide-co2) | [VOC Sensors](https://sensirion.com/products/catalog/?category=voc-volatile-organic-compounds)
- **Application Notes:** Available on product pages
- **Sample Code:** [GitHub](https://github.com/Sensirion)

### Bosch Sensortec (BME680)
- **Website:** [bosch-sensortec.com](https://www.bosch-sensortec.com)
- **BME680 Product Page:** [bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/)
- **BSEC Library:** [BSEC Software](https://www.bosch-sensortec.com/software-tools/software/bme680-software-bsec/)
- **GitHub:** [boschsensortec](https://github.com/boschsensortec)

### Plantower (PMSA003I)
- **Distributor:** Adafruit, various Chinese suppliers
- **Technical Support:** Contact through distributors

### DFRobot (SEN0321)
- **Website:** [dfrobot.com](https://www.dfrobot.com)
- **Wiki:** [wiki.dfrobot.com](https://wiki.dfrobot.com)
- **GitHub:** [DFRobot](https://github.com/DFRobot)

### Seeed Studio (Grove MGSV2)
- **Website:** [seeedstudio.com](https://www.seeedstudio.com)
- **Wiki:** [wiki.seeedstudio.com](https://wiki.seeedstudio.com)
- **GitHub:** [Seeed-Studio](https://github.com/Seeed-Studio)

---

## Software and Tools

### Arduino Development

#### PlatformIO
**What it is:** Modern, professional development environment for embedded systems (replaces Arduino IDE)

**Installation:**
```bash
# On Raspberry Pi / Linux
pip3 install platformio

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Official Resources:**
- **Website:** [platformio.org](https://platformio.org)
- **Documentation:** [docs.platformio.org](https://docs.platformio.org)
- **Installation Guide:** [docs.platformio.org/en/latest/core/installation/index.html](https://docs.platformio.org/en/latest/core/installation/index.html)

**Why PlatformIO instead of Arduino IDE:**
- Faster compilation
- Better library management
- Command-line interface (perfect for headless Raspberry Pi)
- Professional project structure
- Built-in unit testing

#### Arduino Libraries Used

All libraries are defined in `platformio.ini`:

```ini
[env:nanoatmega328]
platform = atmelavr
board = nanoatmega328
framework = arduino
lib_deps =
    adafruit/Adafruit SCD30@^1.0.10
    adafruit/Adafruit BME680 Library@^2.0.2
    adafruit/Adafruit SGP30 Sensor@^2.0.0
    adafruit/Adafruit PM25 AQI Sensor@^1.0.6
    dfrobot/DFRobot_OzoneSensor@^1.0.0
    seeed-studio/Seeed Multichannel Gas Sensor@^1.0.0
```

**Library Documentation:**
- [Adafruit SCD30](https://github.com/adafruit/Adafruit_SCD30)
- [Adafruit BME680](https://github.com/adafruit/Adafruit_BME680)
- [Adafruit SGP30](https://github.com/adafruit/Adafruit_SGP30)
- [Adafruit PM25](https://github.com/adafruit/Adafruit_PM25)
- [DFRobot Ozone](https://github.com/DFRobot/DFRobot_OzoneSensor)

---

### Python Data Collection

#### Required Python Packages

Install via pip:
```bash
pip3 install -r requirements.txt
```

**Core Dependencies:**
- `pyserial` - Serial communication with Arduino
- `paho-mqtt` - MQTT publishing
- `pynmea2` - GPS data parsing
- `netifaces` - Network interface information
- `getmac` - MAC address retrieval
- `PyYAML` - Configuration file parsing

---

### Home Assistant

#### Installation Methods

**Method 1: Docker Container (Recommended for this project)**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Run Home Assistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v /home/pi/homeassistant:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

**Official Resources:**
- **Website:** [home-assistant.io](https://www.home-assistant.io)
- **Installation Guide:** [home-assistant.io/installation/](https://www.home-assistant.io/installation/)
- **MQTT Documentation:** [home-assistant.io/integrations/mqtt/](https://www.home-assistant.io/integrations/mqtt/)

#### Mosquitto MQTT Broker

**Installation on Raspberry Pi:**
```bash
sudo apt install mosquitto mosquitto-clients
```

**Official Resources:**
- **Website:** [mosquitto.org](https://mosquitto.org)
- **Documentation:** [mosquitto.org/documentation/](https://mosquitto.org/documentation/)

---

### Fire Tablet Kiosk Mode

#### Fully Kiosk Browser

**IMPORTANT:** Fully Kiosk Browser is **NOT available** on the Amazon Appstore. It must be sideloaded.

**Official Download:**
- **Website:** [fully-kiosk.com](https://www.fully-kiosk.com)
- **Direct APK Download:** [fully-kiosk.com/en/#download](https://www.fully-kiosk.com/en/#download)
- **Specific Download for Fire OS:** [fully-kiosk.com/en/#download](https://www.fully-kiosk.com/en/#download) - Select "Fire OS" version

**Sideloading Instructions:**

1. **Enable Unknown Sources:**
   - Settings → Security & Privacy → Apps from Unknown Sources → Enable

2. **Download APK:**
   - Open Silk Browser on Fire Tablet
   - Navigate to: `https://www.fully-kiosk.com/en/#download`
   - Download "Fully Kiosk Browser for Fire OS"
   - APK file will save to Downloads folder

3. **Install APK:**
   - Open "Docs" app (File Manager)
   - Navigate to Downloads folder
   - Tap the `.apk` file
   - Tap "Install"
   - Grant permissions when prompted

**Alternative Method (using PC):**

1. **Enable ADB on Fire Tablet:**
   - Settings → Device Options → Developer Options
   - Enable "ADB Debugging"

2. **Install ADB on PC:**
   - Download Android Platform Tools: [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools)

3. **Connect and Install:**
   ```bash
   # Connect Fire Tablet via USB
   adb devices
   adb install fully-kiosk-browser.apk
   ```

**Purchase Information:**
- Free version available with limitations
- Plus license: One-time purchase (~$6-7 per device)
- Removes ads and unlocks advanced features

---

## Technical Glossary

### Air Quality Terms

**AQI (Air Quality Index)**
- Standardized scale (0-500) for reporting air quality
- Developed by EPA (US Environmental Protection Agency)
- Higher values = worse air quality
- Categories: Good (0-50), Moderate (51-100), Unhealthy for Sensitive Groups (101-150), Unhealthy (151-200), Very Unhealthy (201-300), Hazardous (301-500)

**PM (Particulate Matter)**
- Tiny particles suspended in air
- PM2.5 = particles ≤2.5 micrometers in diameter
- PM10 = particles ≤10 micrometers in diameter
- Can penetrate deep into lungs and bloodstream

**VOC (Volatile Organic Compounds)**
- Organic chemicals that evaporate at room temperature
- Examples: formaldehyde, benzene, toluene from paints, cleaners, building materials
- Total VOC (TVOC) = sum of all VOCs detected

**NDIR (Non-Dispersive Infrared)**
- Technology for measuring CO2 by detecting infrared absorption
- "Non-dispersive" = uses specific wavelength filter
- Gold standard for CO2 measurement (no drift, highly accurate)

**MOX (Metal Oxide Sensor)**
- Type of gas sensor using metal oxide semiconductor
- Resistance changes when exposed to gases
- Less specific than NDIR, but detects wider range of gases
- Requires warm-up and calibration

**Electrochemical Sensor**
- Measures gas concentration via chemical reaction generating electrical signal
- High specificity for target gas
- Limited lifespan (consumable component)
- Used in O3 sensor (SEN0321)

**eCO2 (Equivalent CO2)**
- Estimated CO2 level calculated from VOC concentration
- NOT real CO2 measurement
- Assumes correlation between VOCs and human occupancy
- Less accurate than NDIR CO2 sensor

**RH (Relative Humidity)**
- Amount of moisture in air as percentage of maximum at that temperature
- Comfortable range: 30-60% RH
- Too low = dry skin, static electricity
- Too high = mold growth, dust mites

**hPa / kPa (Pressure Units)**
- hPa (hectopascal) = 100 Pascals = 1 millibar
- kPa (kilopascal) = 1000 Pascals = 10 hPa
- Standard atmospheric pressure = 1013 hPa = 101.3 kPa

---

### Electronics Terms

**I2C (Inter-Integrated Circuit)**
- Communication protocol for connecting multiple devices
- Uses 2 wires: SDA (data) and SCL (clock)
- Each device has unique address (e.g., 0x61, 0x76)
- Multiple devices share same bus (daisy-chain)

**SDA (Serial Data)**
- Data line in I2C communication
- Arduino Nano: Pin A4

**SCL (Serial Clock)**
- Clock line in I2C communication
- Arduino Nano: Pin A5

**ADC (Analog-to-Digital Converter)**
- Converts analog voltage to digital number
- Arduino Nano has 10-bit ADC (0-1023)
- Used for MQ136 sensor reading

**UART / Serial**
- Communication protocol using TX/RX pins
- Arduino communicates with Raspberry Pi via USB serial
- Baud rate: 9600 in this project

**VCC / VDD**
- Power supply voltage (typically 3.3V or 5V)

**GND (Ground)**
- Common reference point (0V)
- All grounds must be connected together

**Pull-up Resistor**
- Resistor connecting signal line to VCC
- I2C requires pull-up resistors (often built into modules)

---

### Software Terms

**MQTT (Message Queuing Telemetry Transport)**
- Lightweight publish/subscribe messaging protocol
- Broker (Mosquitto) receives and distributes messages
- Topics organize messages (e.g., "utsensing/SCD30")

**JSON (JavaScript Object Notation)**
- Human-readable data format
- Example: `{"temperature": 25.3, "humidity": 45.2}`

**CSV (Comma-Separated Values)**
- Spreadsheet-compatible text format
- Each line = one reading, columns = parameters

**SSH (Secure Shell)**
- Encrypted remote access to Raspberry Pi
- Default: `ssh pi@192.168.1.100`

**Systemd Service**
- Linux background process manager
- Used to auto-start data collection on boot

**Docker Container**
- Isolated environment for running applications
- Home Assistant runs in container

**APK (Android Package)**
- Installation file for Android apps
- Must be sideloaded on Fire tablets

---

## Calibration Procedures

### SCD30 - Automatic Self-Calibration (ASC)

The SCD30 supports automatic baseline correction over time.

**Enable ASC in firmware:**
```cpp
scd30.setAutoSelfCalibration(true);
```

**Important:**
- ASC assumes sensor is regularly exposed to fresh air (~400 ppm CO2)
- If sensor is in continuously occupied space, disable ASC
- Manual calibration: expose to outdoor air for 5 minutes, set as 400 ppm baseline

---

### SGP30 - Baseline Calibration

**Initial 12-Hour Burn-in:**
```python
# Run sensor in clean air for 12 hours
# Then save baseline values
eco2_baseline, tvoc_baseline = sgp30.get_iaq_baseline()
print(f"eCO2 baseline: {eco2_baseline}, TVOC baseline: {tvoc_baseline}")
# Save these values to configuration file
```

**Restore on Startup:**
```python
# Load saved baseline values
sgp30.set_iaq_baseline(eco2_baseline, tvoc_baseline)
```

**Recalibration Schedule:**
- Every 6 months
- When moved to different environment
- If readings seem inaccurate

---

### MQ136 - R0 Calibration

**Required Equipment:**
- Known clean air environment (0 ppm H2S)
- 48+ hours after first power-on

**Procedure:**
```python
import time

# Read ADC value in clean air
adc_values = []
for i in range(100):
    adc_values.append(read_adc())  # Read from A0
    time.sleep(0.1)

raw_value = sum(adc_values) / len(adc_values)

# Calculate R0
LOAD_RESISTANCE = 10000  # 10kΩ
VCC = 5.0
voltage = (raw_value / 1023) * VCC
rs = LOAD_RESISTANCE * (VCC - voltage) / voltage
R0 = rs  # This is your baseline

print(f"R0 calibration value: {R0} Ω")
# Save R0 to configuration file
```

---

## Wiring Diagrams

### Wire Color Reference (Grove I2C Hub to Arduino Nano)

When connecting the Grove I2C Hub to the Arduino Nano, use the following wire color coding:

| Wire Color | Arduino Pin | Function |
|------------|-------------|----------|
| **Black** | GND | Ground |
| **Red** | 5V | Power (5 volts) |
| **Yellow** | A5 | SCL (I2C clock) |
| **White** | A4 | SDA (I2C data) |
| **Green** | A0 | Analog input (MQ136 H2S sensor) |

```
Grove I2C Hub                    Arduino Nano
┌─────────────┐                 ┌─────────────┐
│             │                 │             │
│  Black  ●───┼────────────────►│ GND         │
│  Red    ●───┼────────────────►│ 5V          │
│  Yellow ●───┼────────────────►│ A5 (SCL)    │
│  White  ●───┼────────────────►│ A4 (SDA)    │
│             │                 │             │
└─────────────┘                 │             │
                                │             │
MQ136 Sensor                    │             │
┌─────────────┐                 │             │
│  Green  ●───┼────────────────►│ A0 (Analog) │
│  (signal)   │                 │             │
└─────────────┘                 └─────────────┘
```

**Note:** The green wire for A0 comes from the MQ136 H2S sensor's signal output, not the Grove I2C Hub. The I2C Hub only uses 4 wires (Black, Red, Yellow, White).

### I2C Bus Wiring (All Digital Sensors)

```
Arduino Nano          Grove Hub 1           Sensors
┌──────────┐         ┌──────────┐
│          │         │          │
│  A4 (SDA)├────────►│ SDA      ├────► SCD30 (0x61)
│  A5 (SCL)├────────►│ SCL      ├────► BME680 (0x76)
│    5V    ├────────►│ VCC      │
│    GND   ├────────►│ GND      │
│          │         │          │
└──────────┘         └────┬─────┘
                          │
                          │ Daisy-chain to Hub 2
                          ▼
                    ┌──────────┐
                    │ Hub 2    ├────► SGP30 (0x58)
                    │          ├────► PMSA003I (0x12)
                    └────┬─────┘
                         │
                         │ Daisy-chain to Hub 3
                         ▼
                    ┌──────────┐
                    │ Hub 3    ├────► SEN0321 (0x73)
                    │          ├────► MGSV2 (0x08)
                    └──────────┘
```

### MQ136 Analog Wiring

```
MQ136 Sensor          Arduino Nano
┌──────────┐         ┌──────────┐
│          │         │          │
│   VCC    ├────────►│   5V     │
│   GND    ├────────►│   GND    │
│   AOUT   ├────────►│   A0     │ (Analog input)
│          │         │          │
└──────────┘         └──────────┘

Note: MQ136 may have 10kΩ load resistor onboard.
Check module schematic.
```

### Raspberry Pi/Odroid to Arduino Connection

**Normal Operation Setup:**

The primary connection for normal operation uses a standard USB cable:

```
Raspberry Pi 4 / Odroid C1+     Arduino Nano
┌──────────┐                   ┌──────────┐
│          │                   │          │
│ USB Port ├───────────────────┤ USB Mini │ (5V power + serial data)
│          │  USB Cable        │          │
└──────────┘                   └──────────┘

Serial Settings:
- Baud Rate: 9600
- Data Bits: 8
- Parity: None
- Stop Bits: 1
- Device: /dev/ttyUSB0 (usually)
```

All five sensor cables connect directly to the Arduino breakout board, which then communicates with the Raspberry Pi/Odroid via this USB connection.

---

### UART-to-USB Debug Adapter (Optional)

**What it is:** A separate USB-to-serial adapter for direct Arduino debugging and development.

**Purpose:** The UART-to-USB adapter is **NOT** part of the normal operational setup. It's a development/troubleshooting tool for:

1. **Direct Arduino monitoring** - Connect the adapter to a computer to view serial output from the Arduino in real-time without going through the Raspberry Pi/Odroid
2. **Independent Arduino testing** - Test the Arduino and sensors separately from the main system
3. **Firmware programming** - Alternative method to upload Arduino code directly via USB (in addition to programming through the Odroid)
4. **Debugging** - If the Odroid USB connection fails, you can still access the Arduino directly via this adapter

**Typical setup:**
- Arduino TX pin → UART adapter RX
- Arduino RX pin → UART adapter TX
- Arduino GND → UART adapter GND
- Adapter connects to computer via USB

This adapter came as part of the original MINTS directions and sits dormant in normal operation, available for troubleshooting if needed.

---

## I2C Address Reference Table

| Sensor | Default Address | Alternative | Notes |
|--------|-----------------|-------------|-------|
| SCD30 | 0x61 | None | Fixed address |
| BME680 | 0x76 | 0x77 | Selectable via SDO pin |
| SGP30 | 0x58 | None | Fixed address |
| PMSA003I | 0x12 | None | Fixed address |
| SEN0321 | 0x73 | None | Fixed address |
| MGSV2 | 0x08 | None | Fixed address |

**Scan I2C Bus:**
```bash
i2cdetect -y 1
```

Expected output:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- 08 -- -- -- -- -- -- -- --
10:          -- -- 12 -- -- -- -- -- -- -- -- -- -- -- -- --
20:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50:          -- -- -- -- -- -- -- -- 58 -- -- -- -- -- -- --
60:          -- 61 -- -- -- -- -- -- -- -- -- -- -- -- -- --
70:          -- -- -- 73 -- -- 76 --
```

---

## Real-Time Clock (RTC) Battery Backup

### CR1220 Battery Pack with JST Connector

The system includes an **RTC (Real-Time Clock) battery backup** to maintain accurate system time even when the Raspberry Pi/Odroid is powered off.

**Component Details:**

| Specification | Details |
|---------------|---------|
| **Battery Type** | CR1220 Lithium Coin Cell |
| **Nominal Voltage** | 3.0V |
| **Configuration** | Pre-assembled battery pack with JST connector |
| **Physical Description** | Coin battery wrapped in black insulation tape with two color-coded wires (red = positive, black = negative) ending in a small plastic JST connector |
| **Connector Type** | JST XH (or similar 2-pin connector) plugs directly into RTC module |
| **Purpose** | Maintains accurate date/time through power cycles for CSV logging and MQTT timestamps |

**Why it matters:**
- Without RTC backup power, the system loses accurate time when powered off
- This breaks timestamp accuracy in CSV files (organized by date)
- MQTT data loses accurate timestamps
- Sensor readings become untrustable for time-series analysis

**Testing the Battery:**

Use a multimeter to check voltage:

1. Set multimeter to **DC Voltage (V with straight line)**
2. Carefully touch **red probe to red wire** (positive)
3. Touch **black probe to black wire** (negative)
4. Read the voltage:
   - **2.5V or higher** = Battery is good
   - **2.0-2.5V** = Getting weak, replace soon
   - **Below 2.0V** = Dead, replace immediately

**Replacing the Battery:**

1. **What to order:**
   - Search for: **"CR1220 battery pack JST connector"** or **"RTC battery module CR1220"**
   - Cost: Usually $2-5 per unit
   - Sources: Amazon, Adafruit, electronics suppliers
   - Buy 2-3 extras to keep in your parts kit

2. **Installation:**
   - Gently unplug the connector from the RTC module
   - Plug in the new battery pack
   - No soldering required

3. **Storage:**
   - Lithium coin batteries remain functional for ~10 years when stored dry
   - Keep spare batteries in a dry place away from moisture

**Expected Battery Life:**
- Typical CR1220 coin cell: 5-10 years (when not actively discharging)
- Check annually if the system is dormant for extended periods

---

## Health and Safety References

### CO2 Exposure Limits
- **OSHA PEL:** 5,000 ppm (8-hour TWA)
- **NIOSH REL:** 5,000 ppm (10-hour TWA)
- **ACGIH TLV:** 5,000 ppm (8-hour TWA)
- **Cognitive impairment begins:** ~1,000 ppm

### PM2.5 Standards
- **WHO 24-hour guideline (2021):** 15 μg/m³
- **WHO annual guideline (2021):** 5 μg/m³
- **US EPA 24-hour standard:** 35 μg/m³
- **US EPA annual standard:** 12 μg/m³

### VOC Guidelines
- **German Federal Environment Agency:**
  - <0.3 mg/m³ (65 ppb): No concern
  - 0.3-1 mg/m³ (65-220 ppb): Acceptable
  - 1-3 mg/m³ (220-660 ppb): Some concern
  - 3-10 mg/m³ (660-2200 ppb): Major concern
  - >10 mg/m³ (>2200 ppb): Unacceptable

### H2S Exposure Limits
- **OSHA PEL:** 20 ppm (ceiling, acceptable maximum peak)
- **NIOSH REL:** 10 ppm (10-minute ceiling)
- **IDLH:** 100 ppm (Immediately Dangerous to Life or Health)
- **Olfactory paralysis:** 100-150 ppm (can't smell it!)
- **Fatal:** 500-1000 ppm (30 minutes)

**References:**
- [OSHA Occupational Exposure Limits](https://www.osha.gov/annotated-pels)
- [WHO Air Quality Guidelines](https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines)
- [EPA Air Quality Standards](https://www.epa.gov/criteria-air-pollutants/naaqs-table)

---

## Sources

This technical reference was compiled from:
- [Sensirion SCD30 Datasheet](https://sensirion.com/media/documents/4EAF6AF8/61652C3C/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)
- [Bosch BME680 Datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- [Plantower PMSA003I Datasheet](https://www.mouser.com/datasheet/2/737/4505_PMSA003I_series_data_manual_English_V2_6-2489521.pdf)
- [Adafruit Learning Guides](https://learn.adafruit.com/)
- [Fully Kiosk Browser Official Site](https://www.fully-kiosk.com)
- [PlatformIO Documentation](https://docs.platformio.org)
- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- WHO, EPA, OSHA official guidelines

**Last verified:** 2025-12-22

---

**END OF TECHNICAL REFERENCE APPENDIX**
