# UTSensing Air Quality Monitoring System

A comprehensive, open-source air quality monitoring platform for collecting, processing, and visualizing environmental data from multiple sensors in real-time.

---

## Which Setup Path Should I Follow?

Use this decision tree to find the right guide for your situation:

```
START HERE
    │
    ▼
Do you have the Arduino Nano + sensor kit?
    │
    ├── YES ──► Do you want the full step-by-step guide?
    │               │
    │               ├── YES ──► Follow the FULL SETUP PATH below
    │               │
    │               └── NO (experienced) ──► See Quick Reference Commands
    │
    └── NO ──► Do you have other sensors (Aranet 4, door sensors, etc.)?
                    │
                    ├── YES ──► Follow the ALTERNATIVE SETUP PATH below
                    │
                    └── NO ──► You can still set up Home Assistant!
                               See Alternative Setup Path
```

---

## Setup Paths

### Full Setup Path (Arduino + All Sensors)

**Total Time:** 2-3 hours | **Difficulty:** Beginner-friendly

| Step | Guide | Time | Description |
|------|-------|------|-------------|
| 1 | [Raspberry Pi Setup](docs/RASPBERRY_PI_SETUP.md) | 90 min | Hardware assembly, OS install, sensor configuration |
| 2 | [Home Assistant Setup](docs/HOME_ASSISTANT_SETUP.md) | 45 min | Dashboard installation and sensor integration |
| 3 | [Fire Tablet Setup](docs/FIRE_TABLET_SETUP.md) | 30 min | *Optional:* Dedicated wall display |

### Alternative Setup Path (No Arduino Kit)

**Total Time:** 1-2 hours | **Difficulty:** Beginner-friendly

Start monitoring air quality with sensors you already have:

| Step | Guide | Time | Description |
|------|-------|------|-------------|
| 1 | [Alternative Sensors Setup](docs/ALTERNATIVE_SENSORS_SETUP.md) | 60 min | Aranet 4, door sensors, any Home Assistant-compatible device |
| 2 | [Fire Tablet Setup](docs/FIRE_TABLET_SETUP.md) | 30 min | *Optional:* Dedicated wall display |

**Note:** You can add the Arduino sensor kit later - the system is designed to expand.

---

## Documentation

### Setup Guides

| Guide | When to Use |
|-------|-------------|
| [Raspberry Pi Setup](docs/RASPBERRY_PI_SETUP.md) | Building the full Arduino sensor system |
| [Alternative Sensors Setup](docs/ALTERNATIVE_SENSORS_SETUP.md) | Using Aranet 4, door sensors, or starting without Arduino |
| [Home Assistant Setup](docs/HOME_ASSISTANT_SETUP.md) | Configuring the dashboard after hardware is ready |
| [Fire Tablet Setup](docs/FIRE_TABLET_SETUP.md) | Setting up a dedicated display |
| [WS3000 Weather Station](docs/WS3000_SETUP.md) | Adding Ambient Weather station via USB |

### Reference

| Guide | Description |
|-------|-------------|
| [Technical Reference](docs/TECHNICAL_REFERENCE.md) | Sensor datasheets, wiring diagrams, calibration procedures |
| [Sensor Interpretation](docs/SENSOR_INTERPRETATION.md) | Understanding what the readings mean |

### Security & Advanced

| Guide | Description |
|-------|-------------|
| [Security Guide](docs/SECURITY.md) | Hardening your installation |
| [Remote Access](docs/REMOTE_ACCESS.md) | Accessing your dashboard from anywhere |
| [Windows SSH Setup](docs/WINDOWS_SSH_SETUP.md) | SSH key setup for Windows users |

### Shared Setup Modules

These are referenced by the main guides. You usually don't need to read these directly:

| Module | Description |
|--------|-------------|
| [Docker & Home Assistant](docs/setup/DOCKER_HOME_ASSISTANT.md) | Container installation |
| [MQTT Setup](docs/setup/MQTT_SETUP.md) | Message broker configuration |
| [PlatformIO & Arduino](docs/setup/PLATFORMIO_ARDUINO.md) | Arduino firmware flashing |

---

## System Overview

### What It Monitors

| Category | Measurements |
|----------|--------------|
| **Air Quality** | PM1, PM2.5, PM10 particulate matter |
| **Gases** | CO2, CO, NO2, O3, H2S, VOCs, Ethanol |
| **Environment** | Temperature, Humidity, Pressure |
| **Location** | GPS coordinates (for mobile deployments) |

### How It Works

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
│            └───────────────┬─────────────────┘                 │
└────────────────────────────┼────────────────────────────────────┘
                             │ USB Serial
┌────────────────────────────┼────────────────────────────────────┐
│            ┌───────────────┴───────────────┐                    │
│            │       Raspberry Pi 4          │                    │
│            └───────────────┬───────────────┘                    │
│         ┌──────────────────┼──────────────────┐                 │
│         ▼                  ▼                  ▼                 │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│   │ CSV Files│      │   MQTT   │      │Home Asst │             │
│   │ (Storage)│      │ (Bridge) │      │(Dashboard)│             │
│   └──────────┘      └──────────┘      └─────┬────┘             │
│                                             │                   │
│                                       ┌─────▼─────┐             │
│                                       │Fire Tablet│             │
│                                       │ (Display) │             │
│                                       └───────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware Requirements

### Full Sensor Kit

| Component | Purpose |
|-----------|---------|
| Raspberry Pi 4 (4GB+) | Main processing unit |
| Arduino Nano | Sensor data collection |
| SCD30 | CO2, Temperature, Humidity |
| BME680 | Temp, Pressure, Humidity, VOC |
| SGP30 | TVOC, eCO2 |
| PMSA003I | Particulate Matter |
| SEN0321 | Ozone |
| MGSV2 | NO2, Ethanol, VOC, CO |
| MQ136 | H2S |
| Grove I2C Hubs (3) | Sensor connections |

See [Technical Reference](docs/TECHNICAL_REFERENCE.md) for complete parts list with purchase links.

### Alternative Sensors (No Arduino Needed)

- **Aranet 4** - Bluetooth CO2 monitor (~$250)
- **Zigbee door/window sensors** - Aqara, Sonoff (~$15 each)
- **Any Home Assistant-compatible sensor**

---

## Quick Reference

### Essential Commands

```bash
# Check sensor service status
sudo systemctl status utsensing

# View live sensor logs
journalctl -u utsensing -f

# Restart sensor service
sudo systemctl restart utsensing

# Check Home Assistant
docker ps
docker logs homeassistant

# Test MQTT
mosquitto_sub -h localhost -t "utsensing/#" -v
```

### Key Directories

| Path | Contents |
|------|----------|
| `/home/pi/utData/raw/` | CSV sensor data |
| `/home/pi/homeassistant/` | Home Assistant config |
| `~/Air-quality-sensors/` | Project repository |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Arduino not detected | Check USB cable, verify with `ls /dev/ttyUSB*` |
| Sensor shows "not found" | Check I2C connections: `i2cdetect -y 1` |
| No data in CSV files | Verify service: `sudo systemctl status utsensing` |
| MQTT not connecting | Check broker: `sudo systemctl status mosquitto` |
| Dashboard empty | Wait 1-2 minutes, verify MQTT integration |

---

## Project Structure

```
Air-quality-sensors/
├── README.md                 # This file
├── docs/
│   ├── RASPBERRY_PI_SETUP.md    # Hardware setup
│   ├── HOME_ASSISTANT_SETUP.md  # Dashboard setup
│   ├── FIRE_TABLET_SETUP.md     # Display setup
│   ├── ALTERNATIVE_SENSORS_SETUP.md  # Non-Arduino sensors
│   ├── TECHNICAL_REFERENCE.md   # Specs & datasheets
│   ├── SENSOR_INTERPRETATION.md # Reading explanations
│   ├── SECURITY.md              # Security hardening
│   ├── REMOTE_ACCESS.md         # External access
│   └── setup/                   # Shared setup modules
│       ├── DOCKER_HOME_ASSISTANT.md
│       ├── MQTT_SETUP.md
│       └── PLATFORMIO_ARDUINO.md
├── firmware/
│   ├── airNano/              # Arduino firmware
│   └── xu4Mqqt/              # Raspberry Pi scripts
├── homeassistant/            # Dashboard configs
└── scripts/                  # Utility scripts
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-sensor`)
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Links

- [GitHub Repository](https://github.com/ericabelson/Air-quality-sensors)
- [Report Issues](https://github.com/ericabelson/Air-quality-sensors/issues)
