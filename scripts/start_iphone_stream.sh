#!/bin/bash
###############################################################################
# Start iPhone Audio Stream (FFmpeg wrapper)
# ==========================================
# Reads the dynamically-detected ALSA loopback card number from
# /run/audio_loopback_card (written by audio_startup.sh at boot) and
# launches FFmpeg to capture the iPhone RTSP stream.
#
# This replaces the old approach of hardcoding "hw:3,0" in the systemd
# service file, which would break whenever the card number changed on reboot.
#
# Environment variables (set in the systemd service file):
#   IPHONE_IP   - iPhone's IP address (required, no default)
#   RTSP_PORT   - RTSP port (default: 8554)
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

# Read the loopback card number written at boot by audio_startup.sh
CARD_FILE="/run/audio_loopback_card"

if [ ! -f "$CARD_FILE" ]; then
    echo "ERROR: $CARD_FILE not found." >&2
    echo "  Is audio_startup.service running?" >&2
    echo "  Manual fix: sudo bash /path/to/audio_startup.sh" >&2
    exit 1
fi

CARD=$(cat "$CARD_FILE")

if [ -z "$CARD" ]; then
    echo "ERROR: $CARD_FILE is empty." >&2
    exit 1
fi

# Validate environment
if [ -z "$IPHONE_IP" ]; then
    echo "ERROR: IPHONE_IP environment variable not set." >&2
    echo "  Set it in the systemd service file:" >&2
    echo "  Environment=\"IPHONE_IP=192.168.x.x\"" >&2
    exit 1
fi

RTSP_PORT="${RTSP_PORT:-8554}"
RTSP_URL="rtsp://${IPHONE_IP}:${RTSP_PORT}/live.sdp"
DEVICE="hw:${CARD},0"

echo "Starting iPhone audio stream..."
echo "  RTSP URL:   $RTSP_URL"
echo "  Output:     $DEVICE (card $CARD)"
echo "  Transport:  TCP (reliable for WiFi)"

# exec replaces this shell with FFmpeg so systemd tracks the right PID
#
# Transport: TCP is far more reliable than UDP for persistent RTSP over WiFi.
# UDP drops packets silently and FFmpeg hangs for 2+ minutes before timing out.
# TCP detects connection loss quickly and lets systemd restart us.
#
# Timeouts (in microseconds):
#   -stimeout  10000000  = 10s RTSP socket timeout (connect + setup)
#   -rw_timeout 5000000  = 5s  read/write timeout (during streaming)
#
exec /usr/bin/ffmpeg \
    -rtsp_transport tcp \
    -stimeout 10000000 \
    -rw_timeout 5000000 \
    -i "$RTSP_URL" \
    -vn \
    -acodec pcm_s16le \
    -ar 16000 \
    -ac 1 \
    -f alsa \
    "$DEVICE"
