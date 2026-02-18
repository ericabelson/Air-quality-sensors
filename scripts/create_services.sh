#!/bin/bash
###############################################################################
# Create Systemd Services for Audio Detection
# ============================================
# Creates systemd service files for automatic startup on the Raspberry Pi.
#
# Services created:
# - audio_startup.service       (oneshot: detect ALSA loopback card at boot)
# - iphone-audio-stream.service (FFmpeg RTSP capture → ALSA loopback)
# - dog_bark_detector.service   (dog bark detection → MQTT)
# - birdnet_analyzer.service    (bird species detection → MQTT)
# - audio_csv_export.timer      (hourly CSV export)
#
# Configuration (set env vars before running, or accept defaults):
#   PI_USER      - Pi username (default: current user)
#   PI_HOME      - Pi home directory (default: ~$PI_USER)
#   IPHONE_IP    - iPhone IP address (REQUIRED - no default)
#   RTSP_PORT    - RTSP port (default: 8554)
#   BIRDNET_LAT  - Latitude for BirdNET (default: 30.2672 = Austin, TX)
#   BIRDNET_LON  - Longitude for BirdNET (default: -97.7431)
#   REPO_DIR     - Path to this git repo (default: auto-detected)
#
# Usage:
#   IPHONE_IP=192.168.68.116 ./create_services.sh
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
# Configuration
###############################################################################

PI_USER="${PI_USER:-$(whoami)}"
PI_HOME="${PI_HOME:-$(eval echo "~$PI_USER")}"
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
IPHONE_IP="${IPHONE_IP:-}"
RTSP_PORT="${RTSP_PORT:-8554}"
BIRDNET_LAT="${BIRDNET_LAT:-30.2672}"
BIRDNET_LON="${BIRDNET_LON:-97.7431}"

AUDIO_DIR="${PI_HOME}/audio_detection"
VENV_PYTHON="${AUDIO_DIR}/venv/bin/python3"

if [ -z "$IPHONE_IP" ]; then
    echo -e "${RED}Error: IPHONE_IP is required${NC}"
    echo ""
    echo "Usage:"
    echo "  IPHONE_IP=192.168.x.x ./create_services.sh"
    echo ""
    echo "Find your iPhone IP: iPhone > Settings > Wi-Fi > tap your network"
    exit 1
fi

echo -e "${GREEN}Creating Systemd Services${NC}"
echo "  User:      $PI_USER"
echo "  Home:      $PI_HOME"
echo "  Audio dir: $AUDIO_DIR"
echo "  Repo:      $REPO_DIR"
echo "  iPhone IP: $IPHONE_IP"
echo ""

###############################################################################
# Audio Startup Service (oneshot - runs FIRST at boot)
###############################################################################

echo -e "${YELLOW}Creating audio_startup.service...${NC}"

sudo tee /etc/systemd/system/audio_startup.service > /dev/null << EOF
[Unit]
Description=Audio Pipeline Startup (detect ALSA loopback card)
DefaultDependencies=yes
After=sound.target
Before=iphone-audio-stream.service dog_bark_detector.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash ${REPO_DIR}/scripts/audio_startup.sh

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}  audio_startup.service created${NC}"

###############################################################################
# iPhone Audio Stream Service (uses dynamic card number)
###############################################################################

echo -e "${YELLOW}Creating iphone-audio-stream.service...${NC}"

sudo tee /etc/systemd/system/iphone-audio-stream.service > /dev/null << EOF
[Unit]
Description=iPhone Periscope HD Audio Stream
After=network.target audio_startup.service
Requires=audio_startup.service
Wants=network.target

[Service]
Type=simple
User=${PI_USER}
Restart=always
RestartSec=10

# iPhone IP and port passed as environment variables
Environment="IPHONE_IP=${IPHONE_IP}"
Environment="RTSP_PORT=${RTSP_PORT}"

# Wrapper script reads /run/audio_loopback_card for the correct device
ExecStart=/bin/bash ${REPO_DIR}/scripts/start_iphone_stream.sh

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}  iphone-audio-stream.service created (iPhone IP: ${IPHONE_IP})${NC}"

###############################################################################
# Dog Bark Detector Service
###############################################################################

echo -e "${YELLOW}Creating dog_bark_detector.service...${NC}"

sudo tee /etc/systemd/system/dog_bark_detector.service > /dev/null << EOF
[Unit]
Description=Dog Bark Detector
After=network.target mosquitto.service iphone-audio-stream.service audio_startup.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=${PI_USER}
WorkingDirectory=${AUDIO_DIR}
ExecStart=${VENV_PYTHON} ${REPO_DIR}/scripts/dog_bark_detector.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}  dog_bark_detector.service created${NC}"

###############################################################################
# BirdNET Analyzer Service
###############################################################################

echo -e "${YELLOW}Creating birdnet_analyzer.service...${NC}"

sudo tee /etc/systemd/system/birdnet_analyzer.service > /dev/null << EOF
[Unit]
Description=BirdNET Real-Time Bird Analyzer
After=network.target mosquitto.service iphone-audio-stream.service audio_startup.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=${PI_USER}
WorkingDirectory=${AUDIO_DIR}
ExecStart=${VENV_PYTHON} ${REPO_DIR}/scripts/birdnet_analyzer.py
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

echo -e "${GREEN}  birdnet_analyzer.service created${NC}"

###############################################################################
# CSV Export Timer (Hourly)
###############################################################################

echo -e "${YELLOW}Creating CSV export timer...${NC}"

sudo tee /etc/systemd/system/audio_csv_export.service > /dev/null << EOF
[Unit]
Description=Export Audio Detection CSV Files

[Service]
Type=oneshot
User=${PI_USER}
WorkingDirectory=${AUDIO_DIR}
ExecStart=${VENV_PYTHON} ${REPO_DIR}/scripts/csv_exporter.py --all
StandardOutput=journal
StandardError=journal
EOF

sudo tee /etc/systemd/system/audio_csv_export.timer > /dev/null << 'EOF'
[Unit]
Description=Hourly CSV Export Timer
Requires=audio_csv_export.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo -e "${GREEN}  CSV export timer created (runs hourly)${NC}"

###############################################################################
# Enable Services
###############################################################################

echo ""
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}Enabling services...${NC}"
sudo systemctl enable audio_startup.service
sudo systemctl enable iphone-audio-stream.service
sudo systemctl enable dog_bark_detector.service
sudo systemctl enable birdnet_analyzer.service
sudo systemctl enable audio_csv_export.timer

echo -e "${GREEN}  All services enabled${NC}"

###############################################################################
# Summary
###############################################################################

echo ""
echo -e "${GREEN}Services created successfully!${NC}"
echo ""
echo "Boot order:"
echo "  1. audio_startup.service  (detects ALSA loopback card number)"
echo "  2. iphone-audio-stream    (FFmpeg captures iPhone RTSP to loopback)"
echo "  3. dog_bark_detector      (reads loopback, detects barks, publishes MQTT)"
echo "  4. birdnet_analyzer       (reads loopback, identifies bird species)"
echo ""
echo "To start everything now:"
echo "  sudo systemctl start audio_startup"
echo "  sudo systemctl start iphone-audio-stream"
echo "  sudo systemctl start dog_bark_detector"
echo "  sudo systemctl start birdnet_analyzer"
echo "  sudo systemctl start audio_csv_export.timer"
echo ""
echo "To check status:"
echo "  systemctl is-active audio_startup iphone-audio-stream dog_bark_detector birdnet_analyzer"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u dog_bark_detector -f"
echo "  sudo journalctl -u iphone-audio-stream -f"
echo ""
