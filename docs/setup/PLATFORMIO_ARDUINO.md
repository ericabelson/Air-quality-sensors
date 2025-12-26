# PlatformIO & Arduino Setup

This module covers installing PlatformIO and flashing the Arduino Nano firmware.

**Time Required:** 15 minutes

---

## What is PlatformIO?

PlatformIO is a professional development tool for embedded systems that replaces the Arduino IDE. It's faster, more reliable, and works perfectly on a headless Raspberry Pi.

**Official Website:** [https://platformio.org](https://platformio.org)
**Documentation:** [https://docs.platformio.org](https://docs.platformio.org)

---

## Step 1: Install PlatformIO

```bash
# Install PlatformIO Core
pip3 install platformio

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Installation takes 2-5 minutes.**

---

## Step 2: Verify Installation

```bash
pio --version
```

**Expected output:**
```
PlatformIO Core, version X.X.X
```

### If command not found:
- Log out and back in
- Or manually: `export PATH="$HOME/.local/bin:$PATH"`

---

## Step 3: Connect Arduino

1. Connect Arduino Nano to Raspberry Pi via USB cable
2. Verify detection:
   ```bash
   ls /dev/ttyUSB*
   ```
   You should see `/dev/ttyUSB0` or similar.

---

## Step 4: Set Permissions

```bash
# Give permission to access the serial port
sudo chmod 666 /dev/ttyUSB0

# Add your user to dialout group for permanent access
sudo usermod -a -G dialout $USER
```

**Important:** Log out and back in for the group change to take effect.

---

## Step 5: Flash the Firmware

```bash
cd ~/Air-quality-sensors/firmware/airNano
pio run -t upload
```

**Expected output:**
```
Processing nanoatmega328 (platform: atmelavr; board: nanoatmega328; framework: arduino)
...
avrdude: 6502 bytes of flash written
avrdude: verifying ...
avrdude: 6502 bytes of flash verified

SUCCESS
```

---

## Troubleshooting

### Permission denied

```bash
sudo chmod 666 /dev/ttyUSB0
# Then try uploading again
```

### Device not found

1. Check USB cable is connected
2. Try a different USB port
3. Check with: `dmesg | tail -20`
4. Try a different USB cable (some are power-only)

### Programmer not responding

Arduino Nano clones may use an old bootloader. Edit `platformio.ini`:

```ini
[env:nanoatmega328]
upload_speed = 57600
```

Then try uploading again.

### Command not found: pio

Ensure PATH is set:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## Verification

Check Arduino output:
```bash
dmesg | tail -20
```

Look for lines like:
```
usb 1-1.3: new full-speed USB device number 5 using dwc_otg
usb 1-1.3: New USB device found, idVendor=1a86, idProduct=7523
ch341-uart converter now attached to ttyUSB0
```

---

## Next Steps

After the Arduino is flashed:
- [Test sensor data collection](../RASPBERRY_PI_SETUP.md#part-5-test-everything)
- [Set up auto-start service](../RASPBERRY_PI_SETUP.md#part-6-set-up-auto-start)
