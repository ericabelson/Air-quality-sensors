# Security Guide for Air Quality Monitor

This guide covers security best practices for your Raspberry Pi air quality monitoring system. Following these recommendations will protect your home network from potential threats.

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Quick Security Checklist](#quick-security-checklist)
3. [Automated Security Hardening](#automated-security-hardening)
4. [Network Segmentation](#network-segmentation)
5. [SSH Hardening](#ssh-hardening)
6. [Firewall Configuration](#firewall-configuration)
7. [Home Assistant Security](#home-assistant-security)
8. [Docker Security](#docker-security)
9. [Ongoing Maintenance](#ongoing-maintenance)

---

## Security Overview

### Why Security Matters

Your Raspberry Pi is a computer connected to your home network. If compromised, an attacker could:

- Access other devices on your network (computers, phones, smart home devices)
- Use your Pi as a launching point for attacks
- Monitor your network traffic
- Access your personal data

### What This Project Does (and Doesn't Do)

**Local-only by default:**
- All sensor data is stored locally on your Pi
- No data is sent to external servers
- MQTT is configured for local broker only (disabled by default)

**Network exposure:**
- Home Assistant dashboard on port 8123 (local network)
- SSH on port 22 (for administration)
- Optional remote access (Tailscale, Cloudflare, or Nabu Casa)

---

## Quick Security Checklist

Complete these steps in order of priority:

| Priority | Action | Difficulty | Time |
|----------|--------|------------|------|
| 1 | Run security hardening script | Easy | 5 min |
| 2 | Set up SSH key authentication | Medium | 15 min |
| 3 | Enable Home Assistant 2FA | Easy | 5 min |
| 4 | Set up network segmentation | Medium | 30 min |
| 5 | Use Tailscale for remote access | Easy | 10 min |

---

## Automated Security Hardening

We provide a script that automatically configures most security settings.

### Running the Security Script

```bash
# Navigate to the scripts directory
cd ~/Air-quality-sensors/scripts

# Make the script executable
chmod +x security-hardening.sh

# Run with sudo
sudo bash security-hardening.sh
```

### What the Script Does

1. **Updates system packages** - Installs latest security patches
2. **Configures SSH hardening** - Disables root login, limits auth attempts
3. **Installs fail2ban** - Blocks IPs after failed login attempts
4. **Configures UFW firewall** - Only allows necessary ports
5. **Enables auto-updates** - Security updates install automatically

### After Running the Script

**IMPORTANT:** Before closing your terminal:

1. Open a **new terminal window**
2. Try to SSH into your Pi: `ssh your-user@your-pi-ip`
3. If it works, you're done!
4. If it fails, use the original terminal to fix the issue

---

## Network Segmentation

Network segmentation isolates your IoT devices (like the Raspberry Pi) from your main devices (computers, phones). This limits damage if any device is compromised.

### Why Segment Your Network?

```
WITHOUT SEGMENTATION:
┌─────────────────────────────────────────────────┐
│              Single Network                      │
│  Raspberry Pi ←→ Computer ←→ Phone ←→ TV        │
│       ↑                                          │
│  If compromised, attacker can reach everything  │
└─────────────────────────────────────────────────┘

WITH SEGMENTATION:
┌─────────────────────┐    ┌─────────────────────┐
│    IoT Network      │    │    Main Network     │
│   (Raspberry Pi)    │ X  │ (Computers, Phones) │
│                     │    │                     │
│   Can reach:        │    │   Can reach:        │
│   - Internet        │    │   - Internet        │
│   - Pi dashboard    │    │   - IoT dashboard   │
│                     │    │                     │
│   Cannot reach:     │    │                     │
│   - Main devices    │    │                     │
└─────────────────────┘    └─────────────────────┘
```

### TP-Link Deco M9 Plus Setup

The Deco M9 Plus supports IoT network isolation. Here's how to set it up:

#### Method 1: Guest Network (Easiest)

Use the Guest Network feature to isolate your Raspberry Pi:

1. **Open the Deco app** on your phone

2. **Go to Guest Network:**
   - Tap the **More** tab (bottom right)
   - Tap **Guest Network**

3. **Enable Guest Network:**
   - Toggle **Guest Network** to ON
   - Set a network name (SSID): `IoT-Devices` or similar
   - Set a strong password

4. **Configure Isolation:**
   - Ensure **Guest Network Isolation** is ON
   - This prevents guest/IoT devices from accessing main network devices

5. **Connect Pi to Guest Network:**
   - SSH into your Pi (while still on main network)
   - Edit WiFi config:
     ```bash
     sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
     ```
   - Update to use IoT network:
     ```
     network={
         ssid="IoT-Devices"
         psk="your-iot-network-password"
         key_mgmt=WPA-PSK
     }
     ```
   - Reboot: `sudo reboot`

6. **Access Dashboard:**
   - Your Pi will now be on the guest network
   - You can still access the dashboard from your main network
   - The Pi cannot initiate connections to main network devices

#### Method 2: IoT Network (If Available in Firmware)

Some Deco firmware versions have a dedicated IoT Network feature:

1. **Open the Deco app**

2. **Go to Advanced Settings:**
   - Tap **More** > **Advanced**
   - Look for **IoT Network** or **IoT Devices**

3. **Enable IoT Network:**
   - Toggle ON
   - Set network name: `IoT-Network`
   - Set password

4. **Configure Settings:**
   - Enable **Isolate IoT devices from main network**
   - Allow **IoT devices to access internet**
   - Allow **Main network to access IoT devices** (for dashboard access)

5. **Connect Pi to IoT Network:**
   - Follow Step 5 from Method 1

#### Verifying Isolation Works

After setup, verify the Pi is isolated:

1. **From Pi, try to ping a main network device:**
   ```bash
   ping 192.168.0.100  # Your computer's IP
   ```
   This should fail or timeout.

2. **From computer, access Pi dashboard:**
   ```
   http://[PI_IP]:8123
   ```
   This should work.

#### Firewall Rules (Advanced)

If your Deco supports custom firewall rules (in newer firmware):

1. **Block IoT to LAN:**
   - Source: IoT Network
   - Destination: Main Network
   - Action: Block

2. **Allow LAN to IoT:**
   - Source: Main Network
   - Destination: IoT Network (port 8123, 22)
   - Action: Allow

3. **Allow IoT to Internet:**
   - Source: IoT Network
   - Destination: Internet
   - Action: Allow

### Other Router Brands

<details>
<summary>Ubiquiti/UniFi</summary>

1. Create a new VLAN in UniFi Controller
2. Create a new WiFi network on that VLAN
3. Set up firewall rules to block inter-VLAN traffic
4. Allow specific ports (8123, 22) from main VLAN to IoT VLAN

</details>

<details>
<summary>Eero</summary>

1. Use Eero's Guest Network feature
2. Enable "Guest Network Isolation"
3. Connect Pi to guest network

</details>

<details>
<summary>Google Nest WiFi</summary>

1. Create a Guest network
2. Connect Pi to guest network
3. Guest devices are automatically isolated

</details>

---

## SSH Hardening

### Set Up SSH Key Authentication

SSH keys are more secure than passwords:

**On your computer (not the Pi):**

```bash
# Generate a new SSH key
ssh-keygen -t ed25519 -C "air-quality-pi"

# When prompted for location, press Enter for default
# When prompted for passphrase, enter a strong passphrase (recommended)

# Copy the key to your Pi
ssh-copy-id your-username@your-pi-ip
```

**Test the key:**

```bash
ssh your-username@your-pi-ip
```

You should log in without entering your Pi password (just the key passphrase if set).

### Disable Password Authentication

After SSH keys work, disable password login:

```bash
sudo nano /etc/ssh/sshd_config.d/security-hardening.conf
```

Ensure these lines are present:
```
PasswordAuthentication no
PermitRootLogin no
MaxAuthTries 3
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### Change SSH Port (Optional)

Changing the default port reduces automated attacks:

```bash
sudo nano /etc/ssh/sshd_config
```

Add:
```
Port 2222  # Or any port between 1024-65535
```

Update firewall:
```bash
sudo ufw delete allow ssh
sudo ufw allow 2222/tcp comment 'SSH on custom port'
sudo ufw reload
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

Connect using: `ssh -p 2222 user@pi-ip`

---

## Firewall Configuration

### UFW (Uncomplicated Firewall)

The security script configures UFW automatically. To manage manually:

**View current rules:**
```bash
sudo ufw status verbose
```

**Allow a service:**
```bash
sudo ufw allow 8123/tcp comment 'Home Assistant'
```

**Restrict to local network only:**
```bash
# Delete unrestricted rule
sudo ufw delete allow 8123/tcp

# Add local-only rule (adjust network range)
sudo ufw allow from 192.168.1.0/24 to any port 8123 comment 'Home Assistant local only'
```

**Block an IP:**
```bash
sudo ufw deny from 1.2.3.4
```

**View blocked IPs (fail2ban):**
```bash
sudo fail2ban-client status sshd
```

---

## Home Assistant Security

### Enable Two-Factor Authentication (2FA)

1. Log into Home Assistant
2. Click your username (bottom of sidebar)
3. Scroll to **Multi-factor Authentication Modules**
4. Click **Enable** next to **Totp**
5. Scan the QR code with an authenticator app:
   - Google Authenticator
   - Authy
   - 1Password
   - Bitwarden
6. Enter the code to confirm

### Create Separate User Accounts

Don't share a single admin account:

1. Go to **Settings** > **People**
2. Click **Add Person**
3. Create accounts for each family member
4. Set appropriate permissions (Admin vs User)

### Review Login Attempts

Check for suspicious activity:

1. Go to **Settings** > **System** > **Logs**
2. Filter for "login" or "auth"
3. Look for failed login attempts from unknown IPs

### Use a Strong Password

Your Home Assistant password should be:
- At least 16 characters
- Mix of letters, numbers, symbols
- Unique (not used elsewhere)
- Consider using a password manager

---

## Docker Security

### Reduce Container Privileges

The default Home Assistant installation uses `--privileged`. For better security:

```bash
# Stop current container
docker stop homeassistant
docker rm homeassistant

# Run with reduced privileges
docker run -d \
  --name homeassistant \
  --restart=unless-stopped \
  -e TZ=America/Chicago \
  -v /home/pi/homeassistant:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Note: Some integrations may require `--privileged`. Add it back only if needed.

### Keep Containers Updated

```bash
# Pull latest image
docker pull ghcr.io/home-assistant/home-assistant:stable

# Recreate container
docker stop homeassistant
docker rm homeassistant
# Run the docker command above again
```

### Container Monitoring

```bash
# View running containers
docker ps

# View container logs
docker logs homeassistant

# View resource usage
docker stats homeassistant
```

---

## Ongoing Maintenance

### Weekly Tasks

- [ ] Check fail2ban status: `sudo fail2ban-client status sshd`
- [ ] Review Home Assistant logs for anomalies
- [ ] Verify backups are working

### Monthly Tasks

- [ ] Update Home Assistant: `docker pull ghcr.io/home-assistant/home-assistant:stable`
- [ ] Review UFW logs: `sudo less /var/log/ufw.log`
- [ ] Check for failed SSH attempts: `sudo grep "Failed password" /var/log/auth.log`

### Quarterly Tasks

- [ ] Review all user accounts and permissions
- [ ] Update passwords
- [ ] Test backup restoration
- [ ] Review and update firewall rules

### Automatic Updates

The security script enables automatic security updates. Verify they're working:

```bash
# Check unattended-upgrades status
sudo systemctl status unattended-upgrades

# View upgrade logs
sudo cat /var/log/unattended-upgrades/unattended-upgrades.log
```

---

## Remote Access Security

If you need remote access, use one of these **secure** methods (in order of recommendation):

1. **Tailscale** (Recommended)
   - Free, zero-config VPN
   - No open ports on your router
   - WireGuard encryption
   - See [REMOTE_ACCESS.md](REMOTE_ACCESS.md)

2. **Cloudflare Tunnel**
   - Free with Cloudflare account
   - No open ports
   - Built-in DDoS protection

3. **Home Assistant Cloud (Nabu Casa)**
   - $6.50/month
   - Managed by Home Assistant team
   - Supports 2FA

### Never Do This

- **Never port forward** ports 22 or 8123 directly to the internet
- **Never disable** your firewall for "convenience"
- **Never share** SSH credentials or Home Assistant passwords
- **Never ignore** failed login notifications

---

## Incident Response

### If You Suspect Compromise

1. **Disconnect the Pi from the network:**
   - Unplug Ethernet or disable WiFi
   - This stops ongoing attacks

2. **From another computer, change passwords:**
   - Router admin password
   - Other IoT device passwords
   - Any passwords stored on the Pi

3. **Examine the Pi:**
   - Boot with a fresh SD card
   - Mount the old SD card as a data drive
   - Look for unauthorized changes

4. **Consider fresh install:**
   - Backup your sensor data
   - Flash a fresh Raspberry Pi OS
   - Run security hardening before restoring data

5. **Report if appropriate:**
   - If credentials were stolen, report to affected services
   - If part of a botnet, consider reporting to ISP

---

## Getting Help

If you have security concerns:

1. Check the [Troubleshooting](#troubleshooting) section in setup guides
2. Open an issue on GitHub
3. Do NOT post sensitive info (passwords, IPs) in public issues

---

## Appendix: Security Resources

- [Raspberry Pi Security Guide](https://www.raspberrypi.org/documentation/configuration/security.md)
- [Home Assistant Security Checklist](https://www.home-assistant.io/docs/configuration/securing/)
- [fail2ban Documentation](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [UFW Documentation](https://help.ubuntu.com/community/UFW)
