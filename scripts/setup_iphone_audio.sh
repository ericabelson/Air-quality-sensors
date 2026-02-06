#!/bin/bash
###############################################################################
# Setup iPhone Audio Streaming via ALSA Loopback
# ===============================================
# Automates the ALSA loopback device + iPhone RTSP stream service setup.
#
# What this does:
#   1. Loads the snd-aloop kernel module (virtual audio device)
#   2. Makes it persistent across reboots
#   3. Creates a systemd service that captures iPhone RTSP audio via FFmpeg
#   4. Enables and starts the service
#
# Usage:
#   ./setup_iphone_audio.sh <iPhone-IP-address>
#
# Example:
#   ./setup_iphone_audio.sh 192.168.1.150
#
# Prerequisites:
#   - iPhone running Periscope HD with RTSP streaming enabled
#   - ffmpeg installed on the Pi
#   - iPhone and Pi on the same network
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

###############################################################################
# Parse Arguments
###############################################################################

IPHONE_IP="${1}"
RTSP_PORT="${2:-8554}"

if [ -z "$IPHONE_IP" ]; then
    echo -e "${RED}Error: iPhone IP address required${NC}"
    echo ""
    echo "Usage: $0 <iPhone-IP> [RTSP-port]"
    echo ""
    echo "Example:"
    echo "  $0 192.168.1.150"
    echo "  $0 192.168.1.150 8554"
    echo ""
    echo "To find your iPhone IP:"
    echo "  iPhone > Settings > Wi-Fi > tap your network > IP Address"
    exit 1
fi

RTSP_URL="rtsp://${IPHONE_IP}:${RTSP_PORT}/live.sdp"

echo -e "${GREEN}=== iPhone Audio Stream Setup ===${NC}"
echo "iPhone IP:   ${IPHONE_IP}"
echo "RTSP Port:   ${RTSP_PORT}"
echo "Stream URL:  ${RTSP_URL}"
echo ""

###############################################################################
# Check Prerequisites
###############################################################################

echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg not found. Install it with:${NC}"
    echo "  sudo apt-get install -y ffmpeg"
    exit 1
fi
echo -e "${GREEN}  ✓ ffmpeg installed${NC}"

# Check if we can reach the iPhone (quick ping test)
if ping -c 1 -W 2 "${IPHONE_IP}" &> /dev/null; then
    echo -e "${GREEN}  ✓ iPhone reachable at ${IPHONE_IP}${NC}"
else
    echo -e "${YELLOW}  ⚠ Cannot ping iPhone at ${IPHONE_IP} - continuing anyway${NC}"
    echo "    (Make sure Periscope HD is running and streaming)"
fi

###############################################################################
# Step 1: Load ALSA Loopback Module
###############################################################################

echo ""
echo -e "${YELLOW}Step 1: Loading ALSA loopback kernel module...${NC}"

if lsmod | grep -q snd_aloop; then
    echo -e "${GREEN}  ✓ snd-aloop already loaded${NC}"
else
    sudo modprobe snd-aloop
    if lsmod | grep -q snd_aloop; then
        echo -e "${GREEN}  ✓ snd-aloop loaded successfully${NC}"
    else
        echo -e "${RED}  ✗ Failed to load snd-aloop${NC}"
        echo "    Your kernel may not support ALSA loopback."
        echo "    Try: sudo apt-get install linux-modules-extra-\$(uname -r)"
        exit 1
    fi
fi

###############################################################################
# Step 2: Make Module Persistent
###############################################################################

echo -e "${YELLOW}Step 2: Making snd-aloop persistent across reboots...${NC}"

if grep -q "^snd-aloop" /etc/modules 2>/dev/null; then
    echo -e "${GREEN}  ✓ Already in /etc/modules${NC}"
else
    echo "snd-aloop" | sudo tee -a /etc/modules > /dev/null
    echo -e "${GREEN}  ✓ Added snd-aloop to /etc/modules${NC}"
fi

###############################################################################
# Step 3: Detect Loopback Card Number
###############################################################################

echo -e "${YELLOW}Step 3: Detecting loopback device...${NC}"

# Find the loopback card number
LOOPBACK_CARD=$(arecord -l 2>/dev/null | grep -i "loopback" | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')

if [ -z "$LOOPBACK_CARD" ]; then
    echo -e "${RED}  ✗ Loopback device not found in arecord -l${NC}"
    echo "    Module loaded but device not appearing. Try rebooting."
    exit 1
fi

echo -e "${GREEN}  ✓ Loopback device is card ${LOOPBACK_CARD}${NC}"

# FFmpeg writes to hw:X,0 (playback side), detector reads from hw:X,1 (capture side)
PLAYBACK_DEVICE="hw:${LOOPBACK_CARD},0"
CAPTURE_DEVICE="hw:${LOOPBACK_CARD},1"

echo "    FFmpeg output:   ${PLAYBACK_DEVICE}"
echo "    Detector input:  ${CAPTURE_DEVICE}"

###############################################################################
# Step 4: Create Systemd Service
###############################################################################

echo ""
echo -e "${YELLOW}Step 4: Creating iphone-audio-stream service...${NC}"

sudo tee /etc/systemd/system/iphone-audio-stream.service > /dev/null << SVCEOF
[Unit]
Description=iPhone Periscope HD Audio Stream
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Restart=always
RestartSec=10

# Capture iPhone RTSP audio, convert to 16kHz mono PCM, pipe to ALSA loopback
ExecStart=/usr/bin/ffmpeg \\
    -rtsp_transport udp \\
    -i ${RTSP_URL} \\
    -vn \\
    -acodec pcm_s16le \\
    -ar 16000 \\
    -ac 1 \\
    -f alsa \\
    ${PLAYBACK_DEVICE}

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

echo -e "${GREEN}  ✓ Service file created${NC}"

###############################################################################
# Step 5: Enable and Start
###############################################################################

echo -e "${YELLOW}Step 5: Enabling and starting service...${NC}"

sudo systemctl daemon-reload
sudo systemctl enable iphone-audio-stream.service
sudo systemctl start iphone-audio-stream.service

# Give it a moment to connect
sleep 3

STATUS=$(systemctl is-active iphone-audio-stream.service 2>/dev/null || true)

if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}  ✓ Service is running!${NC}"
else
    echo -e "${YELLOW}  ⚠ Service status: ${STATUS}${NC}"
    echo "    Check logs with: sudo journalctl -u iphone-audio-stream -f"
    echo "    Make sure Periscope HD is streaming on the iPhone."
fi

###############################################################################
# Step 6: Verify Audio
###############################################################################

echo ""
echo -e "${YELLOW}Step 6: Verifying audio capture...${NC}"

# Try to record 2 seconds from the capture side
TESTFILE="/tmp/iphone_audio_test.wav"
timeout 4 arecord -D "${CAPTURE_DEVICE}" -f S16_LE -r 16000 -c 1 -d 2 "${TESTFILE}" 2>/dev/null || true

if [ -f "$TESTFILE" ] && [ -s "$TESTFILE" ]; then
    # Check audio levels
    LEVEL=$(python3 -c "
import wave, struct, math
try:
    w = wave.open('${TESTFILE}', 'r')
    frames = w.readframes(w.getnframes())
    if len(frames) < 4:
        print('empty')
    else:
        samples = [abs(struct.unpack('<h', frames[i:i+2])[0]) for i in range(0, min(len(frames), 64000), 2)]
        peak = max(samples)
        rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
        if peak < 10:
            print('silence')
        else:
            print(f'ok peak={peak} rms={rms:.0f}')
except Exception as e:
    print(f'error: {e}')
" 2>/dev/null)

    case "$LEVEL" in
        ok*)
            echo -e "${GREEN}  ✓ Audio is flowing! (${LEVEL})${NC}"
            ;;
        silence)
            echo -e "${YELLOW}  ⚠ Audio captured but appears silent${NC}"
            echo "    Make some noise near the iPhone and try again."
            ;;
        *)
            echo -e "${YELLOW}  ⚠ Could not verify audio levels (${LEVEL})${NC}"
            ;;
    esac
    rm -f "$TESTFILE"
else
    echo -e "${YELLOW}  ⚠ Could not capture test audio${NC}"
    echo "    The stream may still be connecting. Wait a moment and test manually:"
    echo "    arecord -D ${CAPTURE_DEVICE} -f S16_LE -r 16000 -c 1 -d 3 /tmp/test.wav"
fi

###############################################################################
# Summary
###############################################################################

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Audio pipeline:"
echo "  iPhone (Periscope HD) → RTSP → FFmpeg → ALSA Loopback → Detector"
echo ""
echo "Important: Update your dog bark detector to use the loopback device."
echo "  In dog_bark_detector.py, update AUDIO_DEVICE_INDEX to match"
echo "  the loopback capture device, or set the PulseAudio default source."
echo ""
echo "Useful commands:"
echo "  sudo systemctl status iphone-audio-stream  # Check stream status"
echo "  sudo journalctl -u iphone-audio-stream -f   # Watch stream logs"
echo "  sudo systemctl restart dog_bark_detector     # Restart detector"
echo "  arecord -l                                   # List audio devices"
echo ""
