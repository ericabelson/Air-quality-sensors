# Shared Setup Modules

These modules contain reusable setup instructions referenced by the main guides.

## When to Use These

You generally don't need to read these directly. They are referenced from:

- [Raspberry Pi Setup](../RASPBERRY_PI_SETUP.md)
- [Home Assistant Setup](../HOME_ASSISTANT_SETUP.md)
- [Alternative Sensors Setup](../ALTERNATIVE_SENSORS_SETUP.md)

## Available Modules

| Module | Description |
|--------|-------------|
| [Docker & Home Assistant](DOCKER_HOME_ASSISTANT.md) | Installing Docker and Home Assistant Container |
| [MQTT Setup](MQTT_SETUP.md) | Installing Mosquitto and configuring MQTT |
| [PlatformIO & Arduino](PLATFORMIO_ARDUINO.md) | Installing PlatformIO and flashing Arduino firmware |

## Why Modules?

These common setup steps appear in multiple guides. By extracting them into modules:

1. **Less duplication** - Changes only need to be made once
2. **Easier maintenance** - Single source of truth
3. **Clearer guides** - Main guides can focus on their specific purpose
