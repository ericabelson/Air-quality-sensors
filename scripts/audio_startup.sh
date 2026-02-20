#!/bin/bash
###############################################################################
# Audio Pipeline Startup Script
# =============================
# Runs at boot (as a oneshot systemd service) BEFORE the audio stream and
# detector services. Ensures the ALSA loopback device is ready and writes
# the dynamically-detected card number to /run/audio_loopback_card so that
# other services can read it instead of hardcoding a card number.
#
# Why this exists:
#   After a reboot the ALSA loopback card number can change (e.g. from
#   card 3 to card 1). The iphone-audio-stream service used to hardcode
#   "hw:3,0" which would silently fail if the number shifted.
#
# Usage:
#   sudo bash audio_startup.sh        # manual run
#   (or) runs automatically via audio_startup.service at boot
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

echo "=== Audio Pipeline Startup ==="
echo "Time: $(date)"

###############################################################################
# Step 1: Ensure snd-aloop kernel module is loaded
###############################################################################

echo "Checking snd-aloop kernel module..."

if lsmod | grep -q snd_aloop; then
    echo "  snd-aloop: already loaded"
else
    echo "  Loading snd-aloop..."
    modprobe snd-aloop
    # Give the kernel a moment to create the device
    sleep 2

    if lsmod | grep -q snd_aloop; then
        echo "  snd-aloop: loaded successfully"
    else
        echo "  ERROR: Failed to load snd-aloop" >&2
        exit 1
    fi
fi

###############################################################################
# Step 2: Detect loopback card number
###############################################################################

echo "Detecting loopback card number..."

# Wait up to 10 seconds for the device to appear (can be slow after boot)
for i in $(seq 1 10); do
    CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
    if [ -n "$CARD" ]; then
        break
    fi
    echo "  Waiting for loopback device... ($i/10)"
    sleep 1
done

if [ -z "$CARD" ]; then
    echo "ERROR: No ALSA loopback device found after 10 seconds" >&2
    echo "  Module loaded but device not appearing." >&2
    echo "  Check: arecord -l" >&2
    exit 1
fi

echo "  Loopback card: $CARD"
echo "  FFmpeg output:  hw:$CARD,0"
echo "  Detector input: hw:$CARD,1"

###############################################################################
# Step 3: Write card number to /run for other services
###############################################################################

echo "$CARD" > /run/audio_loopback_card
chmod 644 /run/audio_loopback_card
echo "  Written to /run/audio_loopback_card"

###############################################################################
# Step 4: Ensure /mnt/usb exists for USB recording storage
###############################################################################

if [ ! -d /mnt/usb ]; then
    mkdir -p /mnt/usb
    echo "  Created /mnt/usb mount point"
fi

echo "=== Audio Pipeline Startup Complete ==="
