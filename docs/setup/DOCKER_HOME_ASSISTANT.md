# Docker & Home Assistant Installation

This module covers installing Docker and Home Assistant Container on your Raspberry Pi.

**Time Required:** 15-20 minutes

---

## Prerequisites

- Raspberry Pi with Raspberry Pi OS installed
- SSH access to your Pi
- Internet connection

---

## Step 1: Install Docker

SSH into your Raspberry Pi and run:

```bash
# Download and run Docker install script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group
sudo usermod -aG docker $USER
```

**Important:** Log out and back in for the group change to take effect:

```bash
logout
```

Then SSH back in.

---

## Step 2: Start Home Assistant Container

```bash
# Create config directory
mkdir -p ~/homeassistant

# Start Home Assistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v ~/homeassistant:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

**Note:** Replace `America/Chicago` with your timezone.

Wait 5-10 minutes for Home Assistant to initialize.

---

## Step 3: Access Home Assistant

1. Open a web browser
2. Go to: `http://[YOUR_PI_IP]:8123`
3. Create your user account
4. Set your home location
5. Complete the setup wizard

---

## Step 4: Add Bluetooth Support (Optional)

If you're using Bluetooth sensors (like Aranet 4), stop and recreate the container with Bluetooth access:

```bash
docker stop homeassistant
docker rm homeassistant

docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v ~/homeassistant:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

---

## Verification

Check that Home Assistant is running:

```bash
docker ps
```

You should see a container named `homeassistant` with status `Up`.

---

## Troubleshooting

### Container not starting

```bash
# Check logs
docker logs homeassistant
```

### Can't access web interface

- Verify the container is running: `docker ps`
- Check the IP address is correct
- Wait a few more minutes (first start can take 10+ minutes)

### Permission denied errors

Make sure you logged out and back in after adding your user to the docker group.

---

## Next Steps

After Home Assistant is running:
- [Configure MQTT](MQTT_SETUP.md) for sensor data
- [Set up the dashboard](../HOME_ASSISTANT_SETUP.md)
