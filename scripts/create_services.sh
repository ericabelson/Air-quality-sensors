#!/bin/bash
###############################################################################
# Create Systemd Services for Audio Detection
# ============================================
# Creates systemd service files for automatic startup
#
# Services created:
# - dog_bark_detector.service (dog bark detection)
# - birdnet_analyzer.service (bird species detection)
# - audio_csv_export.timer (hourly CSV export)
# - iphone-audio-stream.service (RTSP audio stream from iPhone to ALSA loopback)
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Creating Systemd Services${NC}"

###############################################################################
# Dog Bark Detector Service
###############################################################################

echo -e "${YELLOW}Creating dog_bark_detector.service...${NC}"

sudo tee /etc/systemd/system/dog_bark_detector.service > /dev/null << 'EOF'
[Unit]
Description=Dog Bark Detector
After=network.target mosquitto.service iphone-audio-stream.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/dog_bark_detector.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ dog_bark_detector.service created${NC}"

###############################################################################
# BirdNET Analyzer Service
###############################################################################

echo -e "${YELLOW}Creating birdnet_analyzer.service...${NC}"

# Location — set these env vars before running, or edit the service file later
BIRDNET_LAT="${BIRDNET_LAT:-0}"
BIRDNET_LON="${BIRDNET_LON:-0}"

sudo tee /etc/systemd/system/birdnet_analyzer.service > /dev/null << EOF
[Unit]
Description=BirdNET Real-Time Bird Analyzer
After=network.target mosquitto.service iphone-audio-stream.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/birdnet_analyzer.py
Restart=always
RestartSec=15

# Environment variables
Environment="PYTHONUNBUFFERED=1"
Environment="BIRDNET_LAT=${BIRDNET_LAT}"
Environment="BIRDNET_LON=${BIRDNET_LON}"
Environment="BIRDNET_MIN_CONF=0.25"
Environment="BIRDNET_GAP=0"

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ birdnet_analyzer.service created${NC}"

###############################################################################
# CSV Export Timer (Hourly)
###############################################################################

echo -e "${YELLOW}Creating CSV export timer...${NC}"

# Create the service
sudo tee /etc/systemd/system/audio_csv_export.service > /dev/null << 'EOF'
[Unit]
Description=Export Audio Detection CSV Files

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/csv_exporter.py --all
StandardOutput=journal
StandardError=journal
EOF

# Create the timer (runs every hour)
sudo tee /etc/systemd/system/audio_csv_export.timer > /dev/null << 'EOF'
[Unit]
Description=Hourly CSV Export Timer
Requires=audio_csv_export.service

[Timer]
# Run every hour at the top of the hour
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo -e "${GREEN}✓ CSV export timer created (runs hourly)${NC}"

###############################################################################
# iPhone Audio Stream Service
###############################################################################

echo -e "${YELLOW}Creating iphone-audio-stream.service...${NC}"

# Default iPhone IP - update this to match your network
IPHONE_IP="${IPHONE_IP:-192.168.1.150}"
RTSP_PORT="${RTSP_PORT:-8554}"

# Detect ALSA loopback card number (if snd-aloop is loaded)
LOOPBACK_CARD=$(arecord -l 2>/dev/null | grep -i "loopback" | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
LOOPBACK_CARD="${LOOPBACK_CARD:-1}"

sudo tee /etc/systemd/system/iphone-audio-stream.service > /dev/null << EOF
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
    -i rtsp://${IPHONE_IP}:${RTSP_PORT}/live.sdp \\
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

echo -e "${GREEN}✓ iphone-audio-stream.service created (iPhone IP: ${IPHONE_IP})${NC}"

###############################################################################
# Enable and Start Services
###############################################################################

echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}Enabling services...${NC}"
sudo systemctl enable iphone-audio-stream.service
sudo systemctl enable dog_bark_detector.service
sudo systemctl enable birdnet_analyzer.service
sudo systemctl enable audio_csv_export.timer

echo -e "${GREEN}✓ Services enabled${NC}"

echo ""
echo -e "${GREEN}Services created successfully!${NC}"
echo ""
echo "To start the services now:"
echo "  sudo systemctl start iphone-audio-stream"
echo "  sudo systemctl start dog_bark_detector"
echo "  sudo systemctl start birdnet_analyzer"
echo "  sudo systemctl start audio_csv_export.timer"
echo ""
echo "To check status:"
echo "  sudo systemctl status iphone-audio-stream"
echo "  sudo systemctl status dog_bark_detector"
echo "  sudo systemctl status birdnet_analyzer"
echo "  sudo systemctl status audio_csv_export.timer"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u iphone-audio-stream -f"
echo "  sudo journalctl -u dog_bark_detector -f"
echo "  sudo journalctl -u birdnet_analyzer -f"
echo ""
echo -e "${YELLOW}NOTE: Set IPHONE_IP before running to use your iPhone's IP:${NC}"
echo "  IPHONE_IP=192.168.1.XXX ./create_services.sh"
echo ""
