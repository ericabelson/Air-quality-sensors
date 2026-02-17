#!/bin/bash
###############################################################################
# Fix FFmpeg Service - Add timeout so it auto-restarts on stream drops
# =====================================================================
# The current iphone-audio-stream service hangs forever when the iPhone
# stops streaming (Periscope HD closed, phone locked, etc). This adds
# timeouts so FFmpeg exits and systemd restarts it automatically.
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
# -timeout 5000000: RTSP connection timeout after 5s (in microseconds)
#   (replaces -stimeout which was removed in ffmpeg 7.x)
# -rw_timeout 5000000: read/write timeout - forces FFmpeg to exit on stale stream
# When FFmpeg exits due to timeout, systemd Restart=always brings it back.
ExecStart=/usr/bin/ffmpeg \\
    -rtsp_transport udp \\
    -timeout 5000000 \\
    -rw_timeout 5000000 \\
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
