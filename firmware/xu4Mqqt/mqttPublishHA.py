#!/usr/bin/env python3
"""
MQTT Publisher for Home Assistant Integration

This script reads sensor JSON files and publishes them to an MQTT broker
in a format suitable for Home Assistant auto-discovery.

Usage:
    python3 mqttPublishHA.py

Configuration:
    Edit the settings below or set environment variables:
    - MQTT_BROKER: MQTT broker address (default: localhost)
    - MQTT_PORT: MQTT broker port (default: 1883)
    - DATA_FOLDER: Path to sensor data folder
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Run: pip3 install paho-mqtt")
    sys.exit(1)

# =============================================================================
# Configuration
# =============================================================================

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

DATA_FOLDER = os.environ.get("DATA_FOLDER", "/home/utsensing/utData/raw")
PUBLISH_INTERVAL = 10  # seconds

# MQTT Topics
TOPIC_PREFIX = "utsensing"
DISCOVERY_PREFIX = "homeassistant"

# Sensors to publish
SENSORS = [
    "SCD30",
    "BME680",
    "SGP30",
    "PMSA003I",
    "SEN0321",
    "MGSV2",
    "MQ136",
]

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MQTT Client
# =============================================================================

class SensorPublisher:
    """Publishes sensor data to MQTT broker."""

    def __init__(self, broker: str, port: int, username: str = "", password: str = ""):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()

        if username and password:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.connected = False
        self.mac_address = self._get_mac_address()

    def _get_mac_address(self) -> str:
        """Get the MAC address for device identification."""
        try:
            from getmac import get_mac_address
            mac = get_mac_address()
            if mac:
                return mac.replace(":", "")
        except Exception:
            pass

        # Fallback: try reading from network interface
        for interface in ["eth0", "wlan0", "enp1s0"]:
            path = f"/sys/class/net/{interface}/address"
            if os.path.exists(path):
                with open(path) as f:
                    return f.read().strip().replace(":", "")

        return "unknown"

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
            self._publish_discovery()
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        logger.warning("Disconnected from MQTT broker")
        self.connected = False

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def _publish_discovery(self):
        """Publish Home Assistant MQTT discovery messages."""
        device_info = {
            "identifiers": [f"utsensing_{self.mac_address}"],
            "name": "UTSensing Air Quality Monitor",
            "model": "UTSensing v1",
            "manufacturer": "MINTS",
        }

        # SCD30 sensors
        self._publish_sensor_discovery("co2", "CO2", "ppm", "carbon_dioxide",
                                       "SCD30", device_info)
        self._publish_sensor_discovery("temperature", "Temperature", "°C", "temperature",
                                       "SCD30", device_info)
        self._publish_sensor_discovery("humidity", "Humidity", "%", "humidity",
                                       "SCD30", device_info)

        # BME680 sensors
        self._publish_sensor_discovery("pressure", "Pressure", "hPa", "pressure",
                                       "BME680", device_info)
        self._publish_sensor_discovery("gas", "Gas Resistance", "kΩ", None,
                                       "BME680", device_info)

        # SGP30 sensors
        self._publish_sensor_discovery("TVOC", "TVOC", "ppb", "volatile_organic_compounds_parts",
                                       "SGP30", device_info)
        self._publish_sensor_discovery("eCO2", "eCO2", "ppm", None,
                                       "SGP30", device_info)

        # PMSA003I sensors
        self._publish_sensor_discovery("pm1Env", "PM1", "μg/m³", "pm1",
                                       "PMSA003I", device_info)
        self._publish_sensor_discovery("pm2p5Env", "PM2.5", "μg/m³", "pm25",
                                       "PMSA003I", device_info)
        self._publish_sensor_discovery("pm10Env", "PM10", "μg/m³", "pm10",
                                       "PMSA003I", device_info)

        # SEN0321 sensors
        self._publish_sensor_discovery("Ozone", "Ozone", "ppb", "ozone",
                                       "SEN0321", device_info)

        # MGSV2 sensors
        self._publish_sensor_discovery("CO", "Carbon Monoxide", "ppm", "carbon_monoxide",
                                       "MGSV2", device_info)
        self._publish_sensor_discovery("NO2", "Nitrogen Dioxide", "ppm", "nitrogen_dioxide",
                                       "MGSV2", device_info)

        logger.info("Published Home Assistant discovery messages")

    def _publish_sensor_discovery(self, field: str, name: str, unit: str,
                                  device_class: Optional[str], sensor_name: str,
                                  device_info: Dict):
        """Publish discovery message for a single sensor."""
        unique_id = f"utsensing_{self.mac_address}_{sensor_name}_{field}"
        topic = f"{DISCOVERY_PREFIX}/sensor/{unique_id}/config"

        config = {
            "name": f"Air Quality {name}",
            "unique_id": unique_id,
            "state_topic": f"{TOPIC_PREFIX}/{sensor_name}",
            "value_template": f"{{{{ value_json.{field} }}}}",
            "unit_of_measurement": unit,
            "device": device_info,
        }

        if device_class:
            config["device_class"] = device_class

        self.client.publish(topic, json.dumps(config), retain=True)

    def publish_sensor_data(self, sensor_name: str, data: Dict):
        """Publish sensor data to MQTT."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return

        topic = f"{TOPIC_PREFIX}/{sensor_name}"
        payload = json.dumps(data)
        self.client.publish(topic, payload)
        logger.debug(f"Published to {topic}: {payload}")

    def read_sensor_json(self, sensor_name: str) -> Optional[Dict]:
        """Read sensor data from JSON file."""
        # Find the MAC address folder
        data_path = Path(DATA_FOLDER)
        if not data_path.exists():
            return None

        # Look for JSON file in MAC address subdirectories
        for mac_folder in data_path.iterdir():
            if mac_folder.is_dir():
                json_file = mac_folder / f"{sensor_name}.json"
                if json_file.exists():
                    try:
                        with open(json_file) as f:
                            return json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        logger.error(f"Error reading {json_file}: {e}")

        return None

    def publish_all_sensors(self):
        """Read and publish all sensor data."""
        for sensor_name in SENSORS:
            data = self.read_sensor_json(sensor_name)
            if data:
                self.publish_sensor_data(sensor_name, data)
            else:
                logger.debug(f"No data found for sensor: {sensor_name}")


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point."""
    logger.info("Starting UTSensing MQTT Publisher")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Data Folder: {DATA_FOLDER}")

    publisher = SensorPublisher(
        MQTT_BROKER, MQTT_PORT,
        MQTT_USERNAME, MQTT_PASSWORD
    )

    try:
        publisher.connect()

        # Wait for connection
        time.sleep(2)

        while True:
            publisher.publish_all_sensors()
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()
