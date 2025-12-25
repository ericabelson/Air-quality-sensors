# Accessing Your Dashboard Remotely

This guide explains how to view your air quality dashboard from anywhere—not just when you're connected to your home WiFi.

---

## Understanding Local vs Remote Access

By default, your Home Assistant dashboard is only accessible on your **local network**:

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR HOME NETWORK                        │
│                                                              │
│   ┌──────────────┐        ┌──────────────┐                  │
│   │ Raspberry Pi │◄──────►│ Your Phone   │  ✅ Works        │
│   │   (sensors)  │        │ (on WiFi)    │                  │
│   └──────────────┘        └──────────────┘                  │
│          ▲                                                   │
│          │                ┌──────────────┐                  │
│          └───────────────►│ Fire Tablet  │  ✅ Works        │
│                           └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    OUTSIDE YOUR HOME                         │
│                                                              │
│   ┌──────────────┐        ┌──────────────┐                  │
│   │ Your Phone   │───X───►│ Raspberry Pi │  ❌ No access    │
│   │ (at work)    │        │   (at home)  │                  │
│   └──────────────┘        └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

To access your dashboard from outside your home, you need one of the solutions below.

---

## Quick Comparison

| Solution | Cost | Setup Difficulty | Best For |
|----------|------|------------------|----------|
| **Home Assistant Cloud (Nabu Casa)** | $6.50/month | Very Easy | Users who want it to "just work" |
| **Tailscale** | Free | Easy | Tech-comfortable users wanting free solution |
| **Cloudflare Tunnel** | Free | Medium | Users with a domain name |

---

## Option 1: Home Assistant Cloud (Nabu Casa)

**Best for:** Users who want the easiest setup with no technical configuration.

Home Assistant Cloud is the official remote access service from the makers of Home Assistant. It's the simplest option—just sign up and it works.

### Pros
- One-click setup, no router configuration needed
- Supports voice assistants (Alexa, Google Home)
- Helps fund Home Assistant development
- Automatic SSL certificates

### Cons
- Monthly subscription ($6.50/month or $65/year)
- Requires internet connection

### Setup Steps

1. **Open Home Assistant** in your browser:
   ```
   http://[YOUR_PI_IP]:8123
   ```

2. **Go to Settings:**
   - Click **Settings** in the sidebar
   - Click **Home Assistant Cloud**

3. **Create an account:**
   - Click **Start your free trial**
   - Enter your email and create a password
   - Verify your email

4. **Enable Remote Access:**
   - After logging in, toggle **Remote Control** to ON
   - Your remote URL will appear (e.g., `https://xxxxxxxx.ui.nabu.casa`)

5. **Access from anywhere:**
   - Use the Nabu Casa URL from any device, anywhere
   - Or use the Home Assistant Companion app (iOS/Android)

### Mobile App Setup

1. Download **Home Assistant** app from App Store or Google Play
2. Open the app and tap **Connect**
3. Log in with your Nabu Casa account
4. Your dashboard is now available on your phone anywhere

---

## Option 2: Tailscale (Free)

**Best for:** Tech-comfortable users who want a free, secure solution.

Tailscale creates a private network (VPN) between your devices. It's free for personal use and doesn't require any router configuration.

### Pros
- Free for personal use (up to 100 devices)
- Very secure (WireGuard-based)
- No port forwarding needed
- Works behind any firewall

### Cons
- Requires installing Tailscale on each device
- Slightly more technical than Nabu Casa

### Setup Steps

#### Step 1: Create a Tailscale Account

1. Go to [https://tailscale.com](https://tailscale.com)
2. Click **Get Started**
3. Sign up with Google, Microsoft, or GitHub account

#### Step 2: Install Tailscale on Your Raspberry Pi

SSH into your Raspberry Pi and run:

```bash
# Add Tailscale's package repository
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up
```

A URL will appear. Open it in a browser and log in to authorize the Pi.

Verify it's connected:
```bash
tailscale status
```

Note your Pi's Tailscale IP (e.g., `100.x.x.x`).

#### Step 3: Install Tailscale on Your Phone/Computer

**On iPhone/Android:**
1. Download **Tailscale** from App Store or Google Play
2. Open the app and sign in with the same account

**On Windows/Mac:**
1. Download Tailscale from [https://tailscale.com/download](https://tailscale.com/download)
2. Install and sign in

#### Step 4: Access Your Dashboard

From any device with Tailscale installed, access your dashboard at:

```
http://[PI_TAILSCALE_IP]:8123
```

For example: `http://100.64.0.1:8123`

**Tip:** To find your Pi's Tailscale IP, run `tailscale ip` on the Pi or check the Tailscale admin console.

### Optional: Set a Friendly Name

In the Tailscale admin console ([https://login.tailscale.com/admin](https://login.tailscale.com/admin)):

1. Find your Raspberry Pi in the list
2. Click the three dots → **Edit machine name**
3. Name it `utsensing`

Now you can access your dashboard at: `http://utsensing:8123`

---

## Option 3: Cloudflare Tunnel (Free)

**Best for:** Users who already have a domain name and want a professional setup.

Cloudflare Tunnel creates a secure connection from your Pi to Cloudflare's network, allowing access via a custom domain.

### Pros
- Free (with a free Cloudflare account)
- Professional URL (e.g., `https://airquality.yourdomain.com`)
- Built-in DDoS protection
- Automatic SSL

### Cons
- Requires owning a domain name
- More complex setup
- Domain must use Cloudflare DNS

### Prerequisites

- A domain name (e.g., `yourdomain.com`)
- Domain DNS managed by Cloudflare (free)

### Setup Steps

#### Step 1: Set Up Cloudflare

1. Create a free account at [https://cloudflare.com](https://cloudflare.com)
2. Add your domain and follow the instructions to update nameservers

#### Step 2: Install cloudflared on Raspberry Pi

SSH into your Pi:

```bash
# Download and install cloudflared
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Authenticate with Cloudflare
cloudflared tunnel login
```

This opens a browser window. Select your domain to authorize.

#### Step 3: Create a Tunnel

```bash
# Create a tunnel named "homeassistant"
cloudflared tunnel create homeassistant

# Note the tunnel ID shown (e.g., a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
```

#### Step 4: Configure the Tunnel

Create a config file:

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Add this content (replace values with yours):

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/pi/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: airquality.yourdomain.com
    service: http://localhost:8123
  - service: http_status:404
```

#### Step 5: Create DNS Record

```bash
cloudflared tunnel route dns homeassistant airquality.yourdomain.com
```

#### Step 6: Run the Tunnel

Test it first:
```bash
cloudflared tunnel run homeassistant
```

If it works, set it up as a service:
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

#### Step 7: Configure Home Assistant

Edit Home Assistant config to allow the Cloudflare proxy:

```bash
nano /home/pi/homeassistant/configuration.yaml
```

Add:
```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12
    - 127.0.0.1
```

Restart Home Assistant:
```bash
docker restart homeassistant
```

Now access your dashboard at: `https://airquality.yourdomain.com`

---

## What About Raspberry Pi Connect?

You may have seen **Raspberry Pi Connect** mentioned in the Raspberry Pi Imager. This is a remote access service from Raspberry Pi Foundation that provides:

- Remote terminal (SSH) access to your Pi
- Remote desktop screen sharing

**However, Pi Connect does NOT help with accessing your Home Assistant dashboard.** It only gives you access to the Pi itself, not to web services running on it (like Home Assistant on port 8123).

Use Pi Connect only if you need to:
- Troubleshoot your Pi remotely
- Access the Pi's desktop interface
- Run terminal commands when away from home

For viewing your air quality data remotely, use one of the three options above instead.

---

## Mobile App Options

Once you have remote access set up, you can use these apps:

### Home Assistant Companion App (Recommended)

Available for iOS and Android. Provides:
- Full dashboard access
- Push notifications for sensor alerts
- Widgets for your home screen
- Location-based automations

**Setup:**
1. Install "Home Assistant" from App Store / Google Play
2. Enter your remote URL (Nabu Casa, Tailscale IP, or Cloudflare domain)
3. Log in with your Home Assistant credentials

### Browser Bookmark

Simply bookmark your remote URL in your phone's browser for quick access.

---

## Troubleshooting

### "Connection refused" when accessing remotely

- Verify Home Assistant is running: `docker ps`
- Check the service is set up correctly (Tailscale/Cloudflare)
- Ensure you're using the correct IP or URL

### Tailscale shows "offline"

- SSH into the Pi and run: `sudo tailscale up`
- Check internet connection on the Pi

### Cloudflare tunnel not connecting

- Verify the tunnel is running: `sudo systemctl status cloudflared`
- Check logs: `sudo journalctl -u cloudflared -f`

### Nabu Casa says "remote access disabled"

- Go to Home Assistant → Settings → Home Assistant Cloud
- Toggle Remote Control to ON
- Check your Nabu Casa subscription status

---

## Security Considerations

**IMPORTANT:** Before enabling remote access, complete the security hardening steps in [SECURITY.md](SECURITY.md).

### Required Security Steps

Complete these before enabling remote access:

1. **Run the security hardening script:**
   ```bash
   cd ~/Air-quality-sensors/scripts
   sudo bash security-hardening.sh
   ```

2. **Enable two-factor authentication** in Home Assistant:
   - Settings → Profile → Multi-factor Authentication
   - Use an authenticator app (Google Authenticator, Authy, etc.)

3. **Use strong, unique passwords:**
   - At least 16 characters
   - Mix of letters, numbers, symbols
   - Use a password manager

4. **Set up SSH key authentication:**
   ```bash
   # On your computer
   ssh-keygen -t ed25519 -C "air-quality-pi"
   ssh-copy-id your-user@your-pi-ip
   ```

### Recommended Security Steps

5. **Network segmentation:**
   - Put Pi on a separate IoT/Guest network
   - See [SECURITY.md](SECURITY.md#network-segmentation)

6. **Keep software updated:**
   ```bash
   docker pull ghcr.io/home-assistant/home-assistant:stable
   docker stop homeassistant && docker rm homeassistant
   # Re-run docker command from setup guide
   ```

7. **Review access logs periodically:**
   - Home Assistant: Settings → System → Logs
   - SSH: `sudo grep "Failed password" /var/log/auth.log`

### Security Ranking of Remote Access Options

| Method | Security | Why |
|--------|----------|-----|
| **Tailscale** | Excellent | Zero-config VPN, no exposed ports, WireGuard encryption |
| **Cloudflare Tunnel** | Excellent | No exposed ports, DDoS protection, requires domain |
| **Home Assistant Cloud** | Very Good | Managed service, supports 2FA, easy setup |
| **Port Forwarding** | POOR | Exposes Pi directly to internet - **NEVER DO THIS** |

### What NOT to Do

- **NEVER port forward** ports 22 (SSH) or 8123 (Home Assistant) directly to the internet
- **NEVER disable** firewall for "convenience"
- **NEVER share** credentials publicly (GitHub issues, forums, etc.)
- **NEVER skip** 2FA setup for remote access

---

## Summary

| If you want... | Use this |
|----------------|----------|
| Easiest setup, don't mind paying | Home Assistant Cloud (Nabu Casa) |
| Free, willing to install an app on each device | Tailscale |
| Free, own a domain, comfortable with technical setup | Cloudflare Tunnel |

All three options work well. Choose based on your comfort level and preferences.
