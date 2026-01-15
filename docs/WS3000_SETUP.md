# Ambient Weather WS 3000 X5 Setup Guide

Connect your Ambient Weather WS 3000 X5 wireless thermo-hygrometer to Home Assistant via USB - fully local, no cloud required.

**Time Required:** 30 minutes
**Prerequisites:** Raspberry Pi with Home Assistant running

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Install System Dependencies](#install-system-dependencies)
4. [Set Up USB Permissions](#set-up-usb-permissions)
5. [Install Node.js Library](#install-nodejs-library)
6. [Test USB Connection](#test-usb-connection)
7. [Install MQTT Broker](#install-mqtt-broker)
8. [Create MQTT Publishing Script](#create-mqtt-publishing-script)
9. [Set Up Automatic Startup](#set-up-automatic-startup)
10. [Configure Home Assistant](#configure-home-assistant)
11. [Power Loss Recovery](#power-loss-recovery)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The Ambient Weather WS 3000 X5 is a wireless thermo-hygrometer console that can receive data from up to 8 remote temperature/humidity sensors. While it's designed to send data to Ambient Weather's cloud service, it also has a USB port for direct data access.

This guide sets up a fully local integration:

```
┌─────────────────┐     USB      ┌─────────────────┐
│  WS 3000 X5     │─────────────►│  Raspberry Pi   │
│    Console      │              │                 │
└─────────────────┘              │  ┌───────────┐  │
                                 │  │  Node.js  │  │
┌─────────────────┐     RF       │  │  Script   │  │
│ Remote Sensors  │─────────────►│  └─────┬─────┘  │
│   (1-8 units)   │   915 MHz    │        │ MQTT   │
└─────────────────┘              │  ┌─────▼─────┐  │
                                 │  │ Mosquitto │  │
                                 │  └─────┬─────┘  │
                                 │        │        │
                                 │  ┌─────▼─────┐  │
                                 │  │   Home    │  │
                                 │  │ Assistant │  │
                                 │  └───────────┘  │
                                 └─────────────────┘
```

### What You Get

- Temperature and humidity from up to 8 remote sensors
- Data updates every 60 seconds
- Fully local - no cloud, no internet required
- Automatic recovery after power loss

---

## Hardware Requirements

| Item | Notes |
|------|-------|
| Ambient Weather WS 3000 X5 | Console with USB port |
| USB Cable | USB-A to Mini-B (included with console) |
| Remote Sensors | Up to 8 thermo-hygrometer sensors |
| Raspberry Pi | Any model with USB port |

---

## Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y build-essential git libusb-dev libudev-dev nodejs npm
```

---

## Set Up USB Permissions

Create a udev rule so the Pi can access the WS 3000 without root:

```bash
sudo nano /etc/udev/rules.d/50-ws3000.rules
```

Add this single line:

```
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5750", SUBSYSTEMS=="usb", ACTION=="add", MODE="0666", GROUP="plugdev"
```

Save and reload:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Install Node.js Library

```bash
mkdir -p ~/ws3000
cd ~/ws3000
npm init -y
npm install EpicVoyage/ambientweather-ws3000
npm install mqtt
```

---

## Test USB Connection

Connect the WS 3000 X5 to your Pi via USB, then test:

```bash
cd ~/ws3000
node -e "
const ws3000 = require('ambientweather-ws3000');
ws3000.query().then(sensors => {
  for (let x = 1; x <= 8; x++) {
    if (sensors[x].active) {
      console.log('Sensor ' + x + ': ' + sensors[x].temperature + '°C, ' + sensors[x].humidity + '%');
    }
  }
});
"
```

You should see output like:

```
Sensor 1: 22.1°C, 71%
Sensor 2: 21.0°C, 85%
Sensor 3: 24.1°C, 71%
...
```

**Note:** Only sensors that are paired and transmitting will appear. If you're missing sensors, pair them through the WS 3000 console menu.

---

## Install MQTT Broker

Install Mosquitto:

```bash
sudo apt-get install -y mosquitto mosquitto-clients
```

Configure for local access:

```bash
sudo nano /etc/mosquitto/conf.d/local.conf
```

Add:

```
listener 1883
allow_anonymous true
```

Start and enable:

```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

---

## Create MQTT Publishing Script

Create the script:

```bash
nano ~/ws3000/ws3000-mqtt.js
```

Paste:

```javascript
const ws3000 = require('ambientweather-ws3000');
const mqtt = require('mqtt');

// Configuration
const MQTT_BROKER = 'mqtt://localhost:1883';
const POLL_INTERVAL = 60000; // 60 seconds
const TOPIC_PREFIX = 'ws3000';

// Sensor names (customize these to match your locations)
const SENSOR_NAMES = {
  1: 'sensor_1',
  2: 'sensor_2',
  3: 'sensor_3',
  4: 'sensor_4',
  5: 'sensor_5',
  6: 'sensor_6',
  7: 'sensor_7',
  8: 'sensor_8'
};

const client = mqtt.connect(MQTT_BROKER);

client.on('connect', () => {
  console.log('Connected to MQTT broker');
  pollSensors();
  setInterval(pollSensors, POLL_INTERVAL);
});

client.on('error', (err) => {
  console.error('MQTT error:', err);
});

async function pollSensors() {
  try {
    const sensors = await ws3000.query();
    const timestamp = new Date().toISOString();

    for (let x = 1; x <= 8; x++) {
      if (sensors[x].active) {
        const name = SENSOR_NAMES[x];
        const payload = JSON.stringify({
          temperature: sensors[x].temperature,
          humidity: sensors[x].humidity,
          timestamp: timestamp
        });

        client.publish(`${TOPIC_PREFIX}/${name}`, payload);
        console.log(`[${timestamp}] Sensor ${x}: ${sensors[x].temperature}°C, ${sensors[x].humidity}%`);
      }
    }
  } catch (err) {
    console.error('Error polling sensors:', err);
  }
}
```

Test it:

```bash
node ~/ws3000/ws3000-mqtt.js
```

You should see:

```
Connected to MQTT broker
[2025-12-26T00:27:49.108Z] Sensor 1: 21.7°C, 72%
[2025-12-26T00:27:49.108Z] Sensor 2: 21.0°C, 85%
...
```

Press `Ctrl+C` to stop.

---

## Set Up Automatic Startup

Create a systemd service:

```bash
sudo nano /etc/systemd/system/ws3000.service
```

Paste (replace `pi` with your username if different):

```ini
[Unit]
Description=WS3000 Weather Station MQTT Publisher
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ws3000
ExecStart=/usr/bin/node /home/pi/ws3000/ws3000-mqtt.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ws3000
sudo systemctl start ws3000
sudo systemctl status ws3000
```

---

## Configure Home Assistant

### Step 1: Add MQTT Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **MQTT**
4. Enter:
   - Broker: `localhost`
   - Port: `1883`
   - Leave username/password blank

### Step 2: Add Sensor Configuration

Edit Home Assistant configuration:

```bash
sudo nano ~/homeassistant/configuration.yaml
```

Add this MQTT sensor configuration:

```yaml
mqtt:
  sensor:
    # WS3000 Sensor 1
    - name: "WS3000 Sensor 1 Temperature"
      state_topic: "ws3000/sensor_1"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 1 Humidity"
      state_topic: "ws3000/sensor_1"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 2
    - name: "WS3000 Sensor 2 Temperature"
      state_topic: "ws3000/sensor_2"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 2 Humidity"
      state_topic: "ws3000/sensor_2"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 3
    - name: "WS3000 Sensor 3 Temperature"
      state_topic: "ws3000/sensor_3"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 3 Humidity"
      state_topic: "ws3000/sensor_3"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 4
    - name: "WS3000 Sensor 4 Temperature"
      state_topic: "ws3000/sensor_4"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 4 Humidity"
      state_topic: "ws3000/sensor_4"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 5
    - name: "WS3000 Sensor 5 Temperature"
      state_topic: "ws3000/sensor_5"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 5 Humidity"
      state_topic: "ws3000/sensor_5"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 6
    - name: "WS3000 Sensor 6 Temperature"
      state_topic: "ws3000/sensor_6"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 6 Humidity"
      state_topic: "ws3000/sensor_6"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 7
    - name: "WS3000 Sensor 7 Temperature"
      state_topic: "ws3000/sensor_7"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 7 Humidity"
      state_topic: "ws3000/sensor_7"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity

    # WS3000 Sensor 8
    - name: "WS3000 Sensor 8 Temperature"
      state_topic: "ws3000/sensor_8"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "WS3000 Sensor 8 Humidity"
      state_topic: "ws3000/sensor_8"
      value_template: "{{ value_json.humidity }}"
      unit_of_measurement: "%"
      device_class: humidity
```

### Step 3: Restart Home Assistant

```bash
docker restart homeassistant
```

### Step 4: Verify Sensors

1. Wait 2-3 minutes for Home Assistant to restart
2. Go to **Developer Tools** → **States**
3. Filter for `ws3000`
4. You should see your sensors with temperature and humidity values

---

## Power Loss Recovery

All services are configured to start automatically on boot:

| Service | Auto-Start | Restart on Failure |
|---------|------------|-------------------|
| `mosquitto.service` | ✅ Enabled | ✅ Yes |
| `ws3000.service` | ✅ Enabled | ✅ Yes (10s delay) |
| Home Assistant Docker | ✅ `--restart=unless-stopped` | ✅ Yes |

After a power loss, everything will recover automatically within 1-2 minutes of boot.

To manually check status after a reboot:

```bash
sudo systemctl status mosquitto
sudo systemctl status ws3000
docker ps | grep homeassistant
```

---

## Setting a Static IP Address

By default, the Raspberry Pi gets an IP address from your router (DHCP). If your router reassigns IP addresses, your display and other services may break. To prevent this, set a static IP:

### Using NetworkManager (Ubuntu-based systems)

Find your connection name:
```bash
sudo nmcli connection show
```

Look for your WiFi connection (should be `netplan-wlan0-*` or similar). Then set a static IP:

```bash
sudo nmcli connection modify YOUR_CONNECTION_NAME ipv4.method manual \
  ipv4.addresses 192.168.68.109/24 \
  ipv4.gateway 192.168.68.1 \
  ipv4.dns "8.8.8.8 8.8.4.4"
```

Apply changes:
```bash
sudo nmcli connection up YOUR_CONNECTION_NAME
```

Verify:
```bash
ip addr show wlan0
```

### Using Traditional /etc/dhcpcd.conf (Raspberry Pi OS)

Edit the DHCP config:
```bash
sudo nano /etc/dhcpcd.conf
```

Add to the bottom:
```
interface wlan0
static ip_address=192.168.68.109/24
static routers=192.168.68.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

Save and restart:
```bash
sudo systemctl restart dhcpcd
```

### Using Router DHCP Reservation (Recommended for Simplicity)

Alternatively, configure your router to always assign the same IP to your Raspberry Pi:

1. Access your router admin page (usually `192.168.68.1`)
2. Find DHCP Reservations or Static DHCP
3. Add a reservation for your Raspberry Pi's MAC address (find it with `ip link show`)
4. Set the reserved IP to `192.168.68.109`
5. Save

This way the router manages the assignment and you don't have to manually configure it on the Pi.

---

## Troubleshooting

### USB Device Not Found

1. Check the device is connected:
   ```bash
   lsusb | grep 0483:5750
   ```

2. Verify udev rules are loaded:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

3. Unplug and replug the USB cable

### MQTT Connection Refused

1. Check Mosquitto is running:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Test MQTT manually:
   ```bash
   mosquitto_pub -h localhost -t "test" -m "hello"
   mosquitto_sub -h localhost -t "test"
   ```

### Sensors Show "Unavailable" in Home Assistant

1. Check the ws3000 service is running:
   ```bash
   sudo systemctl status ws3000
   ```

2. Check MQTT messages are being published:
   ```bash
   mosquitto_sub -h localhost -t "ws3000/#" -v
   ```

3. Verify Home Assistant MQTT integration is connected:
   - **Settings** → **Devices & Services** → **MQTT** → check status

### Missing Sensors

If fewer than 8 sensors appear:
- Sensors must be paired with the WS 3000 console
- Check batteries in remote sensors
- Move sensors closer to the console
- Pair sensors using the console menu

### MQTT Connection Timeout ("connack timeout")

If the ws3000 service logs show `MQTT error: Error: connack timeout`, this usually means the MQTT broker URL in the script is pointing to an old/invalid IP address.

**Root Cause:** The `MQTT_BROKER` variable in `ws3000-mqtt.js` should be set to `localhost:1883`, not a static IP address. If it's hardcoded to an IP (e.g., `mqtt://192.168.68.116:1883`), it will fail if:
- The device's IP address changes
- The Raspberry Pi is on a different network
- The IP was from a previous device

**Fix:**

1. Open the script:
   ```bash
   nano ~/ws3000/ws3000-mqtt.js
   ```

2. Find this line:
   ```javascript
   const MQTT_BROKER = 'mqtt://192.168.68.XXX:1883';  // or any IP address
   ```

3. Change it to:
   ```javascript
   const MQTT_BROKER = 'mqtt://localhost:1883';
   ```

4. Save and restart:
   ```bash
   sudo systemctl restart ws3000
   ```

5. Verify connection:
   ```bash
   sudo journalctl -u ws3000 -f
   ```

You should now see "Connected to MQTT broker" and sensor data being published.

**Prevention:** To prevent IP address changes from affecting your setup in the future, configure a **static IP** on the Raspberry Pi. See [Setting a Static IP Address](#setting-a-static-ip-address) below.

### Service Won't Start

Check logs:
```bash
sudo journalctl -u ws3000 -f
```

Common issues:
- Wrong username in service file
- Node.js not installed
- npm packages not installed in ~/ws3000
- MQTT broker URL is incorrect (see "MQTT Connection Timeout" above)

---

## Customizing Sensor Names

To give sensors meaningful names (e.g., "Living Room", "Garage"), edit the script:

```bash
nano ~/ws3000/ws3000-mqtt.js
```

Change the `SENSOR_NAMES` section:

```javascript
const SENSOR_NAMES = {
  1: 'living_room',
  2: 'bedroom',
  3: 'garage',
  4: 'basement',
  5: 'attic',
  6: 'outdoor',
  7: 'sensor_7',
  8: 'sensor_8'
};
```

Then update your Home Assistant configuration to match the new topic names (e.g., `ws3000/living_room`).

Restart the service:

```bash
sudo systemctl restart ws3000
docker restart homeassistant
```

---

## Related Documentation

- [Home Assistant Setup](HOME_ASSISTANT_SETUP.md) - Full MQTT integration for other sensors
- [Alternative Sensors Setup](ALTERNATIVE_SENSORS_SETUP.md) - Aranet 4, door sensors, and more
- [Fire Tablet Setup](FIRE_TABLET_SETUP.md) - Display dashboard on a tablet

---

## Credits

- [ambientweather-ws3000](https://github.com/EpicVoyage/ambientweather-ws3000) - Node.js USB library by EpicVoyage
