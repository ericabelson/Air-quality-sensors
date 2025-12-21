# Amazon Fire Tablet Display Setup

Transform an Amazon Fire tablet into a dedicated air quality display that shows real-time sensor data from your UTSensing system.

**Time Required:** 30-60 minutes
**Cost:** Fire HD 8 ($50-100) or Fire HD 10 ($80-150)
**Prerequisites:** Home Assistant running with UTSensing sensors configured

---

## Table of Contents

1. [What You Need](#what-you-need)
2. [Part 1: Prepare the Fire Tablet](#part-1-prepare-the-fire-tablet)
3. [Part 2: Install Fully Kiosk Browser](#part-2-install-fully-kiosk-browser)
4. [Part 3: Configure Kiosk Mode](#part-3-configure-kiosk-mode)
5. [Part 4: Optimize Display Settings](#part-4-optimize-display-settings)
6. [Part 5: Power and Mounting](#part-5-power-and-mounting)
7. [Alternative: Without Rooting](#alternative-without-rooting)
8. [Troubleshooting](#troubleshooting)

---

## What You Need

### Hardware
- [ ] Amazon Fire HD 8 (2020 or newer) or Fire HD 10
- [ ] USB power cable and adapter (5V 2A minimum)
- [ ] Wall mount (optional) - 3D printed or purchased
- [ ] MicroSD card (optional, for offline mode)

### Software (Free)
- [ ] Fully Kiosk Browser (free version works fine)
- [ ] Home Assistant running on your network

### Network
- [ ] WiFi access to same network as Home Assistant
- [ ] Static IP recommended for Home Assistant

---

## Part 1: Prepare the Fire Tablet

### Step 1.1: Initial Setup

1. Power on the Fire tablet
2. Connect to your WiFi network
3. Sign in with an Amazon account (required for app store)
4. Complete the initial setup wizard
5. Skip any offers for Kindle Unlimited, etc.

### Step 1.2: Update the System

1. Go to **Settings** → **Device Options** → **System Updates**
2. Check for and install any available updates
3. Restart if prompted

### Step 1.3: Disable Lock Screen (Optional but Recommended)

1. Go to **Settings** → **Security & Privacy**
2. Set **Lock Screen Password** to **Off**
3. Confirm the warning

### Step 1.4: Disable Notifications

1. Go to **Settings** → **Notifications**
2. Turn off notifications for apps you don't need
3. Especially disable Amazon Shopping, Kindle, etc.

### Step 1.5: Disable Ads on Lock Screen

1. Go to **Settings** → **Lockscreen**
2. If available, disable "Ads" or "Special Offers"
3. (Note: You may need to pay $15 to remove lock screen ads)

---

## Part 2: Install Fully Kiosk Browser

### What is Fully Kiosk Browser?

Fully Kiosk Browser is an app designed for dedicated displays. It:
- Runs a web page in full-screen mode
- Prevents users from exiting to other apps
- Automatically returns to the dashboard if the app crashes
- Supports motion-activated screen wake
- Can dim the screen at night

### Step 2.1: Download Fully Kiosk Browser

**Method A: From Amazon Appstore (Easiest)**

1. Open the **Amazon Appstore** on your Fire tablet
2. Search for "Fully Kiosk Browser"
3. Install the free version

**Method B: Sideload APK (If not in Appstore)**

1. On the Fire tablet, go to **Settings** → **Security & Privacy**
2. Enable **Apps from Unknown Sources**
3. Open Silk Browser
4. Go to: `https://www.fully-kiosk.com/en/#download`
5. Download the APK file
6. Open the downloaded file and install

### Step 2.2: Grant Permissions

When you first open Fully Kiosk:

1. Allow **Display over other apps**
2. Allow **Modify system settings**
3. Allow **Access device location** (optional)
4. Enable **Device Admin** when prompted (for kiosk mode)

---

## Part 3: Configure Kiosk Mode

### Step 3.1: Set the Start URL

1. Open Fully Kiosk Browser
2. Tap the three lines (menu) in the top-right
3. Go to **Settings** → **Web Content Settings**
4. Set **Start URL** to:

```
http://[YOUR_PI_IP]:8123/lovelace/tablet
```

Replace `[YOUR_PI_IP]` with your Raspberry Pi's IP address.

Example: `http://192.168.1.100:8123/lovelace/tablet`

### Step 3.2: Configure Auto-Login (Important!)

Home Assistant requires login. To auto-login:

1. In Fully Kiosk, go to **Settings** → **Web Content Settings**
2. Enable **Autoplay Videos**
3. Enable **Enable JavaScript**
4. Enable **Load Links in Same Tab**

**Create a Long-Lived Access Token:**

1. On your computer, open Home Assistant
2. Click your user profile (bottom left)
3. Scroll to **Long-Lived Access Tokens**
4. Click **Create Token**
5. Name it "Fire Tablet"
6. Copy the token (you can only see it once!)

**Use Token in URL:**

Update your Start URL to:
```
http://[YOUR_PI_IP]:8123/lovelace/tablet?auth_callback=1&access_token=[YOUR_TOKEN]
```

Or set up trusted networks in Home Assistant (easier):

Edit Home Assistant `configuration.yaml`:
```yaml
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 192.168.1.0/24  # Your local network
      allow_bypass_login: true
    - type: homeassistant
```

### Step 3.3: Enable Kiosk Mode

1. Go to **Settings** → **Kiosk Mode**
2. Enable **Enable Kiosk Mode**
3. Set **Kiosk Exit Password** (remember this!)
4. Enable these options:
   - **Lock Safe Mode**
   - **Disable Status Bar**
   - **Disable Navigation Bar**
   - **Disable Volume Buttons** (optional)
   - **Disable Power Button** (optional, use carefully)

### Step 3.4: Configure Screen Behavior

1. Go to **Settings** → **Device Management**
2. **Keep Screen On**: Enable
3. **Screen Brightness**: Set desired level (e.g., 50%)
4. **Screen Off Timer**: Set to Never (or a long time)

**For Night Mode (Dim at Night):**

1. Go to **Settings** → **Device Management**
2. Enable **Time-based Screen Brightness**
3. Set schedule (e.g., 22:00-07:00)
4. Set night brightness (e.g., 10%)

### Step 3.5: Motion Detection (Optional)

Enable motion-activated screen:

1. Go to **Settings** → **Motion Detection**
2. Enable **Detect Motion (Front Camera)**
3. Set **Turn Screen On** on motion
4. Set **Screen Off After** (e.g., 5 minutes of no motion)

---

## Part 4: Optimize Display Settings

### Step 4.1: Configure Auto-Restart

1. Go to **Settings** → **Web Content Settings**
2. Enable **Auto Reload on Network Reconnect**
3. Set **Reload After Idle Time**: 300 (5 minutes)

### Step 4.2: Prevent Screen Burn-in

1. Go to **Settings** → **Device Management**
2. Enable **Screen Saver** (optional)
3. Or use Home Assistant's dimming features

### Step 4.3: Disable Swipe Gestures

1. Go to **Settings** → **Kiosk Mode**
2. Enable **Disable Swipe from Edges**
3. Enable **Disable All Touch Gestures** (optional)

### Step 4.4: Test the Configuration

1. Tap **Back** until you're at the main screen
2. Tap the **Home** icon to load your dashboard
3. Verify the dashboard loads correctly
4. Test that you cannot exit to other apps
5. Try pressing Home and Back buttons (should be blocked)

**To Exit Kiosk Mode:**
1. Tap the screen 5 times quickly in the same spot (default)
2. Enter your Kiosk Exit Password
3. Or: Swipe from left edge, tap settings gear

---

## Part 5: Power and Mounting

### Step 5.1: Continuous Power

The tablet should be plugged in 24/7:

1. Use the original charger or a quality 5V 2A adapter
2. Consider a right-angle USB cable for cleaner mounting
3. The battery will stay at 100% when plugged in

**Battery Health Note:** Modern tablets handle continuous charging well. If concerned, Fully Kiosk has a setting to limit charging to 80%.

### Step 5.2: Mounting Options

**Option A: Tablet Stand**
- Simple desktop stands are $10-20
- Allows easy removal for updates

**Option B: Wall Mount**
- Flush wall mounts available on Amazon ($15-30)
- 3D printable mounts available on Thingiverse
- Run power cable through wall for clean look

**Option C: Magnetic Mount**
- Attach metal plate to back of tablet
- Use magnetic mount on wall
- Easy on/off for maintenance

### Step 5.3: Hide the Power Cable

- Use cable raceways (paintable)
- Run through wall (if comfortable with electrical work)
- Position near outlet for short cable run

---

## Alternative: Without Rooting

If you don't want to use Fully Kiosk, here are simpler alternatives:

### Option A: Silk Browser Bookmark

1. Open **Silk Browser** on Fire tablet
2. Navigate to your Home Assistant dashboard
3. Tap menu → **Add to Home**
4. Creates a shortcut icon
5. Enable "Do Not Disturb" mode
6. Disable screen timeout in Settings

**Limitations:** User can still access other apps, less reliable.

### Option B: Home Assistant Companion App

1. Sideload Home Assistant Companion App
2. Configure with your Home Assistant URL
3. Enable kiosk mode in app settings

**How to sideload:**
1. Enable Apps from Unknown Sources
2. Download APK from GitHub releases
3. Install via file manager

### Option C: Wall Panel App

1. Search for "WallPanel" in apps
2. Configure with MQTT and Home Assistant
3. Supports motion detection and more

---

## Troubleshooting

### Dashboard Won't Load

1. **Check WiFi Connection**
   - Go to Settings → Network
   - Verify connected to correct network

2. **Verify URL**
   - Test URL in Silk Browser first
   - Make sure IP address is correct
   - Check if Home Assistant is running

3. **Firewall Issues**
   - Ensure port 8123 is open on Pi
   - Check if tablet can ping Pi:
     ```
     http://[PI_IP]:8123
     ```

### Screen Goes Black

1. **Check Power Settings**
   - Fully Kiosk: Settings → Device Management → Keep Screen On
   - Tablet Settings: Display → Screen Timeout → Never

2. **Check Motion Detection**
   - If enabled, wave hand in front of camera
   - Try disabling motion detection temporarily

### Kiosk Mode Not Working

1. **Device Admin**
   - Go to Settings → Security → Device Administrators
   - Ensure Fully Kiosk is enabled as admin

2. **Reinstall**
   - Uninstall Fully Kiosk
   - Reinstall and grant all permissions again

### Dashboard Shows Login Screen

1. **Trusted Networks**
   - Add tablet's IP range to trusted networks
   - Restart Home Assistant

2. **Long-Lived Token**
   - Create new token in HA profile
   - Update Start URL with token

### Tablet Runs Hot

1. **Reduce Brightness**
   - Lower screen brightness to 50% or less
   - Enable night mode dimming

2. **Remove Case**
   - If tablet has a case, heat may build up
   - Ensure ventilation around tablet

### Auto-Reload Not Working

1. **Check Settings**
   - Fully Kiosk → Settings → Web Content Settings
   - Enable Auto Reload on Network Reconnect

2. **Network Stability**
   - Ensure stable WiFi connection
   - Consider using 5GHz if available

---

## Recommended Settings Summary

```
Fully Kiosk Browser Settings:

Web Content Settings:
  - Start URL: http://[PI_IP]:8123/lovelace/tablet
  - Enable JavaScript: ON
  - Autoplay Videos: ON
  - Load Links in Same Tab: ON
  - Auto Reload on Network Reconnect: ON

Kiosk Mode:
  - Enable Kiosk Mode: ON
  - Disable Status Bar: ON
  - Disable Navigation Bar: ON
  - Lock Safe Mode: ON

Device Management:
  - Keep Screen On: ON
  - Screen Brightness: 50%
  - Time-based Brightness: ON (optional)
    - Night hours: 22:00 - 07:00
    - Night brightness: 10%

Motion Detection (optional):
  - Detect Motion: ON
  - Turn Screen On on Motion: ON
  - Screen Off After: 300 seconds
```

---

## Next Steps

Your Fire tablet is now a dedicated air quality display!

- **Customize the dashboard** - Edit in Home Assistant
- **Add more sensors** - Multiple UTSensing units
- **Set up alerts** - Push notifications to phone
- **Add automations** - Turn on fans when AQI is high

See [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md) for dashboard customization options.
