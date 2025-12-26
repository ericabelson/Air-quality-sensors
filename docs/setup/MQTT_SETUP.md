# MQTT Broker Setup

This module covers installing and configuring the Mosquitto MQTT broker for sensor data publishing.

**Time Required:** 10 minutes

---

## What is MQTT?

MQTT is a lightweight messaging protocol used to send sensor data from your UTSensing system to Home Assistant. The Mosquitto broker acts as a central hub that receives data from sensors and forwards it to subscribers (like Home Assistant).

---

## Step 1: Install Mosquitto

```bash
# Install Mosquitto MQTT broker and clients
sudo apt install -y mosquitto mosquitto-clients

# Enable and start the service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

---

## Step 2: Configure Mosquitto

Create a configuration file:

```bash
sudo tee /etc/mosquitto/conf.d/utsensing.conf > /dev/null <<EOF
listener 1883
allow_anonymous true
EOF
```

Restart Mosquitto:

```bash
sudo systemctl restart mosquitto
```

---

## Step 3: Test MQTT

Open two terminal windows.

**Terminal 1 - Subscribe:**
```bash
mosquitto_sub -h localhost -t "test/#" -v
```

**Terminal 2 - Publish:**
```bash
mosquitto_pub -h localhost -t "test/hello" -m "Hello MQTT!"
```

You should see the message appear in Terminal 1.

---

## Step 4: Add MQTT to Home Assistant

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MQTT"
4. Enter broker details:
   - Broker: `localhost` (or your Pi's IP address)
   - Port: `1883`
   - Leave username/password blank

---

## Step 5: Enable MQTT in UTSensing

Edit the configuration file:

```bash
nano ~/Air-quality-sensors/firmware/xu4Mqqt/mintsXU4/mintsDefinitions.py
```

Update these settings:

```python
mqttOn = True
mqttBroker = "localhost"
mqttPort = 1883
```

Restart the UTSensing service:

```bash
sudo systemctl restart utsensing
```

---

## Verification

Check that MQTT messages are flowing:

```bash
mosquitto_sub -h localhost -t "utsensing/#" -v
```

You should see sensor data appearing every few seconds.

---

## Troubleshooting

### Mosquitto not running

```bash
sudo systemctl status mosquitto
# If not running:
sudo systemctl start mosquitto
```

### Can't connect from Home Assistant

- Verify Mosquitto is listening: `sudo netstat -tlnp | grep 1883`
- Check firewall: `sudo ufw allow 1883/tcp`

### No sensor data appearing

- Verify `mqttOn = True` in mintsDefinitions.py
- Check UTSensing service: `sudo systemctl status utsensing`
- Check logs: `journalctl -u utsensing -f`

---

## Security Note

The configuration above allows anonymous connections, which is fine for a local network. For production or exposed networks, configure authentication:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd your_username
```

Then update the config:
```
listener 1883
password_file /etc/mosquitto/passwd
allow_anonymous false
```
