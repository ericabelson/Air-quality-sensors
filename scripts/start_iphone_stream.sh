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

# Note: no set -e here — ffmpeg exits non-zero on RTSP disconnect, which is
# expected. We want systemd Restart=always to handle reconnection cleanly.

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
# Output devices:
#   sub0 (plughw:CARD,0) -> PulseAudio reads PCM1/sub0 for BirdNET-Pi recording.
#     plughw (not hw:) handles format/rate conversion so ffmpeg doesn't crash if
#     PulseAudio has locked the loopback to 44100 Hz stereo.
#   sub1 (loopback_write_bark, defined in /etc/asound.conf) -> bark detector +
#     birdnet_analyzer read PCM1/sub1 via dsnoop+plug (loopback_cap). Using a
#     separate subdevice from PulseAudio's sub0 avoids exclusive-access conflicts.
SUB0="plughw:${CARD},0"
SUB1="loopback_write_bark"

echo "Starting iPhone audio stream..."
echo "  RTSP URL:   $RTSP_URL"
echo "  Output:     $SUB0 (BirdNET/PulseAudio)  +  $SUB1 (bark detector)"
echo "  Transport:  TCP (reliable for WiFi)"

# exec replaces this shell with FFmpeg so systemd tracks the right PID.
#
# Transport: TCP is far more reliable than UDP for persistent RTSP over WiFi.
# Reconnection: systemd Restart=always + RestartSec=5 retries the RTSP URL
# automatically whenever Periscope stops streaming.
#
# asplit duplicates the decoded audio to both ALSA outputs simultaneously.
# Each output is independent — an XRUN on one does not affect the other.
#
exec /usr/bin/ffmpeg \
    -rtsp_transport tcp \
    -i "$RTSP_URL" \
    -filter_complex "[0:a]asplit=2[a1][a2]" \
    -map "[a1]" -acodec pcm_s16le -ar 16000 -ac 1 -f alsa "$SUB0" \
    -map "[a2]" -acodec pcm_s16le -ar 16000 -ac 1 -f alsa "$SUB1"
