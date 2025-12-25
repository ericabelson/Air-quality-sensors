# Amazon Fire Tablet Display Setup

Transform an Amazon Fire tablet into a dedicated air quality display that shows real-time sensor data from your UTSensing system.

**Time Required:** 30-60 minutes
**Cost:** Fire HD 8 ($50-100) or Fire HD 10 ($80-150)
**Prerequisites:** Home Assistant running with UTSensing sensors configured (see below)

**For technical details:** See [Technical Reference Appendix](TECHNICAL_REFERENCE.md) for Fully Kiosk Browser official download links and ADB installation guides

---

## IMPORTANT: What is Home Assistant?

**Home Assistant** is free, open-source software that creates a dashboard to display your sensor data. It runs on your Raspberry Pi and provides a web interface you can view from any device.

**You MUST set up Home Assistant BEFORE following this guide.** The Fire tablet is just a dedicated screen to display your Home Assistant dashboard.

### Complete This First:
1. Follow the [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) to set up your Pi
2. Follow the [Home Assistant Setup Guide](HOME_ASSISTANT_SETUP.md) to install and configure Home Assistant with your sensors

Once Home Assistant is running and showing your sensor data at `http://[YOUR_PI_IP]:8123`, you're ready to continue with this guide.

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

### IMPORTANT: Fully Kiosk Browser is NOT in the Amazon Appstore

**Fully Kiosk Browser is NOT available in the Amazon Appstore** and must be sideloaded manually. Follow the detailed instructions below.

### Step 2.1: Enable Installation from Unknown Sources

Before downloading Fully Kiosk Browser, you must enable installation of apps from outside the Amazon Appstore:

1. On your Fire tablet, swipe down from the top
2. Tap **Settings** (gear icon)
3. Tap **Security & Privacy**
4. Find **Apps from Unknown Sources** or **Install Unknown Apps**
5. Toggle it to **ON**
6. Read the warning and tap **OK**

**Why this is safe:** You're only installing from the official Fully Kiosk website, not random sources.

### Step 2.2: Download Fully Kiosk Browser APK

Now download the app directly from the official website:

1. On your Fire tablet, open the **Silk Browser** app
2. In the address bar, type exactly: `https://www.fully-kiosk.com`
3. Tap **Enter**
4. Look for the **Download APK Files** box on the right side of the page (you may need to scroll down)
5. Tap **Fully Kiosk Browser APK** (regular edition) to download
   - There is no separate "Fire OS" version - the regular APK works on Fire tablets
6. A prompt will appear asking to download a file
7. Tap **Download** to confirm
8. Wait for the download to complete (you'll see a notification)

**File location:** The APK file will be saved to your Downloads folder (typically named `de.ozerov.fully.apk` or similar).

**Official Download Link (if typing):** `https://www.fully-kiosk.com/en/#download`

### Step 2.3: Install the APK File

Now install the app you just downloaded:

1. On your Fire tablet, open the **Docs** app
   - Swipe up from the bottom to see all apps
   - Look for **Docs** (it's the default file manager)
2. Tap **Local Storage** (or **Internal Storage**)
3. Tap **Download** folder
4. Find the file named something like `fully-kiosk-fire.apk` or `de.ozerov.fully.apk`
5. Tap on the `.apk` file
6. A screen will appear saying "Do you want to install this application?"
7. Tap **Install**
8. Wait for installation to complete (5-10 seconds)
9. Tap **Done** (do NOT tap "Open" yet)

**Troubleshooting:**
- **Can't find Docs app?** Try opening **Files** or **File Manager**
- **Install button is grayed out?** Go back to Step 2.1 and ensure "Apps from Unknown Sources" is enabled
- **Installation failed?** Download the APK again; the file may have been corrupted

**✓ Installation successful?** Great! Skip ahead to [Step 2.4: Grant Permissions](#step-24-grant-permissions) below.

---

### Alternative Method: Install via Computer (Advanced)

> **Note:** Only use this method if the direct installation above (Steps 2.1-2.3) didn't work for you. Most users won't need this.

If you have a computer and USB cable, you can install via ADB (Android Debug Bridge):

**Requirements:**
- Windows, Mac, or Linux computer
- USB cable (USB-A to Micro-USB or USB-C, depending on your Fire tablet model)
- Android Platform Tools

**Step-by-Step:**

1. **On your Fire Tablet:**
   - Settings → Device Options → About Fire Tablet
   - Tap **Serial Number** 7 times to enable Developer Options
   - Go back → **Developer Options**
   - Enable **ADB Debugging**
   - Enable **Apps from Unknown Sources**

2. **On your Computer:**
   - Download Android Platform Tools:
     - Windows: [https://dl.google.com/android/repository/platform-tools-latest-windows.zip](https://dl.google.com/android/repository/platform-tools-latest-windows.zip)
     - Mac: [https://dl.google.com/android/repository/platform-tools-latest-darwin.zip](https://dl.google.com/android/repository/platform-tools-latest-darwin.zip)
     - Linux: [https://dl.google.com/android/repository/platform-tools-latest-linux.zip](https://dl.google.com/android/repository/platform-tools-latest-linux.zip)
   - Extract the ZIP file to a folder (e.g., `C:\platform-tools`)

3. **Download Fully Kiosk APK to your computer:**
   - Visit [https://www.fully-kiosk.com/en/#download](https://www.fully-kiosk.com/en/#download)
   - Download "Fully Kiosk Browser for Fire OS"
   - Save the `.apk` file to the same folder as platform-tools

4. **Connect Tablet to Computer:**
   - Connect Fire tablet to computer via USB cable
   - On tablet, tap **Allow** when prompted "Allow USB debugging?"
   - Check "Always allow from this computer"

5. **Install via ADB:**

   **Windows:**
   - Open Command Prompt
   - Navigate to platform-tools folder:
     ```cmd
     cd C:\platform-tools
     adb devices
     ```
   - You should see your device listed
   - Install the APK:
     ```cmd
     adb install fully-kiosk-fire.apk
     ```

   **Mac/Linux:**
   - Open Terminal
   - Navigate to platform-tools folder:
     ```bash
     cd ~/platform-tools
     ./adb devices
     ```
   - You should see your device listed
   - Install the APK:
     ```bash
     ./adb install fully-kiosk-fire.apk
     ```

6. **Verify Installation:**
   - Look for "Success" message in terminal
   - On tablet, check app drawer for Fully Kiosk Browser icon

---

### Step 2.4: Grant Permissions (On-Demand)

Fully Kiosk Browser requests permissions **on-demand** as you enable features that need them, not all at once on first launch. You may see some permission prompts now, but most will appear later when you configure specific features.

#### Permissions You May See Now

**Location Access (Optional)**
- If prompted for location access, you can tap **Deny** - this is fine for a wall-mounted display
- Tap **Allow** only if you want location-based features

#### Permissions You'll See Later

The following permissions are requested when you enable the features that need them:

| Permission | When It's Requested |
|------------|---------------------|
| **Display Over Other Apps** | When you enable Kiosk Mode (Step 3.4) or Motion Detection |
| **Modify System Settings** | When you configure screen brightness or dimming |
| **Device Administrator** | When you enable Screen Off Timer, Remote Admin, or Scheduled Sleep |

**Don't worry if you don't see all these prompts now!** They will appear at the appropriate time as you work through the configuration steps below.

#### How to Grant Permissions When Prompted

When a permission prompt appears:
1. Tap **Go to Settings** (or similar button)
2. Find **Fully Kiosk Browser** in the list
3. Toggle the switch to **ON**
4. Tap the **Back** button to return to Fully Kiosk

**Note:** You can also grant permissions manually anytime:
- Go to Fire tablet **Settings** → **Apps & Notifications** → **Fully Kiosk Browser** → **Permissions**

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

### Step 3.2: Configure Fully Kiosk Browser Settings

Before connecting to Home Assistant, configure these basic settings in Fully Kiosk:

#### Step 3.2.1: Enable Required Browser Settings
1. In Fully Kiosk, tap the menu (three lines, top-right)
2. Go to **Settings** → **Web Content Settings**
3. Enable **Autoplay Videos** (toggle to ON)
4. Enable **Enable JavaScript** (toggle to ON)
5. Enable **Load Links in Same Tab** (toggle to ON)
6. Tap **Back** to save

### Step 3.3: Configure Auto-Login to Home Assistant

Home Assistant requires you to log in. Since you don't want to log in every time on a wall display, you need to set up automatic authentication. Choose ONE of the two methods below:

---

#### Method A: Trusted Networks (Easier - Recommended)

This method tells Home Assistant to automatically trust any device on your home network.

##### Step 3.3.1: Access Home Assistant on Your Computer
1. On your computer (not the tablet), open a web browser
2. Go to `http://[YOUR_PI_IP]:8123`
   - Replace `[YOUR_PI_IP]` with your Raspberry Pi's IP address
   - Example: `http://192.168.1.100:8123`
3. Log in with your Home Assistant username and password (the one you created during [Home Assistant Setup](HOME_ASSISTANT_SETUP.md))

##### Step 3.3.2: Edit the Configuration File
1. In Home Assistant, click **Settings** in the left sidebar
2. Click **Add-ons** (if using Home Assistant OS) or access your Pi via SSH
3. You need to edit the file `configuration.yaml` on your Raspberry Pi
4. Add the following to the file:

```yaml
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 192.168.1.0/24  # Your local network - adjust if different
      allow_bypass_login: true
    - type: homeassistant
```

**Note:** Change `192.168.1.0/24` to match your network. If your Pi's IP is `192.168.0.100`, use `192.168.0.0/24`.

##### Step 3.3.3: Restart Home Assistant
1. In Home Assistant, go to **Settings** → **System** → **Restart**
2. Click **Restart** and wait 1-2 minutes for it to come back up
3. Now any device on your home network can access Home Assistant without logging in

---

#### Method B: Long-Lived Access Token (More Secure)

This method creates a special password (token) embedded in the URL. More secure but slightly more complex.

##### Step 3.3.1: Open Home Assistant on Your Computer
1. On your computer (not the tablet), open a web browser
2. Go to `http://[YOUR_PI_IP]:8123`
   - Replace `[YOUR_PI_IP]` with your Raspberry Pi's IP address
   - Example: `http://192.168.1.100:8123`
3. Log in with your Home Assistant username and password

##### Step 3.3.2: Navigate to Your User Profile
1. Look at the bottom-left corner of Home Assistant
2. Click on your **username** or the **person icon**
3. This opens your User Profile page

##### Step 3.3.3: Create a Long-Lived Access Token
1. Scroll down to the **Long-Lived Access Tokens** section
2. Click **Create Token**
3. Enter a name: `Fire Tablet`
4. Click **OK** or **Create**
5. **IMPORTANT:** A token will appear. Copy it immediately!
6. Save this token somewhere safe - you can only see it once!

Example token (yours will be different):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI...
```

##### Step 3.3.4: Update the Start URL in Fully Kiosk
1. Go back to Fully Kiosk on your tablet
2. Go to **Settings** → **Web Content Settings**
3. Update the **Start URL** to include the token:

```
http://[YOUR_PI_IP]:8123/lovelace/tablet?auth_callback=1&access_token=[YOUR_TOKEN]
```

Replace:
- `[YOUR_PI_IP]` with your Raspberry Pi's IP (e.g., `192.168.1.100`)
- `[YOUR_TOKEN]` with the token you copied

Example:
```
http://192.168.1.100:8123/lovelace/tablet?auth_callback=1&access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI...
```

---

### Step 3.4: Enable Kiosk Mode

1. Go to **Settings** → **Kiosk Mode**
2. Enable **Enable Kiosk Mode**
3. Set **Kiosk Exit Password** (remember this!)
4. Enable these options:
   - **Lock Safe Mode**
   - **Disable Status Bar**
   - **Disable Navigation Bar**
   - **Disable Volume Buttons** (optional)
   - **Disable Power Button** (optional, use carefully)

### Step 3.5: Configure Screen Behavior

1. Go to **Settings** → **Device Management**
2. **Keep Screen On**: Enable
3. **Screen Brightness**: Set desired level (e.g., 50%)
4. **Screen Off Timer**: Set to Never (or a long time)

**For Night Mode (Dim at Night):**

1. Go to **Settings** → **Device Management**
2. Enable **Time-based Screen Brightness**
3. Set schedule (e.g., 22:00-07:00)
4. Set night brightness (e.g., 10%)

### Step 3.6: Motion Detection (Optional)

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
