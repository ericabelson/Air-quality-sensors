# UTSensing Air Quality Monitoring System

A comprehensive, open-source air quality monitoring platform for collecting, processing, and visualizing environmental data from multiple sensors in real-time.

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Sensors](#supported-sensors)
3. [System Architecture](#system-architecture)
4. [Hardware Requirements](#hardware-requirements)
5. [Quick Start](#quick-start)
6. [Documentation](#documentation)
7. [Data Interpretation](#data-interpretation)
8. [Home Assistant Integration](#home-assistant-integration)
9. [Troubleshooting](#troubleshooting)
10. [License](#license)

---

## Overview

UTSensing provides real-time monitoring of:

- **Air Quality**: PM1, PM2.5, PM10 particulate matter
- **Gases**: CO2, CO, NO2, O3, H2S, VOCs, Ethanol
- **Environment**: Temperature, Humidity, Pressure
- **Location**: GPS coordinates (for mobile deployments)

**Key Features:**
- Modular sensor architecture - add or remove sensors easily
- Real-time data logging to CSV and JSON
- MQTT support for cloud integration
- Home Assistant compatible for smart home dashboards
- Extensible design for additional sensors (door sensors, motion, etc.)

---

## Supported Sensors

| Sensor | Model | Parameters | Units | Health Relevance |
|--------|-------|------------|-------|------------------|
| **CO2 Sensor** | SCD30 | CO2, Temperature, Humidity | ppm, °C, %RH | Indoor air quality indicator |
| **Environmental** | BME680 | Temperature, Pressure, Humidity, VOC Gas Resistance | °C, kPa, %RH, kΩ | Weather & air quality |
| **VOC/eCO2** | SGP30 | TVOC, eCO2, Raw H2, Raw Ethanol | ppb, ppm, raw | Indoor pollution |
| **Multi-Gas** | MGSV2 | NO2, Ethanol, VOC, CO | ppm | Harmful gas detection |
| **Ozone** | SEN0321 | O3 | ppb | Outdoor air quality |
| **Particulate Matter** | PMSA003I | PM1, PM2.5, PM10, Particle bins (0.3-10μm) | μg/m³, count/dL | Respiratory health |
| **Hydrogen Sulfide** | MQ136 | H2S | Raw ADC (convertible to ppm) | Toxic gas detection |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SENSOR LAYER                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  SCD30  │ │ BME680  │ │  SGP30  │ │ PMSA003I│ │ SEN0321 │   │
│  │  (CO2)  │ │ (Env)   │ │ (VOC)   │ │  (PM)   │ │  (O3)   │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       └──────────┬┴──────────┬┴──────────┬┴──────────┬┘        │
│                  │    I2C Bus           │                       │
│            ┌─────┴─────────────────────┴─────┐                 │
│            │        Arduino Nano             │                 │
│            │    (Sensor Data Collection)     │                 │
│            └───────────────┬─────────────────┘                 │
└────────────────────────────┼────────────────────────────────────┘
                             │ Serial (USB) @ 9600 baud
┌────────────────────────────┼────────────────────────────────────┐
│                            │                                     │
│            ┌───────────────┴───────────────┐                    │
│            │   Raspberry Pi 4 / Odroid C1+ │                    │
│            │    (Data Processing Unit)     │                    │
│            └───────────────┬───────────────┘                    │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         ▼                  ▼                  ▼                 │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│   │ CSV Files│      │   JSON   │      │   MQTT   │             │
│   │ (Storage)│      │ (Latest) │      │ (Cloud)  │             │
│   └──────────┘      └────┬─────┘      └──────────┘             │
│                          │                                      │
│                          ▼                                      │
│                   ┌──────────────┐                              │
│                   │Home Assistant│──────► Fire Tablet           │
│                   │  Dashboard   │        (Display)             │
│                   └──────────────┘                              │
│                    PROCESSING LAYER                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware Requirements

### Complete Parts List

#### Main Processing Unit
| Component | Quantity | Purpose |
|-----------|----------|---------|
| Raspberry Pi 4 (4GB+) OR Odroid C1+ | 1 | Main data processing |
| 32GB+ MicroSD Card (Class 10) | 1 | OS and data storage |
| USB Power Supply (5V 3A) | 1 | Power for Pi |
| Micro USB Cable (A-Mini A, 1ft) | 1 | Arduino connection |

#### Sensor Interface
| Component | Quantity | Purpose |
|-----------|----------|---------|
| Arduino Nano (ATmega328P) | 1 | Sensor data collection |
| Arduino Nano Base/Shield | 1 | Easy sensor connections |
| Grove I2C Hub | 3 | Sensor bus expansion |
| RTC Battery (CR1220) | 1 | Timekeeping backup |

#### Sensors
| Sensor | Quantity | Measures |
|--------|----------|----------|
| SCD30 | 1 | CO2, Temperature, Humidity |
| BME680 | 1 | Temp, Pressure, Humidity, VOC |
| SGP30 | 1 | TVOC, eCO2 |
| MGSV2 (Multichannel Gas) | 1 | NO2, Ethanol, VOC, CO |
| SEN0321 | 1 | Ozone |
| PMSA003I | 1 | Particulate Matter |
| MQ136 | 1 | H2S |

#### Housing & Mounting
| Component | Quantity | Purpose |
|-----------|----------|---------|
| 3D Printed Base | 1 | Component mounting |
| Poly Case Box with Screws | 1 | Weather protection |
| Solar Radiation Shield (Accurite) | 1 | Sensor protection |
| M3 x 20mm Screws | 20 | Assembly |
| M2 x 20mm Screws | 20 | Assembly |

#### Power (Optional - Mobile/Outdoor)
| Component | Quantity | Purpose |
|-----------|----------|---------|
| Rosewill RBPB-20010 Battery | 1 | Portable power |

---

## Quick Start

### Option A: I want to set up everything from scratch
See [Complete Raspberry Pi 4 Setup Guide](docs/RASPBERRY_PI_SETUP.md)

### Option B: I have the hardware assembled, need software only

**IMPORTANT:** Read [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md) first for verified sensor specifications and software installation details.

```bash
# 1. Clone the repository
git clone https://github.com/ericabelson/Air-quality-sensors.git
cd Air-quality-sensors

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Install PlatformIO (for Arduino programming)
pip3 install platformio
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Flash Arduino Nano firmware
cd firmware/airNano
pio run -t upload

# 5. Start data collection
cd ../xu4Mqqt
./runAll.sh
```

**See [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md) for:**
- Official sensor datasheets with download links
- PlatformIO installation troubleshooting
- I2C wiring diagrams
- Calibration procedures

### Option C: I want to view data on a dashboard
See [Home Assistant Dashboard Setup](docs/HOME_ASSISTANT_SETUP.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md) | **START HERE** - Sensor datasheets, specifications, and verified technical details |
| [RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md) | Complete step-by-step Raspberry Pi 4 setup |
| [SENSOR_INTERPRETATION.md](docs/SENSOR_INTERPRETATION.md) | Understanding sensor data with formulas |
| [HOME_ASSISTANT_SETUP.md](docs/HOME_ASSISTANT_SETUP.md) | Dashboard and Home Assistant integration |
| [REMOTE_ACCESS.md](docs/REMOTE_ACCESS.md) | Access your dashboard from anywhere (Nabu Casa, Tailscale, Cloudflare) |
| [FIRE_TABLET_SETUP.md](docs/FIRE_TABLET_SETUP.md) | Using Amazon Fire tablet as display |
| [QUICKSTART.md](docs/QUICKSTART.md) | Fast-track setup guide |

---

## Data Interpretation

### What Do the Numbers Mean?

The system converts raw sensor readings into human-interpretable values:

#### Air Quality Index (PM2.5)

| PM2.5 (μg/m³) | AQI | Category | Health Implications |
|---------------|-----|----------|---------------------|
| 0-12 | 0-50 | Good | Air quality is satisfactory |
| 12.1-35.4 | 51-100 | Moderate | Acceptable; sensitive groups may experience symptoms |
| 35.5-55.4 | 101-150 | Unhealthy for Sensitive | Sensitive groups should limit outdoor exertion |
| 55.5-150.4 | 151-200 | Unhealthy | Everyone may begin to experience health effects |
| 150.5-250.4 | 201-300 | Very Unhealthy | Health alert; everyone may experience serious effects |
| 250.5+ | 301-500 | Hazardous | Emergency conditions; entire population affected |

#### CO2 Levels (Indoor Air Quality)

| CO2 (ppm) | Status | Meaning |
|-----------|--------|---------|
| 400-600 | Excellent | Outdoor-like fresh air |
| 600-1000 | Good | Well-ventilated space |
| 1000-1500 | Fair | Ventilation needed |
| 1500-2500 | Poor | Drowsiness may occur |
| 2500+ | Bad | Headaches, poor concentration |

See [SENSOR_INTERPRETATION.md](docs/SENSOR_INTERPRETATION.md) for complete formulas and conversion details.

---

## Home Assistant Integration

This system integrates with Home Assistant for beautiful dashboards viewable on any device:

```yaml
# Example sensor configuration
sensor:
  - platform: mqtt
    name: "Living Room CO2"
    state_topic: "airquality/scd30/co2"
    unit_of_measurement: "ppm"
    icon: mdi:molecule-co2
```

Features:
- Real-time sensor data display
- 3-day historical graphs
- Color-coded air quality indicators
- Mobile-friendly interface
- Fire tablet kiosk mode support

See [HOME_ASSISTANT_SETUP.md](docs/HOME_ASSISTANT_SETUP.md) for complete setup.

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Arduino not detected | Check USB cable, verify COM port with `ls /dev/ttyUSB*` |
| Sensor shows "not found" | Verify I2C connections, check with `i2cdetect -y 1` |
| No data in CSV files | Check permissions on data folder, verify serial connection |
| MQTT not connecting | Verify broker address and credentials in `mintsDefinitions.py` |

### Diagnostic Commands

```bash
# Check if Arduino is connected
ls /dev/ttyUSB*

# Scan I2C bus for sensors
i2cdetect -y 1

# View real-time serial output
screen /dev/ttyUSB0 9600

# Check running processes
ps aux | grep Reader
```

---

## Project Structure

```
Air-quality-sensors/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── docs/                     # Documentation
│   ├── RASPBERRY_PI_SETUP.md
│   ├── SENSOR_INTERPRETATION.md
│   ├── HOME_ASSISTANT_SETUP.md
│   ├── REMOTE_ACCESS.md
│   ├── FIRE_TABLET_SETUP.md
│   └── QUICKSTART.md
├── firmware/
│   ├── airNano/              # Arduino Nano firmware
│   │   ├── src/main.cpp      # Main sensor loop
│   │   ├── lib/              # Sensor libraries
│   │   └── platformio.ini    # Build configuration
│   └── xu4Mqqt/              # Python data collectors
│       ├── runAll.sh         # Startup script
│       ├── nanoReader.py     # Serial data reader
│       ├── GPSReader.py      # GPS data reader
│       └── mintsXU4/         # Python modules
├── homeassistant/            # Home Assistant configs
│   ├── configuration.yaml
│   └── dashboards/
└── 3DPrints/                 # Housing CAD files
```

---

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-sensor`)
3. Commit your changes (`git commit -am 'Add new sensor support'`)
4. Push to the branch (`git push origin feature/new-sensor`)
5. Create a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License
Copyright (c) 2021 MINTS
```

---

## Acknowledgments

- Multi-scale Integrated Sensing and Simulation (MINTS) group at UT Dallas
- Lakitha Omal Harindha Wijeratne - Original author
- All contributors and the open-source community

---

## Links

- [GitHub Repository](https://github.com/ericabelson/Air-quality-sensors)
- [Report Issues](https://github.com/ericabelson/Air-quality-sensors/issues)
