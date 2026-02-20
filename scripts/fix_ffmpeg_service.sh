#!/bin/bash
###############################################################################
# Fix FFmpeg Service - Update for ffmpeg 7.x compatibility
# =========================================================
# Updates the iphone-audio-stream service to work with ffmpeg 7.x which
# removed the -stimeout and -rw_timeout options. The service relies on
# systemd Restart=always for auto-recovery on stream drops.
#
# Usage:  sudo bash fix_ffmpeg_service.sh
###############################################################################

set -e

echo "=== Fixing iphone-audio-stream service ==="

# Get the current iPhone IP from the existing service
IPHONE_IP=$(systemctl cat iphone-audio-stream 2>/dev/null | grep -oP 'rtsp://\K[0-9.]+' | head -1)
LOOPBACK_CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')

if [ -z "$IPHONE_IP" ]; then
    echo "Error: Could not find iPhone IP from current service"
    exit 1
fi

if [ -z "$LOOPBACK_CARD" ]; then
    echo "Error: Could not find loopback card number"
    exit 1
fi

echo "iPhone IP: $IPHONE_IP"
echo "Loopback card: $LOOPBACK_CARD"
echo ""

# Write the updated service file
# Note: -stimeout and -rw_timeout were removed in ffmpeg 7.x
# Systemd Restart=always handles recovery on stream drops.
sudo tee /etc/systemd/system/iphone-audio-stream.service > /dev/null << EOF
[Unit]
Description=iPhone Periscope HD Audio Stream
After=network.target
Wants=network.target

[Service]
User=$(whoami)
Type=simple
Restart=always
RestartSec=10

# Capture iPhone RTSP audio, convert to 16kHz mono PCM, pipe to ALSA loopback.
# When FFmpeg exits (stream drop, network error), systemd Restart=always brings it back.
ExecStart=/usr/bin/ffmpeg \\
    -rtsp_transport udp \\
    -i rtsp://${IPHONE_IP}:8554/live.sdp \\
    -vn \\
    -acodec pcm_s16le \\
    -ar 16000 \\
    -ac 1 \\
    -f alsa \\
    hw:${LOOPBACK_CARD},0

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Service file updated."
echo ""

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart iphone-audio-stream

echo "Service restarted. Waiting 5 seconds..."
sleep 5

STATUS=$(systemctl is-active iphone-audio-stream 2>/dev/null || true)
echo "Service status: $STATUS"

if [ "$STATUS" != "active" ]; then
    echo ""
    echo "Service may have failed - check if Periscope HD is streaming on iPhone"
    echo "Logs: sudo journalctl -u iphone-audio-stream -n 20 --no-pager"
fi

echo ""
echo "Done. The service will now auto-restart within 15 seconds if the stream drops."
